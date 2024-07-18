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
    A command-line tool for creating valid, subject-level instances of the Neurobagel graph data model.\n
    The 'pheno' command must always be run first to generate the input .jsonld file required for the 'bids' command.

    To view the arguments for a specific command, run: bagel [COMMAND] --help
    """
)


@bagel.command()
def pheno(
    pheno: Path = typer.Option(  # TODO: Rename argument to something clearer, like --tabular.
        ...,
        "--pheno",
        "-t",  # for tabular
        help="The path to a phenotypic .tsv file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
    dictionary: Path = typer.Option(
        ...,
        "--dictionary",
        "-d",
        help="The path to the .json data dictionary corresponding to the phenotypic .tsv file.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
    name: str = typer.Option(
        ...,
        "--name",
        "-n",
        help="A descriptive name for the dataset the input belongs to. "
        "This name is expected to match the name field in the BIDS dataset_description.json file. "
        'Should be enclosed in quotes, e.g.: --name "my dataset name"',
    ),
    portal: str = typer.Option(
        None,
        "--portal",
        "-u",  # for URL
        callback=putil.validate_portal_uri,
        help="URL (HTTP/HTTPS) to a website or page that describes the dataset and access instructions (if available).",
    ),
    output: Path = typer.Option(
        "pheno.jsonld",
        "--output",
        "-o",
        help="The path for the output .jsonld file.",
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        "-f",
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

    # Note that `session_column will be None if there is no session column in the pheno.tsv
    session_column = column_mapping.get("session")

    for participant in pheno_df[participants].unique():
        _sub_pheno = pheno_df.query(f"{participants} == '{str(participant)}'")

        sessions = []
        for session_row_idx, session_row in _sub_pheno.iterrows():
            # If there is no session column, we create a session with a custom label "ses-nb01" to assign each subject's phenotypic data to
            if session_column is None:
                session_name = "ses-nb01"  # TODO: Should we make this more obscure to avoid potential overlap with actual session names?
            else:
                # NOTE: We take the name from the first session column - we don't know how to handle multiple session columns yet
                session_name = session_row[session_column[0]]

            session = models.PhenotypicSession(hasLabel=str(session_name))
            _ses_pheno = session_row

            if "sex" in column_mapping.keys():
                _sex_vals = putil.get_transformed_values(
                    column_mapping["sex"], _ses_pheno, data_dictionary
                )
                if _sex_vals:
                    # NOTE: Our data model only allows a single sex value, so we only take the first instance if multiple columns are about sex
                    session.hasSex = models.Sex(identifier=_sex_vals[0])

            if "diagnosis" in column_mapping.keys():
                _dx_vals = putil.get_transformed_values(
                    column_mapping["diagnosis"], _ses_pheno, data_dictionary
                )
                if not _dx_vals:
                    pass
                # NOTE: If the subject has both a diagnosis value and a value of healthy control, we assume the healthy control designation is more important
                # and do not assign diagnoses to the subject
                elif mappings.NEUROBAGEL["healthy_control"] in _dx_vals:
                    session.isSubjectGroup = models.SubjectGroup(
                        identifier=mappings.NEUROBAGEL["healthy_control"],
                    )
                else:
                    session.hasDiagnosis = [
                        models.Diagnosis(identifier=_dx_val)
                        for _dx_val in _dx_vals
                    ]

            if "age" in column_mapping.keys():
                _age_vals = putil.get_transformed_values(
                    column_mapping["age"], _ses_pheno, data_dictionary
                )
                if _age_vals:
                    # NOTE: Our data model only allows a single age value, so we only take the first instance if multiple columns are about age
                    session.hasAge = _age_vals[0]

            if tool_mapping:
                _assessments = [
                    models.Assessment(identifier=tool)
                    for tool, columns in tool_mapping.items()
                    if putil.are_any_available(
                        columns, _ses_pheno, data_dictionary
                    )
                ]
                if _assessments:
                    # Only set assessments for the subject if at least one has a non-missing item
                    session.hasAssessment = _assessments
            sessions.append(session)

        subject = models.Subject(
            hasLabel=str(participant), hasSession=sessions
        )
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
        "--jsonld-path",
        "-p",  # for pheno
        help="The path to the .jsonld file containing the phenotypic data for your dataset, created by the bagel pheno command.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
    bids_dir: Path = typer.Option(
        ...,
        "--bids-dir",
        "-b",
        help="The path to the corresponding BIDS dataset directory.",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    output: Path = typer.Option(
        "pheno_bids.jsonld",
        "--output",
        "-o",
        help="The path for the output .jsonld file.",
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        "-f",
        help="Overwrite output file if it already exists.",
    ),
):
    """
    Extract imaging metadata from a valid BIDS dataset and combine them
    with phenotypic metadata (.jsonld) created by the bagel pheno command.
    NOTE: Must be run AFTER the pheno command.

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
