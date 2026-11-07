import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from bagel.cli import bagel
from bagel.utilities import file_utils


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
            "harmonize-pheno",
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


def test_command_exits_gracefully_on_malformed_age_value(
    runner,
    test_data,
    tmp_path,
    caplog,
    propagate_errors,
):
    """
    Test that when the age transformation fails for a given combination of
    phenotypic TSV and data dictionary, the CLI exits gracefully with an informative error message.
    """
    # Set up a phenotypic TSV containing an age value that's not a valid ISO 8601 duration
    # unlike expected by the corresponding data dictionary
    phenotypic_df = file_utils.load_tabular(test_data / "example2.tsv")
    phenotypic_df.at[0, "participant_age"] = "20.5"
    phenotypic_df.to_csv(
        tmp_path / "example_with_malformed_age_value.tsv",
        sep="\t",
        index=False,
    )

    out_path = tmp_path / "harmonized.tsv"
    result = runner.invoke(
        bagel,
        [
            "harmonize-pheno",
            "--pheno",
            tmp_path / "example_with_malformed_age_value.tsv",
            "--dictionary",
            test_data
            / "example2.json",  # expects age values to be in ISO 8601 format
            "--output",
            out_path,
        ],
    )

    assert result.exit_code != 0
    assert not out_path.exists()
    assert len(caplog.records) == 1
    assert "Error applying the format nb:FromISO8601" in caplog.text
