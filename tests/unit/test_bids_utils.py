from collections import Counter
from pathlib import Path

import pandas as pd
import pytest
from bids import BIDSLayout

from bagel.utilities import bids_utils


# TODO: Remove since we no longer need the corresponding utility function
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
    "session_df_rows, expected_acquisitions",
    [
        (
            [
                [
                    "sub-01",
                    "ses-01",
                    "T1w",
                    "/data/synthetic/sub-01/ses-01/anat/sub-01_ses-01_T1w.nii",
                ],
                [
                    "sub-01",
                    "ses-01",
                    "bold",
                    "/data/bids-examples/synthetic/sub-01/ses-01/func/sub-01_ses-01_task-nback_run-01_bold.nii",
                ],
                [
                    "sub-01",
                    "ses-01",
                    "bold",
                    "/data/bids-examples/synthetic/sub-01/ses-01/func/sub-01_ses-01_task-nback_run-02_bold.nii",
                ],
                [
                    "sub-01",
                    "ses-01",
                    "bold",
                    "/data/bids-examples/synthetic/sub-01/ses-01/func/sub-01_ses-01_task-rest_bold.nii",
                ],
            ],
            {"nidm:T1Weighted": 1, "nidm:FlowWeighted": 3},
        ),
        (
            [
                [
                    "sub-01",
                    "",
                    "inplaneT2",
                    "/data/bids-examples/ds001/sub-01/anat/sub-01_inplaneT2.nii.gz",
                ],
                [
                    "sub-01",
                    "",
                    "T1w",
                    "/data/bids-examples/ds001/sub-01/anat/sub-01_T1w.nii.gz",
                ],
                [
                    "sub-01",
                    "",
                    "bold",
                    "/data/bids-examples/ds001/sub-01/func/sub-01_task-balloonanalogrisktask_run-01_bold.nii.gz",
                ],
                [
                    "sub-01",
                    "",
                    "bold",
                    "/data/bids-examples/ds001/sub-01/func/sub-01_task-balloonanalogrisktask_run-02_bold.nii.gz",
                ],
                [
                    "sub-01",
                    "",
                    "bold",
                    "/data/bids-examples/ds001/sub-01/func/sub-01_task-balloonanalogrisktask_run-03_bold.nii.gz",
                ],
            ],
            {
                "nidm:T2Weighted": 1,
                "nidm:T1Weighted": 1,
                "nidm:FlowWeighted": 3,
            },
        ),
        (
            [
                [
                    "sub-01",
                    "",
                    "T1w",
                    "/data/bids-examples/eeg_ds000117/sub-01/anat/sub-01_T1w.nii.gz",
                ]
            ],
            {"nidm:T1Weighted": 1},
        ),
    ],
)
def test_create_acquisitions(session_df_rows, expected_acquisitions):
    """
    Test that given a set of rows corresponding to a session's BIDS files,
    create_acquisitions() creates a correct list of acquisitions matching the image file suffixes.
    """
    session_df = pd.DataFrame(
        session_df_rows, columns=["sub", "ses", "suffix", "path"]
    )
    image_list = bids_utils.create_acquisitions(
        session_df=session_df,
    )

    extracted_image_counts = Counter(
        [image.hasContrastType.identifier for image in image_list]
    )

    for expected_contrast, expected_count in expected_acquisitions.items():
        assert extracted_image_counts[expected_contrast] == expected_count


@pytest.mark.parametrize(
    "file_path, ses, expected_session_path",
    [
        (
            "/data/bids/sub-01/ses-01/anat/sub-01_ses-01_T1w.nii",
            "ses-01",
            "/data/bids/sub-01/ses-01",
        ),
        (
            "/data/bids/sub-01/anat/sub-01_ses-01_T1w.nii",
            "",
            "/data/bids/sub-01",
        ),
    ],
)
def test_get_session_path_when_id_in_path(
    file_path, ses, expected_session_path
):
    """
    Test that depending on whether a session ID is provided in addition to a subject ID
    (i.e. whether a BIDS session layer exists), get_session_path() correctly returns the path to
    either the session or subject directory.
    """
    session_path = bids_utils.get_session_path(
        file_path=Path(file_path),
        bids_sub_id="sub-01",
        session_id=ses,
    )

    assert session_path == expected_session_path


@pytest.mark.parametrize(
    "file_path, sub, ses",
    [
        (
            "/data/pd_dataset/pd00123/baseline/nifti/pd00123_T1w.nii",
            "sub-pd00123",
            "ses-baseline",
        ),
        (
            "/data/bids/anat/sub-01_ses-01_T1w.nii",
            "sub-01",
            "ses-01",
        ),
    ],
)
def test_get_session_path_when_id_not_in_path(
    file_path, sub, ses, caplog, propagate_warnings
):
    """
    Test that when the provided session ID is not found in the file path,
    get_session_path() returns no directory path and logs an informative warning.
    """
    session_path = bids_utils.get_session_path(
        file_path=Path(file_path),
        bids_sub_id=sub,
        session_id=ses,
    )

    assert session_path is None
    assert len(caplog.records) == 1
    assert f"{ses} was not found in the path" in caplog.records[0].message
