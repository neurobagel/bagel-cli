from pathlib import Path

import pandas as pd
import pandera.pandas as pa
from typer import BadParameter

from bagel import bids_table_model, mappings, models
from bagel.logger import log_error, logger


def find_unsupported_bids_suffixes(data: pd.DataFrame) -> list:
    """Return any suffixes unsupported by BIDS that are found in the provided BIDS table."""
    return (
        data.loc[
            ~data["suffix"].isin(bids_table_model.BIDS_SUPPORTED_SUFFIXES),
            "suffix",
        ]
        .unique()
        .tolist()
    )


def check_absolute_path(dir_path: Path | None) -> Path | None:
    """
    Raise an error if the input path does not look like an absolute path.
    This is a workaround for --dataset-source-path not requiring the path to exist on the host machine
    (and thus not being able to resolve the path automatically).
    """
    # Allow POSIX-style absolute paths (e.g., "/data/...") across OSes - useful for referencing paths on remote Unix servers.
    if dir_path is not None and not (
        dir_path.is_absolute() or dir_path.as_posix().startswith("/")
    ):
        raise BadParameter(
            "Dataset source directory must be an absolute path."
        )
    return dir_path


def validate_bids_table(bids_table: pd.DataFrame):
    """Error and exit if the provided BIDS table is empty or fails schema validation."""
    try:
        bids_table_model.model.validate(bids_table)
    except pa.errors.SchemaError as err:
        rows_with_errs_msg = ""
        # When validation fails due to a column value check (e.g., as opposed to a missing column),
        # printing the row indices helps with debugging, especially for invalid empty values.
        if isinstance(err.failure_cases, pd.DataFrame):
            rows_with_errs_msg = f"Rows with error (0 = first non-header row): {err.failure_cases['index'].tolist()}. "
        log_error(
            logger,
            f"Invalid BIDS table. Error: {err}. {rows_with_errs_msg}",
        )
    if bids_table.empty:
        log_error(
            logger,
            "BIDS table is empty (only a header row was found). No imaging metadata to add.",
        )


def map_term_to_namespace(term: str, namespace: dict) -> str:
    """Returns the mapped namespace term if it exists, or False otherwise."""
    return namespace.get(term, False)


def create_acquisitions(
    session_df: pd.DataFrame,
) -> list:
    """Parses BIDS image file suffixes for a specified session to create a list of Acquisition objects."""
    image_list = []

    for bids_file_suffix in session_df["suffix"]:
        mapped_term = map_term_to_namespace(
            term=bids_file_suffix,
            namespace=mappings.BIDS,
        )
        if mapped_term:
            image_list.append(
                models.Acquisition(
                    hasContrastType=models.Image(identifier=mapped_term)
                )
            )

    return image_list


def get_session_path(
    dataset_root: Path | None,
    bids_sub_id: str,
    session_id: str,
) -> str:
    """
    Construct the session directory or subject directory path (when there is no session ID) from the source BIDS directory path, subject ID, and session ID.
    If no source BIDS directory is available, return a relative path.
    """
    subject_path = (
        Path(dataset_root / bids_sub_id) if dataset_root else Path(bids_sub_id)
    )
    session_path = (
        subject_path / session_id if session_id.strip() != "" else subject_path
    )
    return session_path.as_posix()
