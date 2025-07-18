from pathlib import Path

import pandas as pd
from typer import BadParameter

from bagel import mappings, models
from bagel.logger import logger


def check_absolute_bids_path(bids_path: Path) -> Path:
    """
    Raise an error if the input BIDS path does not look like an absolute path.
    This is a workaround for --source-bids-dir not requiring the path to exist (and thus not being able to resolve the path automatically),
    since it refers to a path on a host machine which may not be mounted as-is when the CLI is running in a container.
    """
    if not bids_path.is_absolute():
        raise BadParameter("BIDS directory path must be an absolute path.")
    return bids_path


def map_term_to_namespace(term: str, namespace: dict) -> str:
    """Returns the mapped namespace term if it exists, or False otherwise."""
    return namespace.get(term, False)


# TODO: Delete this function once no longer needed.
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
    """Parses BIDS image files for a specified session/subject to create a list of Acquisition objects."""
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
    file_path: Path,
    bids_sub_id: str,
    session_id: str,
) -> str | None:
    """Construct the session directory from the source BIDS directory path if session layer exists, otherwise returns subject directory."""
    target = session_id if session_id.strip() != "" else bids_sub_id

    if target not in file_path.parts:
        # TODO: Have fallback if subject or session ID is not found in the file path?
        # e.g., could default to using the parent of the .nii/.nii.gz file
        logger.warning(
            f"Could not derive an imaging session directory path for sub {bids_sub_id}, ses {session_id}: "
            f"the subject or session ID {target} was not found in the path {file_path}."
        )
        session_path = None
    else:
        target_idx = file_path.parts.index(target)
        session_path = Path(*file_path.parts[: target_idx + 1]).as_posix()

    # Alternative: if we want to catch cases where the session/subject ID is a substring of a directory name
    # (Although, this may be rare if we enforce sub-/ses- prefixes, since IDs are more likely to be substrings of dir names rather than the other way around)
    #
    # Only look for the target ID in directory names, since we want to return a subject/session directory
    # if file_path.suffix:
    #     path_dir_parts = file_path.parent.parts
    # else:
    #     path_dir_parts = file_path.parts
    # target_idx = next((
    #     idx for idx, path_part in enumerate(path_dir_parts) if target in path_part
    # ), None)
    # session_path = Path(*file_path.parts[:target_idx + 1]).as_posix() if target_idx is not None else None

    return session_path
