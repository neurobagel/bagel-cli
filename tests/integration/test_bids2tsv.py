import pandas as pd
import pytest

from bagel.cli import bagel


@pytest.fixture(scope="function")
def default_bids2tsv_output_path(tmp_path):
    """Return temporary bids2tsv command output filepath that uses the default filename."""
    return tmp_path / "bids.tsv"


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
    assert bids_tsv[["sub", "suffix", "path"]].notna().all().all()
    assert bids_tsv["sub"].str.startswith("sub-").all()
    assert bids_tsv["ses"].str.startswith("ses-").all()
    assert set(bids_tsv["suffix"].unique()) == set(["bold", "T1w"])
