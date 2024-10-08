from pathlib import Path
from typing import Optional

from bids import BIDSLayout

from bagel import mappings, models


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
    layout: BIDSLayout,
    bids_dir: Path,
    bids_sub_id: str,
    session: Optional[str],
) -> str:
    """Returns session directory from the BIDS dataset if session layer exists, otherwise returns subject directory."""
    if not session:
        session_path = Path(
            # TODO: Once bug in fetching subject directories with no session layers is resolved,
            # switch to using layout.get() snippet below to fetch subject path.
            bids_dir
            / f"sub-{bids_sub_id}"
        )
    else:
        session_path = (
            Path(layout.root) / f"sub-{bids_sub_id}" / f"ses-{session}"
        )

    return session_path.resolve().as_posix()
