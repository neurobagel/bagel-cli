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


def test_valid_bids_dataset_converted_successfully(
    runner,
    bids_synthetic,
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
            bids_synthetic,
            "--output",
            default_bids2tsv_output_path,
        ],
    )
    assert result.exit_code == 0, f"Errored out. STDOUT: {result.output}"

    bids_tsv = pd.read_csv(default_bids2tsv_output_path, sep="\t")
    assert list(bids_tsv.columns) == ["sub", "ses", "suffix", "path"]
    assert bids_tsv[["sub", "suffix", "path"]].notna().all(axis=None)
    assert bids_tsv["sub"].str.startswith("sub-").all()
    assert bids_tsv["ses"].str.startswith("ses-").all()
    assert set(bids_tsv["suffix"].unique()) == set(["bold", "T1w"])


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
    for substring in ["suffixes unsupported in BIDS", "FAKE"]:
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
