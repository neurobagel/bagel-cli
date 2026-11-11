import pytest

from bagel.cli import bagel


@pytest.mark.parametrize(
    "additional_cli_option,is_output_expected",
    [
        (["--strict"], False),
        ([], True),
    ],
)
def test_strict_mode_for_non_phenotypic_file_parsing_errors(
    runner,
    test_data,
    test_data_upload_path,
    temp_output_jsonld_path,
    caplog,
    propagate_errors,
    additional_cli_option,
    is_output_expected,
):
    # TODO: add docstring
    runner.invoke(
        bagel,
        [
            "create",
            "--pheno",
            test_data_upload_path / "example_synthetic.tsv",
            "--dictionary",
            test_data_upload_path / "example_synthetic.json",
            "--dataset-description",
            test_data_upload_path / "synthetic_dataset_description.json",
            "--bids-table",
            # not a real BIDS table, just a placeholder for a non-UTF-8 encoded TSV file
            test_data / "example_iso88591.tsv",
            "--output",
            temp_output_jsonld_path,
            *additional_cli_option,
        ],
        catch_exceptions=False,
    )

    assert len(caplog.records) == 1
    assert "Error parsing BIDS table" in caplog.text
    assert temp_output_jsonld_path.exists() == is_output_expected
