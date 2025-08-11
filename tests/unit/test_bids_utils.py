from collections import Counter
from pathlib import Path

import pandas as pd
import pytest
import typer
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
                    "/data/synthetic/sub-01/ses-01/func/sub-01_ses-01_task-nback_run-01_bold.nii",
                ],
                [
                    "sub-01",
                    "ses-01",
                    "bold",
                    "/data/synthetic/sub-01/ses-01/func/sub-01_ses-01_task-nback_run-02_bold.nii",
                ],
                [
                    "sub-01",
                    "ses-01",
                    "bold",
                    "/data/synthetic/sub-01/ses-01/func/sub-01_ses-01_task-rest_bold.nii",
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
                    "/data/ds001/sub-01/anat/sub-01_inplaneT2.nii.gz",
                ],
                [
                    "sub-01",
                    "",
                    "T1w",
                    "/data/ds001/sub-01/anat/sub-01_T1w.nii.gz",
                ],
                [
                    "sub-01",
                    "",
                    "bold",
                    "/data/ds001/sub-01/func/sub-01_task-balloonanalogrisktask_run-01_bold.nii.gz",
                ],
                [
                    "sub-01",
                    "",
                    "bold",
                    "/data/ds001/sub-01/func/sub-01_task-balloonanalogrisktask_run-02_bold.nii.gz",
                ],
                [
                    "sub-01",
                    "",
                    "bold",
                    "/data/ds001/sub-01/func/sub-01_task-balloonanalogrisktask_run-03_bold.nii.gz",
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
                    "/data/eeg_ds000117/sub-01/anat/sub-01_T1w.nii.gz",
                ]
            ],
            {"nidm:T1Weighted": 1},
        ),
    ],
)
def test_create_acquisitions(session_df_rows, expected_acquisitions):
    """
    Test that given a table with rows corresponding to a session's BIDS files,
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
    "dataset_root, ses, expected_session_path",
    [
        (
            Path("/data/pd/bids"),
            "ses-01",
            "/data/pd/bids/sub-01/ses-01",
        ),
        (
            Path("/data/pd/bids"),
            "",
            "/data/pd/bids/sub-01",
        ),
        (
            None,
            "ses-01",
            "sub-01/ses-01",
        ),
    ],
)
def test_get_session_path(dataset_root, ses, expected_session_path):
    """
    Test that depending on whether a session ID is provided in addition to a subject ID
    (i.e. whether a BIDS session layer exists), get_session_path() correctly returns the path to
    either the session or subject directory.
    """
    session_path = bids_utils.get_session_path(
        dataset_root=dataset_root,
        bids_sub_id="sub-01",
        session_id=ses,
    )

    assert session_path == expected_session_path


@pytest.mark.parametrize(
    "row_data",
    [
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
                "/data/synthetic/sub-01/ses-01/func/sub-01_ses-01_task-rest_bold.nii",
            ],
            [
                "sub-02",
                "ses-01",
                "T1w",
                "/data/synthetic/sub-02/ses-01/anat/sub-02_ses-01_T1w.nii",
            ],
            [
                "sub-02",
                "ses-01",
                "bold",
                "/data/synthetic/sub-02/ses-01/func/sub-02_ses-01_task-rest_bold.nii",
            ],
        ],
        [
            [
                "sub-01",
                "",
                "T1w",
                "/data/synthetic/sub-01/anat/sub-01_ses-01_T1w.nii.gz",
            ],
            [
                "sub-01",
                "",
                "bold",
                "/data/synthetic/sub-01/func/sub-01_ses-01_task-rest_bold.nii.gz",
            ],
            [
                "sub-02",
                "",
                "T1w",
                "/data/synthetic/sub-02/anat/sub-02_ses-01_T1w.nii.gz",
            ],
            [
                "sub-02",
                "",
                "bold",
                "/data/synthetic/sub-02/func/sub-02_ses-01_task-rest_bold.nii.gz",
            ],
        ],
    ],
)
def test_valid_bids_tables_pass_validation(row_data):
    """Test that a valid BIDS table does not produce a schema validation error"""
    bids_table = pd.DataFrame(
        row_data, columns=["sub", "ses", "suffix", "path"]
    )
    bids_utils.validate_bids_table(bids_table)


@pytest.mark.parametrize(
    "row_data,invalid_column",
    [
        (
            [
                [
                    "sub-01",
                    "01",
                    "T1w",
                    "/data/synthetic/sub-01/ses-01/anat/sub-01_ses-01_T1w.nii",
                ],
                [
                    "sub-01",
                    "01",
                    "bold",
                    "/data/synthetic/sub-01/ses-01/func/sub-01_ses-01_task-rest_bold.nii",
                ],
                [
                    "sub-02",
                    "01",
                    "T1w",
                    "/data/synthetic/sub-02/ses-01/anat/sub-02_ses-01_T1w.nii",
                ],
                [
                    "sub-02",
                    "01",
                    "bold",
                    "/data/synthetic/sub-02/ses-01/func/sub-02_ses-01_task-rest_bold.nii",
                ],
            ],
            "ses",
        ),
        (
            [
                [
                    "01",
                    "ses-01",
                    "T1w",
                    "/data/synthetic/sub-01/anat/sub-01_ses-01_T1w.nii",
                ],
                [
                    "01",
                    "ses-01",
                    "bold",
                    "/data/synthetic/sub-01/func/sub-01_ses-01_task-rest_bold.nii",
                ],
                [
                    "02",
                    "ses-01",
                    "T1w",
                    "/data/synthetic/sub-02/anat/sub-02_ses-01_T1w.nii",
                ],
                [
                    "02",
                    "ses-01",
                    "bold",
                    "/data/synthetic/sub-02/func/sub-02_ses-01_task-rest_bold.nii",
                ],
            ],
            "sub",
        ),
        (
            [
                [
                    "sub-01",
                    "ses-01",
                    "anat",
                    "/data/synthetic/sub-01/anat/sub-01_ses-01_T1w.nii.gz",
                ],
                [
                    "sub-01",
                    "ses-01",
                    "func",
                    "/data/synthetic/sub-01/func/sub-01_ses-01_task-rest_bold.nii.gz",
                ],
                [
                    "sub-02",
                    "ses-01",
                    "anat",
                    "/data/synthetic/sub-02/anat/sub-02_ses-01_T1w.nii.gz",
                ],
                [
                    "sub-02",
                    "ses-01",
                    "func",
                    "/data/synthetic/sub-02/func/sub-02_ses-01_task-rest_bold.nii.gz",
                ],
            ],
            "suffix",
        ),
        (
            [
                [
                    "sub-01",
                    "ses-01",
                    "T1w",
                    "/data/synthetic/sub-01/anat/sub-01_ses-01_T1w.mnc",
                ],
                [
                    "sub-01",
                    "ses-01",
                    "bold",
                    "/data/synthetic/sub-01/func/sub-01_ses-01_task-rest_bold.mnc",
                ],
                [
                    "sub-02",
                    "ses-01",
                    "T1w",
                    "/data/synthetic/sub-02/anat/sub-02_ses-01_T1w.mnc",
                ],
                [
                    "sub-02",
                    "ses-01",
                    "bold",
                    "/data/synthetic/sub-02/func/sub-02_ses-01_task-rest_bold.mnc",
                ],
            ],
            "path",
        ),
        (
            [
                ["sub-01", "ses-01", "T1w", ""],
                ["sub-01", "ses-01", "bold", ""],
                ["sub-02", "ses-01", "T1w", ""],
                ["sub-02", "ses-01", "bold", ""],
            ],
            "path",
        ),
    ],
)
def test_invalid_bids_tables_produce_error(
    row_data, invalid_column, caplog, propagate_errors
):
    """Test that an invalid BIDS table produces an informative schema validation error"""
    bids_table = pd.DataFrame(
        row_data, columns=["sub", "ses", "suffix", "path"]
    )
    with pytest.raises(typer.Exit):
        bids_utils.validate_bids_table(bids_table)

    assert "Invalid BIDS table" in caplog.text
    assert invalid_column in caplog.text
