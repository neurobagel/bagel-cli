import json
from pathlib import Path

import typer
from bids import BIDSLayout

import bagel.bids_utils as butil
import bagel.derivatives_utils as dutil
import bagel.file_utils as futil
import bagel.pheno_utils as putil
from bagel import mappings, models
from bagel.derivatives_utils import PROC_STATUS_COLS
from bagel.utility import (
    confirm_subs_match_pheno_data,
    extract_and_validate_jsonld_dataset,
    generate_context,
    get_imaging_session_instances,
    get_subject_instances,
)

# TODO: Coordinate with Nipoppy about what we want to name this
CUSTOM_SESSION_ID = "nb01"

bagel = typer.Typer(
    help="""
    A command-line tool for creating valid, subject-level instances of the Neurobagel graph data model.\n
    The 'pheno' command must always be run first to generate the input .jsonld file required for the 'bids' command.

    To view the arguments for a specific command, run: bagel [COMMAND] --help
    """,
    # From https://github.com/tiangolo/typer/issues/201#issuecomment-744151303
    context_settings={"help_option_names": ["--help", "-h"]},
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
    futil.check_overwrite(output, overwrite)

    data_dictionary = futil.load_json(dictionary)
    pheno_df = futil.load_tabular(pheno)
    putil.validate_inputs(data_dictionary, pheno_df)

    # NOTE: `space` determines the amount of padding (in num. characters) before the file paths in the print statement.
    # It is currently calculated as = (length of the longer string, including the 3 leading spaces) + (2 extra spaces)
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
        _sub_pheno = pheno_df.query(
            f"`{participants}` == '{str(participant)}'"
        )

        sessions = []
        for session_row_idx, session_row in _sub_pheno.iterrows():
            # If there is no session column, we create a session with a custom label "ses-nb01" to assign each subject's phenotypic data to
            if session_column is None:
                session_name = f"ses-{CUSTOM_SESSION_ID}"
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

    context = generate_context()
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
        help="The path to the .jsonld file containing the phenotypic data for your dataset, created by the bagel pheno command. "
        "This file may optionally also include the processing pipeline metadata for the dataset (created by the bagel derivatives command).",
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
    Extract imaging metadata from a valid BIDS dataset and integrate it with
    subjects' harmonized phenotypic data (from the bagel pheno command) and, optionally,
    processing pipeline metadata (from the bagel derivatives command) in a single .jsonld file.
    NOTE: Must be run AFTER the pheno command.

    This command will create a valid, subject-level instance of the Neurobagel
    graph data model for the combined metadata in the .jsonld format.
    You can upload this .jsonld file to the Neurobagel graph.
    """
    futil.check_overwrite(output, overwrite)

    space = 51
    print(
        "Running initial checks of inputs...\n"
        f"   {'Existing subject graph data to augment (.jsonld):' : <{space}} {jsonld_path}\n"
        f"   {'BIDS dataset directory:' : <{space}} {bids_dir}"
    )

    jsonld_dataset = extract_and_validate_jsonld_dataset(jsonld_path)

    existing_subs_dict = get_subject_instances(jsonld_dataset)

    # TODO: Revert to using Layout.get_subjects() to get BIDS subjects once pybids performance is improved
    confirm_subs_match_pheno_data(
        subjects=butil.get_bids_subjects_simple(bids_dir),
        subject_source_for_err="BIDS directory",
        pheno_subjects=existing_subs_dict.keys(),
    )

    print("Initial checks of inputs passed.\n")

    print("Parsing and validating BIDS dataset. This may take a while...")
    layout = BIDSLayout(bids_dir, validate=True)
    print("BIDS parsing completed.\n")

    print("Merging BIDS metadata with existing subject annotations...\n")
    for bids_sub_id in layout.get_subjects():
        existing_subject = existing_subs_dict.get(f"sub-{bids_sub_id}")
        existing_sessions_dict = get_imaging_session_instances(
            existing_subject
        )

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

            if not image_list:
                continue

            # TODO: Currently if a subject has BIDS data but no "ses-" directories (e.g., only 1 session),
            # we create a session for that subject with a custom label "ses-nb01" to be added to the graph.
            # However, we still provide the BIDS SUBJECT directory as the session path, instead of making up a path.
            # This should be revisited in the future as for these cases the resulting dataset object is not
            # an exact representation of what's on disk.
            # Here, we also need to add back "ses" prefix because pybids stripped it
            session_label = "ses-" + (
                CUSTOM_SESSION_ID if session is None else session
            )
            session_path = butil.get_session_path(
                layout=layout,
                bids_dir=bids_dir,
                bids_sub_id=bids_sub_id,
                session=session,
            )

            # If a custom Neurobagel-created session already exists (if `bagel derivatives` was run first),
            # we add to that session when there is no session layer in the BIDS directory
            if session_label in existing_sessions_dict:
                existing_img_session = existing_sessions_dict.get(
                    session_label
                )
                existing_img_session.hasAcquisition = image_list
                existing_img_session.hasFilePath = session_path
            else:
                new_imaging_session = models.ImagingSession(
                    hasLabel=session_label,
                    hasFilePath=session_path,
                    hasAcquisition=image_list,
                )

            existing_subject.hasSession.append(new_imaging_session)

    context = generate_context()
    merged_dataset = {**context, **jsonld_dataset.dict(exclude_none=True)}

    with open(output, "w") as f:
        f.write(json.dumps(merged_dataset, indent=2))

    print(f"Saved output to:  {output}")


@bagel.command()
def derivatives(
    tabular: Path = typer.Option(
        ...,
        "--tabular",
        "-t",
        help="The path to a .tsv containing subject-level processing pipeline status info. Expected to comply with the Nipoppy processing status file schema.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
    # TODO: Remove _path?
    jsonld_path: Path = typer.Option(
        ...,
        "--jsonld-path",
        "-p",  # for pheno
        help="The path to a .jsonld file containing the phenotypic data for your dataset, created by the bagel pheno command. This JSONLD may optionally also include the BIDS metadata for the dataset (created by the bagel bids command).",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
    output: Path = typer.Option(
        "pheno_derivatives.jsonld",
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
    Extract subject processing pipeline and derivative metadata from a tabular processing status file and
    integrate them in a single .jsonld with subjects' harmonized phenotypic data (from the bagel pheno command) and optionally,
    BIDS metadata (from the bagel bids command).
    NOTE: Must be run AFTER the pheno command.

    This command will create a valid, subject-level instance of the Neurobagel
    graph data model for the combined metadata in the .jsonld format.
    You can upload this .jsonld file to the Neurobagel graph.
    """
    futil.check_overwrite(output, overwrite)

    space = 51
    print(
        "Processing subject-level derivative metadata...\n"
        f"   {'Existing subject graph data to augment (.jsonld):' : <{space}}{jsonld_path}\n"
        f"   {'Processing status file (.tsv):' : <{space}}{tabular}"
    )

    status_df = futil.load_tabular(tabular, input_type="processing status")

    # We don't allow empty values in the participant ID column
    if row_indices := putil.get_rows_with_empty_strings(
        status_df, [PROC_STATUS_COLS["participant"]]
    ):
        raise LookupError(
            f"Your processing status file contains missing values in the column '{PROC_STATUS_COLS['participant']}'. "
            "Please ensure that every row has a non-empty participant id. "
            f"We found missing values in the following rows (first row is zero): {row_indices}."
        )

    pipelines = status_df[PROC_STATUS_COLS["pipeline_name"]].unique()
    dutil.check_pipelines_are_recognized(pipelines)

    # TODO: Do we need to check all versions across all pipelines first, and report all unrecognized versions together?
    for pipeline in pipelines:
        versions = status_df[
            status_df[PROC_STATUS_COLS["pipeline_name"]] == pipeline
        ][PROC_STATUS_COLS["pipeline_version"]].unique()

        dutil.check_pipeline_versions_are_recognized(pipeline, versions)

    jsonld_dataset = extract_and_validate_jsonld_dataset(jsonld_path)

    existing_subs_dict = get_subject_instances(jsonld_dataset)

    confirm_subs_match_pheno_data(
        subjects=status_df[PROC_STATUS_COLS["participant"]].unique(),
        subject_source_for_err="processing status file",
        pheno_subjects=existing_subs_dict.keys(),
    )

    # Create sub-dataframes for each subject
    for subject, sub_proc_df in status_df.groupby(
        PROC_STATUS_COLS["participant"]
    ):
        existing_subject = existing_subs_dict.get(subject)

        # Note: Dictionary of existing imaging sessions can be empty if only bagel pheno was run
        existing_sessions_dict = get_imaging_session_instances(
            existing_subject
        )

        for session, sub_ses_proc_df in sub_proc_df.groupby(
            PROC_STATUS_COLS["session"]
        ):
            completed_pipelines = dutil.create_completed_pipelines(
                sub_ses_proc_df
            )

            if not completed_pipelines:
                continue

            session_label = (
                f"ses-{CUSTOM_SESSION_ID}" if session == "" else session
            )
            if session_label in existing_sessions_dict:
                existing_img_session = existing_sessions_dict.get(session)
                existing_img_session.hasCompletedPipeline = completed_pipelines
            else:
                new_img_session = models.ImagingSession(
                    hasLabel=session_label,
                    hasCompletedPipeline=completed_pipelines,
                )
                existing_subject.hasSession.append(new_img_session)

    context = generate_context()
    merged_dataset = {**context, **jsonld_dataset.dict(exclude_none=True)}

    with open(output, "w") as f:
        f.write(json.dumps(merged_dataset, indent=2))

    print(f"Saved output to:  {output}")
