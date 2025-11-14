import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from bagel.cli import bagel


@pytest.mark.parametrize(
    "raw_tsv,data_dict,expected_harmonized_tsv",
    [
        (
            "neurobagel_examples/data-upload/example_synthetic.tsv",
            "neurobagel_examples/data-upload/example_synthetic.json",
            "data/example_synthetic_harmonized.tsv",
        ),
        (
            "data/example23.tsv",
            "data/example23.json",
            "data/example23_harmonized.tsv",
        ),
    ],
)
def test_valid_inputs_run_successfully(
    runner,
    tests_base_path,
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
            tests_base_path / raw_tsv,
            "--dictionary",
            tests_base_path / data_dict,
            "--output",
            out_path,
        ],
    )

    harmonized_tsv = pd.read_csv(out_path, sep="\t")
    expected_harmonized_tsv = pd.read_csv(
        tests_base_path / expected_harmonized_tsv, sep="\t"
    )

    assert result.exit_code == 0, f"Errored out. STDOUT: {result.output}"
    # The original column order may not be preserved
    assert_frame_equal(
        harmonized_tsv,
        expected_harmonized_tsv,
        check_like=True,
        check_exact=False,
        atol=0.01,
    )
