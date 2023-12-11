import json
from pathlib import Path

import typer
from bids import BIDSLayout
from pydantic import ValidationError

import bagel.bids_utils as butil
import bagel.pheno_utils as putil
from bagel import mappings, models
from bagel.utility import check_overwrite, load_json

bagel = typer.Typer(
    help="""
    A command-line tool for creating valid, subject-level instances of the Neurobagel graph data model.

    To view the arguments for a specific command, run: bagel [COMMAND] --help
    """
)


@bagel.command()
def pheno(
    pheno: Path = typer.Option(  # TODO: Rename argument to something clearer, like --tabular.
        ...,
        help="The path to a phenotypic .tsv file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
    dictionary: Path = typer.Option(
        ...,
        help="The path to the .json data dictionary corresponding to the phenotypic .tsv file.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
    name: str = typer.Option(
        ...,
        help="A descriptive name for the dataset the input belongs to. "
        "This name is expected to match the name field in the BIDS dataset_description.json file. "
        'Should be enclosed in quotes, e.g.: --name "my dataset name"',
    ),
    portal: str = typer.Option(
        default=None,
        callback=putil.validate_portal_uri,
        help="URL (HTTP/HTTPS) to a website or page that describes the dataset and access instructions (if available).",
    ),
    output: Path = typer.Option(
        default="pheno.jsonld",
        help="The path for the output .jsonld file.",
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite output file if it already exists.",
    ),
):
    """
    Process a tabular phenotypic file (.tsv) that has been successfully annotated
    with the Neurobagel annotation tool. The annotations are expected to be stored
    in a data dictionary (.json).

    This command will create a valid, subject-level instance of the Neurobagel
    graph data model for the provided phenotypic file in the .jsonld format.
    You can upload this .jsonld file to the Neurobagel graph.
    """
    # Check if output file already exists
    check_overwrite(output, overwrite)

    data_dictionary = load_json(dictionary)
    pheno_df = putil.load_pheno(pheno)
    putil.validate_inputs(data_dictionary, pheno_df)

    # Display validated input paths to user
    space = 25
    print(
        "Processing phenotypic annotations:\n"
        f"   {'Tabular file (.tsv):' : <{space}} {pheno}\n"
        f"   {'Data dictionary (.json):' : <{space}} {dictionary}\n"
    )

    subject_list = []

    column_mapping = putil.map_categories_to_columns(data_dictionary)
    tool_mapping = putil.map_tools_to_columns(data_dictionary)

    # TODO: needs refactoring once we handle multiple participant IDs
    participants = column_mapping.get("participant")[0]
    # TODO: handle if no session_ID column exists
    session_column = column_mapping.get("session")[0]
    import pdb

    for participant in pheno_df[participants].unique():
        # TODO: needs refactoring once we handle phenotypic information at the session level
        # for the moment we are not creating any session instances in the phenotypic graph
        # we treat the phenotypic information in the first row of the _sub_pheno dataframe
        # as reflecting the subject level phenotypic information
        _sub_pheno = pheno_df.query(
            f"{participants} == '{str(participant)}'"
        )
        
        # TODO ensure we don't have duplicates in the session ID
        session_names = _sub_pheno[session_column].unique()
        pdb.set_trace()
        # TODO make sure we have at least one session
        # We think this will be ['ses-01', 'ses-02']

        sessions = []
        for session_name in session_names:
            session = models.PhenotypicSession(hasLabel=str(session_name))
            _ses_pheno = _sub_pheno.query(
                f"{session_column} == '{str(session_name)}'"
            )
            
            if "sex" in column_mapping.keys():
                _sex_val = putil.get_transformed_values(
                    column_mapping["sex"], _ses_pheno, data_dictionary
                )
                if _sex_val:
                    session.hasSex = models.Sex(identifier=_sex_val)

            if "diagnosis" in column_mapping.keys():
                pdb.set_trace()
                _dx_val = putil.get_transformed_values(
                    column_mapping["diagnosis"], _ses_pheno, data_dictionary
                )
                if _dx_val is None:
                    pass
                elif _dx_val == mappings.NEUROBAGEL["healthy_control"]:
                    session.isSubjectGroup = models.SubjectGroup(
                        identifier=mappings.NEUROBAGEL["healthy_control"],
                    )
                else:
                    session.hasDiagnosis = [models.Diagnosis(identifier=_dx_val)]

            if "age" in column_mapping.keys():
                session.hasAge = putil.get_transformed_values(
                    column_mapping["age"], _ses_pheno, data_dictionary
                )

            if tool_mapping:
                _assessments = [
                    models.Assessment(identifier=tool)
                    for tool, columns in tool_mapping.items()
                    if putil.are_any_available(
                        columns, _ses_pheno, data_dictionary
                    )
                ]
                if _assessments:
                    # Only set assignments for the subject if at least one has a non-missing item
                    session.hasAssessment = _assessments
            sessions.append(session)

        pdb.set_trace()
        subject = models.Subject(hasLabel=str(participant), hasSession=sessions)
        subject_list.append(subject)

    dataset = models.Dataset(
        hasLabel=name,
        hasPortalURI=portal,
        hasSamples=subject_list,
    )

    context = putil.generate_context()
    # We can't just exclude_unset here because the identifier and schemaKey
    # for each instance are created as default values and so technically are never set
    # TODO: we should revisit this because there may be reasons to have None be meaningful in the future
    context.update(**dataset.dict(exclude_none=True))

    with open(output, "w") as f:
        f.write(json.dumps(context, indent=2))

    print(f"Saved output to:  {output}")


@bagel.command()
def bids(
    jsonld_path: Path = typer.Option(
        ...,
        help="The path to a pheno.jsonld file.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
    bids_dir: Path = typer.Option(
        ...,
        help="The path to the corresponding BIDS dataset directory.",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    output: Path = typer.Option(
        help="The path for the output .jsonld file.",
        default="pheno_bids.jsonld",
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite output file if it already exists.",
    ),
):
    """
    Extract imaging metadata from a valid BIDS dataset and combine them
    with phenotypic metadata (.jsonld) created in a previous step using the
    bagel pheno command.

    This command will create a valid, subject-level instance of the Neurobagel
    graph data model for the combined metadata in the .jsonld format.
    You can upload this .jsonld file to the Neurobagel graph.
    """
    # Check if output file already exists
    check_overwrite(output, overwrite)

    space = 32
    print(
        "Running initial checks of inputs...\n"
        f"   {'Phenotypic .jsonld to augment:' : <{space}} {jsonld_path}\n"
        f"   {'BIDS dataset directory:' : <{space}} {bids_dir}"
    )

    jsonld = load_json(jsonld_path)
    # Strip and store context to be added back later, since it's not part of
    # (and can't be easily added) to the existing data model
    context = {"@context": jsonld.pop("@context")}
    try:
        pheno_dataset = models.Dataset.parse_obj(jsonld)
    except ValidationError as err:
        print(err)

    pheno_subject_dict = {
        pheno_subject.hasLabel: pheno_subject
        for pheno_subject in getattr(pheno_dataset, "hasSamples")
    }

    # TODO: Revert to using Layout.get_subjects() to get BIDS subjects once pybids performance is improved
    butil.check_unique_bids_subjects(
        pheno_subjects=pheno_subject_dict.keys(),
        bids_subjects=butil.get_bids_subjects_simple(bids_dir),
    )
    print("Initial checks of inputs passed.\n")

    print("Parsing and validating BIDS dataset. This may take a while...")
    layout = BIDSLayout(bids_dir, validate=True)
    print("BIDS parsing completed.\n")

    print(
        "Merging subject-level BIDS metadata with the phenotypic annotations...\n"
    )
    for bids_sub_id in layout.get_subjects():
        pheno_subject = pheno_subject_dict.get(f"sub-{bids_sub_id}")
        session_list = []

        bids_sessions = layout.get_sessions(subject=bids_sub_id)
        if not bids_sessions:
            if not layout.get_datatypes(subject=bids_sub_id):
                continue
            bids_sessions = [None]

        # For some reason .get_sessions() doesn't always follow alphanumeric order
        # By default (without sorting) the session lists look like ["02", "01"] per subject
        for session in sorted(bids_sessions):
            image_list = butil.create_acquisitions(
                layout=layout,
                bids_sub_id=bids_sub_id,
                session=session,
            )

            # If subject's session has no image files, a Session object is not added
            if not image_list:
                continue

            # TODO: Currently if a subject has BIDS data but no "ses-" directories (e.g., only 1 session),
            # we create a session for that subject with a custom label "ses-nb01" to be added to the graph
            # so the API can still find the session-level information.
            # This should be revisited in the future as for these cases the resulting dataset object is not
            # an exact representation of what's on disk.
            session_label = "nb01" if session is None else session
            session_path = butil.get_session_path(
                layout=layout,
                bids_dir=bids_dir,
                bids_sub_id=bids_sub_id,
                session=session,
            )

            # TODO: needs refactoring once we also handle phenotypic information at the session level
            session_list.append(
                # Add back "ses" prefix because pybids stripped it
                models.ImagingSession(
                    hasLabel="ses-" + session_label,
                    hasFilePath=session_path,
                    hasAcquisition=image_list,
                )
            )

        pheno_subject.hasSession += session_list

    merged_dataset = {**context, **pheno_dataset.dict(exclude_none=True)}

    with open(output, "w") as f:
        f.write(json.dumps(merged_dataset, indent=2))

    print(f"Saved output to:  {output}")
