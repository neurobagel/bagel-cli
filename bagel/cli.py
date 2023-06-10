import json
from pathlib import Path

import pandas as pd
import typer
from bids import BIDSLayout
from pydantic import ValidationError

import bagel.bids_utils as butil
import bagel.pheno_utils as putil
from bagel import mappings, models
from bagel.utility import load_json

bagel = typer.Typer()


@bagel.command()
def pheno(
    dataset_dir: Path = typer.Option(
        ...,
        help="The path to the directory containing the phenotypic data (.tsv and .json data dictionary) for the dataset.",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    pheno: Path = typer.Option(  # TODO: Rename argument to something clearer, like --tabular.
        default=None,
        help="The path to a phenotypic .tsv file.",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    dictionary: Path = typer.Option(
        default=None,
        help="The path to the .json data dictionary "
        "corresponding to the phenotypic .tsv file.",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    output: Path = typer.Option(
        ...,
        help="The directory where outputs should be created.",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    name: str = typer.Option(
        ...,
        help="A descriptive name for the dataset the input belongs to. "
        "This name is expected to match the name field in the BIDS "
        "dataset_description.json file.",
    ),
    portal: str = typer.Option(
        default=None,
        help="URL to a website or page that describes the dataset.",
    ),
):
    """
    Process a tabular phenotypic file (.tsv) that has been successfully annotated
    with the Neurobagel annotation tool. The annotations are expected to be stored
    in a data dictionary (.json).

    This tool will create a valid, subject-level instance of the Neurobagel
    graph datamodel for the provided phenotypic file in the .jsonld format.
    You can upload this .jsonld file to the Neurobagel graph.
    """
    if pheno is None:
        pheno = dataset_dir / "participants.tsv"
    if dictionary is None:
        dictionary = dataset_dir / "participants.json"

    for input_file in [pheno, dictionary]:
        if not input_file.is_file():
            raise FileNotFoundError(
                f"File {input_file} not found. Verify that you have provided the correct dataset directory path, or use the individual file arguments to specify custom file names"
                "for the tabular phenotypic file and/or data dictionary."
            )
        if input_file.resolve().parent != dataset_dir.resolve():
            raise IOError(
                f"The file {input_file} must be located at the top level of the dataset directory {dataset_dir}. Please try again."
            )

    data_dictionary = load_json(dictionary)
    pheno_df = pd.read_csv(pheno, sep="\t", keep_default_na=False, dtype=str)
    putil.validate_inputs(data_dictionary, pheno_df)

    subject_list = []

    column_mapping = putil.map_categories_to_columns(data_dictionary)
    tool_mapping = putil.map_tools_to_columns(data_dictionary)

    # TODO: needs refactoring once we handle multiple participant IDs
    participants = column_mapping.get("participant")[0]

    for participant in pheno_df[participants].unique():
        # TODO: needs refactoring once we handle phenotypic information at the session level
        # for the moment we are not creating any session instances in the phenotypic graph
        # we treat the phenotypic information in the first row of the _sub_pheno dataframe
        # as reflecting the subject level phenotypic information
        _sub_pheno = pheno_df.query(
            f"{participants} == '{str(participant)}'"
        ).iloc[0]

        subject = models.Subject(hasLabel=str(participant))
        if "sex" in column_mapping.keys():
            subject.hasSex = models.Sex(
                identifier=putil.get_transformed_values(
                    column_mapping["sex"], _sub_pheno, data_dictionary
                ),
            )

        if "diagnosis" in column_mapping.keys():
            _dx_val = putil.get_transformed_values(
                column_mapping["diagnosis"], _sub_pheno, data_dictionary
            )
            if _dx_val is None:
                pass
            elif _dx_val == mappings.NEUROBAGEL["healthy_control"]:
                subject.isSubjectGroup = models.SubjectGroup(
                    identifier=mappings.NEUROBAGEL["healthy_control"],
                )
            else:
                subject.hasDiagnosis = [models.Diagnosis(identifier=_dx_val)]

        if "age" in column_mapping.keys():
            subject.hasAge = putil.get_transformed_values(
                column_mapping["age"], _sub_pheno, data_dictionary
            )

        if tool_mapping:
            _assessments = [
                models.Assessment(identifier=tool)
                for tool, columns in tool_mapping.items()
                if putil.are_not_missing(columns, _sub_pheno, data_dictionary)
            ]
            if _assessments:
                # Only set assignments for the subject if at least one is not missing
                subject.hasAssessment = _assessments

        subject_list.append(subject)

    dataset = models.Dataset(hasLabel=name, hasSamples=subject_list)

    if portal is not None:
        dataset.hasPortalURI = portal

    context = putil.generate_context()
    # We can't just exclude_unset here because the identifier and schemaKey
    # for each instance are created as default values and so technically are never set
    # TODO: we should revisit this because there may be reasons to have None be meaningful in the future
    context.update(**dataset.dict(exclude_none=True))

    with open(output / "pheno.jsonld", "w") as f:
        f.write(json.dumps(context, indent=2))


@bagel.command()
def bids(
    jsonld_path: Path = typer.Option(
        ...,
        help="The path to a pheno.jsonld file.",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    bids_dir: Path = typer.Option(
        ...,
        help="The path to the corresponding BIDS dataset directory.",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    output: Path = typer.Option(
        ...,
        help="The directory where outputs should be created",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
):
    """
    Extract imaging metadata from a valid BIDS dataset and combine them
    with phenotypic metadata (.jsonld) created in a previous step using the
    bagel pheno command.

    This tool will create a valid, subject-level instance of the Neurobagel
    graph datamodel for the combined metadata in the .jsonld format.
    You can upload this .jsonld file to the Neurobagel graph.
    """
    jsonld = load_json(jsonld_path)
    layout = BIDSLayout(bids_dir, validate=True)

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
    bids_subject_list = ["sub-" + sub_id for sub_id in layout.get_subjects()]

    butil.check_unique_bids_subjects(
        pheno_subjects=pheno_subject_dict.keys(),
        bids_subjects=bids_subject_list,
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
                models.Session(
                    hasLabel="ses-" + session_label,
                    hasFilePath=session_path,
                    hasAcquisition=image_list,
                )
            )

        pheno_subject.hasSession = session_list

    merged_dataset = {**context, **pheno_dataset.dict(exclude_none=True)}

    with open(output / "pheno_bids.jsonld", "w") as f:
        f.write(json.dumps(merged_dataset, indent=2))
