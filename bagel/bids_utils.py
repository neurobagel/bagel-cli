from pathlib import Path
from typing import Optional

from bids import BIDSLayout

from bagel import mappings, models


# TODO: Can probably generalize below function for use in the pheno command functions as well?
def map_term_to_namespace(term: str, namespace: dict) -> str:
    """Returns the mapped namespace term if it exists, or False otherwise."""
    return namespace.get(term, False)


def check_unique_bids_subjects(pheno_subjects: list, bids_subjects: list):
    """Raises informative error if subject IDs exist that are found only in the BIDS directory."""
    unique_bids_subjects = set(bids_subjects).difference(pheno_subjects)
    if len(unique_bids_subjects) > 0:
        raise LookupError(
            "The specified BIDS directory contains subject IDs not found in"
            f"the provided phenotypic json-ld file: {unique_bids_subjects}"
            "Please check that the specified BIDS and phenotypic datasets match."
        )


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
            # layout.get(
            #     subject=bids_sub_id,
            #     target="subject",
            #     return_type="dir",
            # )[0]
        )
    else:
        session_path = Path(
            layout.get(
                subject=bids_sub_id,
                session=session,
                target="session",
                return_type="dir",
            )[0]
        )

    return session_path.resolve().as_posix()
