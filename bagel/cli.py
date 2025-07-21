from pathlib import Path

import bids2table as b2t2
import pandas as pd
import typer
from bids import BIDSLayout, exceptions
from rich.progress import Progress, SpinnerColumn, TextColumn, track

from bagel import mappings, models

from .logger import VerbosityLevel, configure_logger, log_error, logger
from .utilities import (
    bids_utils,
    derivative_utils,
    file_utils,
    model_utils,
    pheno_utils,
)
from .utilities.derivative_utils import PROC_STATUS_COLS

CUSTOM_SESSION_LABEL = "ses-unnamed"

bagel = typer.Typer(
    help="""
    A command-line tool for creating valid, subject-level instances of the Neurobagel graph data model.\n
    The 'pheno' command must always be run first to generate the input .jsonld file required for the 'bids' command.

    To view the arguments for a specific command, run: bagel [COMMAND] --help
    """,
    # From https://github.com/tiangolo/typer/issues/201#issuecomment-744151303
    context_settings={"help_option_names": ["--help", "-h"]},
    rich_markup_mode="rich",
)


# NOTE: We use a reusable option instead of a callback to avoid the complexity
# of needing to specify the flag before the actual CLI command names
def verbosity_option():
    """Create a reusable verbosity option for commands."""
    return typer.Option(
        VerbosityLevel.INFO,
        "--verbosity",
        "-v",
        callback=configure_logger,
        help="Set the verbosity level of the output. 0 = show errors only; 1 = show errors, warnings, and informational messages; 3 = show all logs, including debug messages.",
    )


def overwrite_option():
    """Create a reusable overwrite option for commands."""
    return typer.Option(
        False,
        "--overwrite",
        "-f",
        help="Overwrite output file if it already exists.",
    )


@bagel.command()
def bids2tsv(
    bids_dir: Path = typer.Option(
        ...,
        "--bids-dir",
        "-b",
        help="The path to the BIDS dataset directory.",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    output: Path = typer.Option(
        "bids.tsv",
        "--output",
        "-o",
        help="The path to save the output .tsv file.",
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
    overwrite: bool = overwrite_option(),
    verbosity: VerbosityLevel = verbosity_option(),
):
    """
    Convert a BIDS dataset into a minimal tabular format (.tsv file) containing information about
    subject, session, suffix (image contrast), and file path for NIfTI data only.
    """
    file_utils.check_overwrite(output, overwrite)

    logger.info(f"Input BIDS directory:  {bids_dir}")

    try:
        # NOTE: If there are no subjects in the BIDS dataset, the validation should fail.
        # The rest of this workflow assumes there's at least one subject in the BIDS dataset.
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            # Add a spinner during BIDS parsing
            progress.add_task(
                "Validating BIDS dataset. This may take a while...", total=None
            )
            BIDSLayout(bids_dir, validate=True)
        logger.info("BIDS validation passed.")
    except exceptions.BIDSValidationError as e:
        log_error(
            logger,
            f"Invalid BIDS dataset at {bids_dir}. Validation error: {e}",
        )

    output_columns = ["sub", "ses", "suffix", "path"]
    dataset_tab = b2t2.index_dataset(bids_dir)
    dataset_df = dataset_tab.to_pandas()

    dataset_df = dataset_df[dataset_df["ext"].isin([".nii", ".nii.gz"])]
    dataset_df["path"] = dataset_df.apply(
        lambda row: (Path(row["root"]) / row["path"]).as_posix(), axis=1
    )
    dataset_df = dataset_df[output_columns]

    dataset_df["sub"] = dataset_df["sub"].apply(lambda id: f"sub-{id}")
    dataset_df["ses"] = dataset_df["ses"].apply(
        lambda id: f"ses-{id}" if pd.notna(id) else id
    )

    dataset_df.to_csv(output, sep="\t", index=False)
    logger.info(f"Saved output to:  {output}")


# TODO: Look into whitespace for command docstring - seems to be preserved in the help text.
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
        callback=pheno_utils.validate_dataset_name,
        help="The full name of the dataset. "
        "This name will be displayed when users discover the dataset in a Neurobagel query. "
        "For a dataset with BIDS data, the name should ideally match the dataset_description.json 'name' field. "
        'Enclose in quotes, e.g.: --name "my dataset name"',
    ),
    portal: str = typer.Option(
        None,
        "--portal",
        "-u",  # for URL
        callback=pheno_utils.validate_portal_uri,
        help="URL (HTTP/HTTPS) to a website or page that describes the dataset and access instructions (if available).",
    ),
    output: Path = typer.Option(
        "pheno.jsonld",
        "--output",
        "-o",
        help="The path to the output .jsonld file.",
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
    overwrite: bool = overwrite_option(),
    verbosity: VerbosityLevel = verbosity_option(),
):
    """
    Process a tabular phenotypic file (.tsv) that has been successfully annotated
    with the Neurobagel annotation tool. The annotations are expected to be stored
    in a data dictionary (.json).

    This command will create a valid, subject-level instance of the Neurobagel
    graph data model for the provided phenotypic file in the .jsonld format.
    You can upload this .jsonld file to the Neurobagel graph.
    """
    file_utils.check_overwrite(output, overwrite)

    data_dictionary = file_utils.load_json(dictionary)
    pheno_df = file_utils.load_tabular(pheno)

    logger.info("Running initial checks of inputs...")
    # NOTE: `width` determines the amount of padding (in num. characters) before the file paths in the print statement.
    # It is calculated as = length of the longer string + 2 extra spaces
    width = 26
    logger.info("%-*s%s", width, "Tabular file (.tsv):", pheno)
    logger.info("%-*s%s", width, "Data dictionary (.json):", dictionary)
    pheno_utils.validate_inputs(data_dictionary, pheno_df)

    # TODO: Remove once we no longer support annotation tool v1 data dictionaries
    data_dictionary = pheno_utils.convert_transformation_to_format(
        data_dictionary
    )

    logger.info("Processing phenotypic annotations...")
    subject_list = []

    column_mapping = pheno_utils.map_categories_to_columns(data_dictionary)
    tool_mapping = pheno_utils.map_tools_to_columns(data_dictionary)

    # TODO: needs refactoring once we handle multiple participant IDs
    participants = column_mapping["participant"][0]

    # Note that `session_column will be None if there is no session column in the pheno.tsv
    session_column = column_mapping.get("session")

    for participant in pheno_df[participants].unique():
        _sub_pheno = pheno_df.query(
            f"`{participants}` == '{str(participant)}'"
        )

        sessions = []
        for session_row_idx, session_row in _sub_pheno.iterrows():
            # Our data model requires a session. To support phenotypic data without sessions,
            # we create a session with a fixed, but unusual CUSTOM_SESSION_LABEL and add the
            # phenotypic data to that session.
            if session_column is None:
                session_label = CUSTOM_SESSION_LABEL
            else:
                # NOTE: We take the name from the first session column - we don't know how to handle multiple session columns yet
                session_label = session_row[session_column[0]]

            session = models.PhenotypicSession(hasLabel=str(session_label))
            _ses_pheno = session_row

            if "sex" in column_mapping.keys():
                _sex_vals = pheno_utils.get_transformed_values(
                    column_mapping["sex"], _ses_pheno, data_dictionary
                )
                if _sex_vals:
                    # NOTE: Our data model only allows a single sex value, so we only take the first instance if multiple columns are about sex
                    session.hasSex = models.Sex(identifier=_sex_vals[0])

            if "diagnosis" in column_mapping.keys():
                _dx_vals = pheno_utils.get_transformed_values(
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
                # NOTE: At the moment, our data model only supports a single age value per subject.
                # To achieve this, we transform the values from ALL columns annotated as about age
                # (so we expect each of them to be valid according to the data dictionary model),
                # but we take and store only the first instance in the graph data.
                _age_vals = pheno_utils.get_transformed_values(
                    column_mapping["age"], _ses_pheno, data_dictionary
                )
                if _age_vals:
                    session.hasAge = _age_vals[0]

            if tool_mapping:
                _assessments = [
                    models.Assessment(identifier=tool)
                    for tool, columns in tool_mapping.items()
                    if pheno_utils.are_any_available(
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

    file_utils.save_jsonld(
        data=model_utils.add_context_to_graph_dataset(dataset),
        filename=output,
    )


@bagel.command()
def bids(
    # TODO: Rename to --jsonld? Since other file options do not have the _path suffix.
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
    bids_table: Path = typer.Option(
        ...,
        "--bids-table",
        "-b",
        help="The path to a .tsv file containing the BIDS metadata for image files including 'sub', 'ses', 'suffix', and 'path' columns. "
        "This file can be created using the bagel bids2tsv command.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
    # TODO: Should we include a tip in the help text for using the repository root for DataLad datasets?
    # NOTE: dataset_source_path or dataset_root_path?
    dataset_source_path: Path = typer.Option(
        None,
        "--dataset-source-path",
        "-r",
        callback=bids_utils.check_absolute_path,
        help="The absolute path to the root directory of the dataset at the source location/file server."
        "If provided, this path will be combined with the subject and session IDs from the BIDS table to derive and record source paths for the imaging data.",
        file_okay=False,
        dir_okay=True,
    ),
    # TODO: Should we rename the default output file to something more generic to account for the fact that
    # the file may also include derivatives data? e.g., dataset_bids.jsonld
    output: Path = typer.Option(
        "pheno_bids.jsonld",
        "--output",
        "-o",
        help="The path to the output .jsonld file.",
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
    overwrite: bool = overwrite_option(),
    verbosity: VerbosityLevel = verbosity_option(),
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

    file_utils.check_overwrite(output, overwrite)

    width = 51
    logger.info("Running initial checks of inputs...")
    logger.info(
        "%-*s%s",
        width,
        "Existing subject graph data to augment (.jsonld):",
        jsonld_path,
    )
    logger.info("%-*s%s", width, "BIDS dataset table (.tsv):", bids_table)
    if dataset_source_path:
        logger.info(
            "%-*s%s",
            width,
            "Dataset root directory at the data source location (used to construct imaging data paths):",
            dataset_source_path,
        )

    jsonld_dataset = model_utils.extract_and_validate_jsonld_dataset(
        jsonld_path
    )
    bids_dataset = file_utils.load_tabular(bids_table, input_type="BIDS")

    existing_subs_dict = model_utils.get_subject_instances(jsonld_dataset)
    bids_subject_ids = list(bids_dataset["sub"].unique())

    # TODO: Validate input BIDS table (https://github.com/neurobagel/bagel-cli/issues/476)

    model_utils.confirm_subs_match_pheno_data(
        subjects=bids_subject_ids,
        subject_source_for_err="BIDS dataset file",
        pheno_subjects=existing_subs_dict.keys(),
    )

    logger.info("Initial checks of inputs passed.")

    logger.info("Merging BIDS metadata with existing subject annotations...")
    for bids_sub_id in track(
        bids_subject_ids, description="Processing BIDS subjects..."
    ):
        _bids_sub = bids_dataset[bids_dataset["sub"] == bids_sub_id]
        existing_subject = existing_subs_dict[bids_sub_id]
        existing_sessions_dict = model_utils.get_imaging_session_instances(
            existing_subject
        )

        bids_sessions = list(_bids_sub["ses"].unique())
        # TODO: Do we need to explicitly preprocess cases where ses values are other types of whitespace?
        # Ensure the sessions are in alphanumeric order for readability
        for session_id in sorted(bids_sessions):
            _bids_session = _bids_sub[_bids_sub["ses"] == session_id]
            image_list = bids_utils.create_acquisitions(
                session_df=_bids_session
            )

            if not image_list:
                continue

            # TODO: Currently if a subject has BIDS data but no "ses-" directories (e.g., only 1 session),
            # we create a session with a fixed, but unusual CUSTOM_SESSION_LABEL
            # and add the imaging data info to a session with that label (or create it first).
            # However, we still provide the BIDS SUBJECT directory as the session path, instead of making up a path.
            # This should be revisited in the future as for these cases the resulting dataset object is not
            # an exact representation of what's on disk.
            session_label = (
                CUSTOM_SESSION_LABEL
                if session_id.strip() == ""
                else session_id
            )
            session_path = bids_utils.get_session_path(
                dataset_root=dataset_source_path,
                bids_sub_id=bids_sub_id,
                session_id=session_id,
            )

            # If a custom Neurobagel-created session already exists (if `bagel derivatives` was run first),
            # we add to that session when there is no session layer in the BIDS directory
            if session_label in existing_sessions_dict:
                existing_img_session = existing_sessions_dict[session_label]
                existing_img_session.hasAcquisition = image_list
                existing_img_session.hasFilePath = session_path
            else:
                new_imaging_session = models.ImagingSession(
                    hasLabel=session_label,
                    hasFilePath=session_path,
                    hasAcquisition=image_list,
                )
                existing_subject.hasSession.append(new_imaging_session)

    file_utils.save_jsonld(
        data=model_utils.add_context_to_graph_dataset(jsonld_dataset),
        filename=output,
    )


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
        help="The path to the output .jsonld file.",
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
    overwrite: bool = overwrite_option(),
    verbosity: VerbosityLevel = verbosity_option(),
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

    file_utils.check_overwrite(output, overwrite)

    width = 51
    logger.info("Processing subject-level derivative metadata...")
    logger.info(
        "%-*s%s",
        width,
        "Existing subject graph data to augment (.jsonld):",
        jsonld_path,
    )
    logger.info("%-*s%s", width, "Processing status file (.tsv):", tabular)

    status_df = file_utils.load_tabular(
        tabular, input_type="processing status"
    )

    # We don't allow empty values in the participant ID column
    if row_indices := pheno_utils.get_rows_with_empty_strings(
        status_df, [PROC_STATUS_COLS["participant"]]
    ):
        log_error(
            logger,
            f"Your processing status file contains missing values in the column '{PROC_STATUS_COLS['participant']}'. "
            "Please ensure that every row has a non-empty participant id. "
            f"We found missing values in the following rows (first row is zero): {row_indices}.",
        )

    derivative_utils.check_at_least_one_pipeline_version_is_recognized(
        status_df=status_df
    )

    jsonld_dataset = model_utils.extract_and_validate_jsonld_dataset(
        jsonld_path
    )

    existing_subs_dict = model_utils.get_subject_instances(jsonld_dataset)

    model_utils.confirm_subs_match_pheno_data(
        subjects=status_df[PROC_STATUS_COLS["participant"]].unique(),
        subject_source_for_err="processing status file",
        pheno_subjects=existing_subs_dict.keys(),
    )

    # Create sub-dataframes for each subject
    for subject, sub_proc_df in status_df.groupby(
        PROC_STATUS_COLS["participant"]
    ):
        existing_subject = existing_subs_dict[subject]

        # Note: Dictionary of existing imaging sessions can be empty if only bagel pheno was run
        existing_sessions_dict = model_utils.get_imaging_session_instances(
            existing_subject
        )

        for session_label, sub_ses_proc_df in sub_proc_df.groupby(
            PROC_STATUS_COLS["session"]
        ):
            completed_pipelines = derivative_utils.create_completed_pipelines(
                sub_ses_proc_df
            )

            if not completed_pipelines:
                continue

            session_label = (
                CUSTOM_SESSION_LABEL if session_label == "" else session_label
            )
            if session_label in existing_sessions_dict:
                existing_img_session = existing_sessions_dict[session_label]
                existing_img_session.hasCompletedPipeline = completed_pipelines
            else:
                new_img_session = models.ImagingSession(
                    hasLabel=session_label,
                    hasCompletedPipeline=completed_pipelines,
                )
                existing_subject.hasSession.append(new_img_session)

    file_utils.save_jsonld(
        data=model_utils.add_context_to_graph_dataset(jsonld_dataset),
        filename=output,
    )
