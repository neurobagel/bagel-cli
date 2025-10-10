import pandas as pd
import pytest

from bagel.cli import bagel


@pytest.fixture(scope="function")
def default_bids2tsv_output_path(tmp_path):
    """Return temporary bids2tsv command output filepath that uses the default filename."""
    return tmp_path / "bids.tsv"


@pytest.fixture()
def bids_synthetic_with_fake_suffix_file(bids_synthetic):
    """Yield a temporary synthetic BIDS dataset containing a file with an unsupported suffix."""
    fake_suffix_file = (
        bids_synthetic / "sub-01/ses-01/anat/sub-01_ses-01_FAKE.nii"
    )
    with open(fake_suffix_file, "w") as f:
        f.write("")

    yield bids_synthetic

    fake_suffix_file.unlink()


@pytest.mark.parametrize(
    "bids_dataset,has_sessions,expected_suffixes",
    [
        ("synthetic", True, {"bold", "T1w"}),
        ("eeg_cbm", False, {"eeg"}),
    ],
)
def test_valid_bids_dataset_converted_successfully(
    runner,
    bids_path,
    bids_dataset,
    has_sessions,
    expected_suffixes,
    default_bids2tsv_output_path,
):
    """
    Test that generated TSV contains expected columns and image contrast suffixes
    and that sub and ses columns are correctly prefixed.
    """
    result = runner.invoke(
        bagel,
        [
            "bids2tsv",
            "--bids-dir",
            bids_path / bids_dataset,
            "--output",
            default_bids2tsv_output_path,
        ],
    )
    assert result.exit_code == 0, f"Errored out. STDOUT: {result.output}"

    bids_tsv = pd.read_csv(default_bids2tsv_output_path, sep="\t")
    assert list(bids_tsv.columns) == ["sub", "ses", "suffix", "path"]
    assert bids_tsv[["sub", "suffix", "path"]].notna().all(axis=None)
    assert bids_tsv["sub"].str.startswith("sub-").all()
    if has_sessions:
        assert bids_tsv["ses"].str.startswith("ses-").all()
    else:
        assert bids_tsv["ses"].isna().all()
    assert set(bids_tsv["suffix"].unique()) == expected_suffixes


def test_BIDS_unsupported_suffixes_filtered_out(
    runner,
    bids_synthetic_with_fake_suffix_file,
    default_bids2tsv_output_path,
    test_data_upload_path,
    tmp_path,
    propagate_warnings,
    caplog,
):
    """
    Test that unsupported suffixes used in a BIDS dataset are filtered out by bids2tsv,
    and that the resulting TSV does not produce a validation error when used as input to the bids command.
    """
    result = runner.invoke(
        bagel,
        [
            "bids2tsv",
            "--bids-dir",
            bids_synthetic_with_fake_suffix_file,
            "--output",
            default_bids2tsv_output_path,
        ],
    )
    assert result.exit_code == 0
    assert len(caplog.records) == 1
    for substring in ["suffixes unsupported by Neurobagel", "FAKE"]:
        assert substring in caplog.text

    bids_tsv = pd.read_csv(default_bids2tsv_output_path, sep="\t")
    assert "FAKE" not in bids_tsv["suffix"].unique()

    result = runner.invoke(
        bagel,
        [
            "bids",
            "--jsonld-path",
            test_data_upload_path / "example_synthetic.jsonld",
            "--bids-table",
            default_bids2tsv_output_path,
            "--output",
            tmp_path / "pheno_bids.jsonld",
        ],
    )
    assert result.exit_code == 0


def test_exits_gracefully_if_no_supported_suffixes_in_bids_dir(
    runner,
    bids_path,
    default_bids2tsv_output_path,
    propagate_warnings,
    caplog,
):
    """Test that bids2tsv exits with an informative error if no NIfTI files are found in the BIDS directory."""
    result = runner.invoke(
        bagel,
        [
            "bids2tsv",
            "--bids-dir",
            bids_path / "micr_SEM",
            "--output",
            default_bids2tsv_output_path,
        ],
    )

    assert result.exit_code != 0
    assert not default_bids2tsv_output_path.exists()
    assert len(caplog.records) == 1
    assert (
        "No image files with supported BIDS suffixes were found" in caplog.text
    )
