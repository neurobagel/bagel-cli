from collections import Counter
from pathlib import Path

import pytest
from bids import BIDSLayout

from bagel.utilities import bids_utils


@pytest.mark.parametrize(
    "bids_dir",
    ["synthetic", "ds000248"],
)
def test_get_bids_subjects_simple(bids_path, bids_dir):
    """Test that get_bids_subjects_simple() correctly extracts subject IDs from a BIDS directory."""
    bids_subject_list = bids_utils.get_bids_subjects_simple(
        bids_path / bids_dir
    )
    expected_subjects = [
        f"sub-{sub_id}"
        for sub_id in BIDSLayout(
            bids_path / bids_dir, validate=True
        ).get_subjects()
    ]
    assert sorted(bids_subject_list) == sorted(expected_subjects)


@pytest.mark.parametrize(
    "bids_dir, acquisitions, bids_session",
    [
        (
            "synthetic",
            {"nidm:T1Weighted": 1, "nidm:FlowWeighted": 3},
            "01",
        ),
        (
            "ds001",
            {
                "nidm:T2Weighted": 1,
                "nidm:T1Weighted": 1,
                "nidm:FlowWeighted": 3,
            },
            None,
        ),
        ("eeg_ds000117", {"nidm:T1Weighted": 1}, None),
    ],
)
def test_create_acquisitions(bids_path, bids_dir, acquisitions, bids_session):
    """Given a BIDS dataset, creates a list of acquisitions matching the image files found on disk."""
    image_list = bids_utils.create_acquisitions(
        layout=BIDSLayout(bids_path / bids_dir, validate=True),
        bids_sub_id="01",
        session=bids_session,
    )

    image_counts = Counter(
        [image.hasContrastType.identifier for image in image_list]
    )

    for contrast, count in acquisitions.items():
        assert image_counts[contrast] == count


@pytest.mark.parametrize(
    "bids_sub_id, session",
    [("01", "01"), ("02", "02"), ("03", "01")],
)
def test_get_session_path_when_session_exists(
    bids_sub_id, session, bids_synthetic
):
    """
    Test that given a subject and session ID (i.e. when BIDS session layer exists for dataset),
    get_session_path() returns a path to the subject's session directory.
    """
    session_path = bids_utils.get_session_path(
        bids_dir=bids_synthetic,
        bids_sub_id=bids_sub_id,
        session=session,
    )

    assert f"sub-{bids_sub_id}" in session_path
    assert f"ses-{session}" in session_path
    assert Path(session_path).is_absolute()
    assert Path(session_path).is_dir()


@pytest.mark.parametrize("bids_sub_id", ["01", "03", "05"])
def test_get_session_path_when_session_missing(bids_sub_id, bids_path):
    """
    Test that given only a subject ID (i.e., when BIDS session layer is missing for dataset),
    get_session_path() returns the path to the subject directory.
    """
    bids_dir = bids_path / "ds001"
    session_path = bids_utils.get_session_path(
        bids_dir=bids_dir,
        bids_sub_id=bids_sub_id,
        session=None,
    )

    assert session_path.endswith(f"sub-{bids_sub_id}")
    assert Path(session_path).is_absolute()
    assert Path(session_path).is_dir()
