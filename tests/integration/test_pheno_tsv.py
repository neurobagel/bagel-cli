import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from bagel.cli import bagel


@pytest.mark.parametrize(
    "raw_tsv,data_dict,expected_harmonized_tsv",
    [
        (
            "tests/neurobagel_examples/data-upload/example_synthetic.tsv",
            "tests/neurobagel_examples/data-upload/example_synthetic.json",
            "tests/data/example_synthetic_harmonized.tsv",
        ),
        (
            "tests/data/example23.tsv",
            "tests/data/example23.json",
            "tests/data/example23_harmonized.tsv",
        ),
    ],
)
def test_valid_inputs_run_successfully(
    runner,
    tmp_path,
    raw_tsv,
    data_dict,
    expected_harmonized_tsv,
):
    """
    Test that the contents of a raw phenotypic TSV are harmonized according to
    the contents of the corresponding data dictionary.
    """
    out_path = tmp_path / "harmonized.tsv"
    result = runner.invoke(
        bagel,
        [
            "pheno-tsv",
            "--pheno",
            raw_tsv,
            "--dictionary",
            data_dict,
            "--output",
            out_path,
        ],
    )

    harmonized_tsv = pd.read_csv(out_path, sep="\t")
    expected_harmonized_tsv = pd.read_csv(expected_harmonized_tsv, sep="\t")

    assert result.exit_code == 0, f"Errored out. STDOUT: {result.output}"
    assert_frame_equal(
        harmonized_tsv, expected_harmonized_tsv, check_like=True, atol=0.01
    )
