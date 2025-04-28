from pathlib import Path
from typing import Optional

from bids import BIDSLayout
from typer import BadParameter

from bagel import mappings, models


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
    layout: BIDSLayout,
    bids_sub_id: str,
    session: Optional[str],
) -> list:
    """Parses BIDS image files for a specified session/subject to create a list of Acquisition objects."""
    image_list = []
    for bids_file in layout.get(
        subject=bids_sub_id,
        session=session,
        extension=[".nii", ".nii.gz"],
    ):
        # If the suffix of a BIDS file is not recognized, then ignore
        mapped_term = map_term_to_namespace(
            bids_file.get_entities().get("suffix"),
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
    source_bids_dir: Path,
    bids_sub_id: str,
    session: Optional[str],
) -> str:
    """Construct the session directory from the source BIDS directory path if session layer exists, otherwise returns subject directory."""
    subject_path = source_bids_dir / f"sub-{bids_sub_id}"
    session_path = subject_path / f"ses-{session}" if session else subject_path
    return session_path.as_posix()
