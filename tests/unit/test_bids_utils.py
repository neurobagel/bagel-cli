from collections import Counter
from pathlib import Path

import pandas as pd
import pytest
import typer

from bagel.utilities import bids_utils


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
                    "T2w",
                    "/data/ds001/sub-01/anat/sub-01_T2w.nii.gz",
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
    mock_bids_term_mapping = {
        "T1w": "nidm:T1Weighted",
        "T2w": "nidm:T2Weighted",
        "bold": "nidm:FlowWeighted",
    }

    session_df = pd.DataFrame(
        session_df_rows, columns=["sub", "ses", "suffix", "path"]
    )
    image_list = bids_utils.create_acquisitions(
        session_df=session_df,
        bids_term_mapping=mock_bids_term_mapping,
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
    "row_data,invalid_column,invalid_row_indices",
    [
        (
            [
                # all rows missing 'ses-' prefix
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
            [0, 1, 2, 3],
        ),
        (
            [
                [
                    "sub-01",
                    "ses-01",
                    "T1w",
                    "/data/synthetic/sub-01/anat/sub-01_ses-01_T1w.nii",
                ],
                [
                    "sub-01",
                    "ses-01",
                    "bold",
                    "/data/synthetic/sub-01/func/sub-01_ses-01_task-rest_bold.nii",
                ],
                [
                    "sub-02",
                    "ses-01",
                    "T1w",
                    "/data/synthetic/sub-02/anat/sub-02_ses-01_T1w.nii",
                ],
                # empty row
                [
                    "",
                    "",
                    "",
                    "",
                ],
            ],
            "sub",
            [3],
        ),
        (
            [
                # empty row only
                [
                    "",
                    "",
                    "",
                    "",
                ],
            ],
            "sub",
            [0],
        ),
        (
            [
                [
                    "sub-01",
                    "ses-01",
                    "",  # missing suffix
                    "/data/synthetic/sub-01/anat/sub-01_ses-01_unsupported1.nii.gz",
                ],
                [
                    "sub-01",
                    "ses-01",
                    "bold",
                    "/data/synthetic/sub-01/func/sub-01_ses-01_task-rest_bold.nii.gz",
                ],
                [
                    "sub-02",
                    "ses-01",
                    "",  # missing suffix
                    "/data/synthetic/sub-02/anat/sub-02_ses-01_unsupported3.nii.gz",
                ],
                [
                    "sub-02",
                    "ses-01",
                    "bold",
                    "/data/synthetic/sub-02/func/sub-02_ses-01_task-rest_bold.nii.gz",
                ],
            ],
            "suffix",
            [0, 2],
        ),
        (
            [
                ["sub-01", "ses-01", "T1w", ""],  # missing required path
                [
                    "sub-01",
                    "ses-01",
                    "bold",
                    "/data/synthetic/sub-01/func/sub-01_ses-01_task-rest_bold.nii",
                ],
                [
                    "sub-02",
                    "ses-01",
                    "T1w",
                    "/data/synthetic/sub-02/anat/sub-02_ses-01_T1w.nii",
                ],
                [
                    "sub-02",
                    "ses-01",
                    "bold",
                    "/data/synthetic/sub-02/func/sub-02_ses-01_task-rest_bold.nii",
                ],
            ],
            "path",
            [0],
        ),
    ],
)
def test_bids_tables_with_invalid_values_produce_error(
    row_data, invalid_column, invalid_row_indices, caplog, propagate_errors
):
    """Test that a BIDS table containing invalid values for columns produces an informative schema validation error."""
    bids_table = pd.DataFrame(
        row_data, columns=["sub", "ses", "suffix", "path"]
    )
    with pytest.raises(typer.Exit):
        bids_utils.validate_bids_table(bids_table)

    assert "Invalid BIDS table" in caplog.text
    assert invalid_column in caplog.text
    assert str(invalid_row_indices) in caplog.text


def test_missing_required_column_produces_error(caplog, propagate_errors):
    """Test that a BIDS table missing a required column produces an informative schema validation error."""
    bids_table = pd.DataFrame(
        [
            [
                "sub-01",
                "ses-01",
                "/data/synthetic/sub-01/anat/sub-01_ses-01_T1w.nii",
            ],
            [
                "sub-01",
                "ses-01",
                "/data/synthetic/sub-01/func/sub-01_ses-01_task-rest_bold.nii",
            ],
            [
                "sub-02",
                "ses-01",
                "/data/synthetic/sub-02/ses-01/anat/sub-02_ses-01_T1w.nii",
            ],
            [
                "sub-02",
                "ses-01",
                "/data/synthetic/sub-02/ses-01/func/sub-02_ses-01_task-rest_bold.nii",
            ],
        ],
        columns=["sub", "ses", "path"],  # missing 'suffix' column
    )
    with pytest.raises(typer.Exit):
        bids_utils.validate_bids_table(bids_table)

    assert "Invalid BIDS table" in caplog.text
    assert "suffix" in caplog.text


def test_header_only_bids_table_produces_error(caplog, propagate_errors):
    """Test that a BIDS table with no rows except the header produces an informative error."""
    bids_table = pd.DataFrame(columns=["sub", "ses", "suffix", "path"])
    with pytest.raises(typer.Exit):
        bids_utils.validate_bids_table(bids_table)

    assert "BIDS table is empty" in caplog.text


def test_get_bids_suffix_to_std_term_mapping():
    """Test that get_bids_suffix_to_std_term_mapping() returns a mapping with expected suffix to standardized term pairings."""
    expected_prefix = "nidm"
    bids_term_mapping = bids_utils.get_bids_suffix_to_std_term_mapping()

    assert all(
        str(value).startswith(f"{expected_prefix}:")
        for value in bids_term_mapping.values()
    )
    assert bids_term_mapping["T1w"] == f"{expected_prefix}:T1Weighted"


def test_partition_suffixes():
    """
    Test that suffixes are correctly partitioned into unique sets of those found in and not found in a reference list.
    """
    suffixes = [
        "T1w",
        "T1w",
        "bold",
        "bold",
        "unknown1",
        "unknown1",
        "unknown2",
    ]
    reference_suffixes = ["T1w", "T2w", "bold", "dwi"]

    found_in_reference, not_found_in_reference = bids_utils.partition_suffixes(
        suffixes, reference_suffixes
    )
    assert found_in_reference == {"T1w", "bold"}
    assert not_found_in_reference == {"unknown1", "unknown2"}


@pytest.mark.parametrize(
    "bids_dir_suffixes, expected_warning",
    [
        (
            ["T1w", "bold", "bold", "notbids1", "notbids2"],
            ("suffixes not recognized by BIDS", "notbids1", "notbids2"),
        ),
        (
            ["T1w", "bold", "2PE", "phase1"],
            (
                "valid BIDS suffixes that are not supported by Neurobagel",
                "2PE",
                "phase1",
            ),
        ),
    ],
)
def test_single_warning_for_only_unrecognized_or_unsupported_file_suffixes(
    bids_dir_suffixes, expected_warning, caplog, propagate_warnings
):
    """
    Test that when only unrecognized or only unsupported file suffixes are present,
    they are filtered out and a single informative warning is logged.
    """
    bids_dir_suffixes = pd.Series(bids_dir_suffixes)
    # Mock minimal set of Neurobagel supported suffixes
    neurobagel_supported_suffixes = {"T1w", "T2w", "bold", "dwi"}
    filtered_suffixes = bids_utils.filter_bids_dir_suffixes(
        suffixes=bids_dir_suffixes,
        imaging_vocab_suffixes=neurobagel_supported_suffixes,
    )

    warnings = [
        record.message
        for record in caplog.records
        if record.levelname == "WARNING"
    ]

    assert len(warnings) == 1
    assert all(substr in warnings[0] for substr in expected_warning)
    assert filtered_suffixes == {"T1w", "bold"}


def test_multi_warning_for_mixed_unrecognized_and_unsupported_file_suffixes(
    caplog, propagate_warnings
):
    """
    Test that when both unrecognized and unsupported file suffixes are present,
    they are filtered out and separate informative warnings are logged.
    """
    bids_dir_suffixes = pd.Series(
        ["T1w", "bold", "2PE", "phase1", "notbids1", "notbids2"]
    )
    expected_unrecognized_suffixes_warning = (
        "suffixes not recognized by BIDS",
        "notbids1",
        "notbids2",
    )
    expected_unsupported_suffixes_warning = (
        "valid BIDS suffixes that are not supported by Neurobagel",
        "2PE",
        "phase1",
    )

    # Mock minimal set of Neurobagel supported suffixes
    neurobagel_supported_suffixes = {"T1w", "T2w", "bold", "dwi"}
    filtered_suffixes = bids_utils.filter_bids_dir_suffixes(
        suffixes=bids_dir_suffixes,
        imaging_vocab_suffixes=neurobagel_supported_suffixes,
    )

    warnings = [
        record.message
        for record in caplog.records
        if record.levelname == "WARNING"
    ]

    assert len(warnings) == 2
    assert any(
        all(
            substr in warning
            for substr in expected_unrecognized_suffixes_warning
        )
        for warning in warnings
    ), "Unrecognized suffixes warning not found"
    assert any(
        all(
            substr in warning
            for substr in expected_unsupported_suffixes_warning
        )
        for warning in warnings
    ), "Unsupported suffixes warning not found"
    assert filtered_suffixes == {"T1w", "bold"}


def test_no_warning_for_non_data_file_suffixes(caplog, propagate_warnings):
    """
    Test that no warnings are logged when all file suffixes are recognized by BIDS
    and all data file suffixes are supported by Neurobagel.
    """
    bids_dir_suffixes = pd.Series(["T1w", "bold", "sessions", "scans"])
    # Mock minimal set of Neurobagel supported suffixes
    neurobagel_supported_suffixes = {"T1w", "T2w", "bold", "dwi"}
    filtered_suffixes = bids_utils.filter_bids_dir_suffixes(
        suffixes=bids_dir_suffixes,
        imaging_vocab_suffixes=neurobagel_supported_suffixes,
    )

    assert len(caplog.records) == 0
    assert filtered_suffixes == {"T1w", "bold"}
