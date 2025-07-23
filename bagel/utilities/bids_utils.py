from pathlib import Path

import pandas as pd
from typer import BadParameter

from bagel import mappings, models


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


def map_term_to_namespace(term: str, namespace: dict) -> str:
    """Returns the mapped namespace term if it exists, or False otherwise."""
    return namespace.get(term, False)


# TODO: Remove this function
def get_bids_subjects_simple(bids_dir: Path) -> list:
    """Returns list of subject IDs (in format of sub-<SUBJECT>) for a BIDS directory inferred from the names of non-empty subdirectories."""
    bids_subject_list = []
    for path in bids_dir.iterdir():
        if (
            path.name.startswith("sub-")
            and path.is_dir()
            and any(path.iterdir())
        ):
            bids_subject_list.append(path.name)
    return bids_subject_list


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
