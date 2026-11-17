import logging

import pytest

from bagel.cli import bagel


@pytest.mark.parametrize(
    "verbosity_level,expected_log_levels",
    [("3", {logging.INFO, logging.ERROR}), ("0", {logging.ERROR})],
)
def test_verbosity_level(
    runner,
    test_data,
    example_dataset_description,
    tmp_path,
    verbosity_level,
    expected_log_levels,
    caplog,
):
    """Test that for invalid inputs, the correct level of logs are produced based on the set verbosity."""
    result = runner.invoke(
        bagel,
        [
            "create",
            "--pheno",
            test_data / "example1.tsv",
            "--dictionary",
            test_data / "example1.json",
            "--output",
            tmp_path / "pheno.jsonld",
            "--dataset-description",
            example_dataset_description,
            "--verbosity",
            verbosity_level,
        ],
        catch_exceptions=False,
    )

    captured_log_levels = {record.levelno for record in caplog.records}
    missing_log_levels = expected_log_levels - captured_log_levels
    unexpected_log_levels = captured_log_levels - expected_log_levels

    assert result.exit_code != 0
    assert (
        not missing_log_levels
    ), f"Missing log level(s): {missing_log_levels}"
    assert (
        not unexpected_log_levels
    ), f"Unexpected log level(s): {unexpected_log_levels}"


def test_no_progress_graphic_with_min_verbosity(
    runner,
    test_data_upload_path,
    tmp_path,
):
    """Test that on a successful run, no output is shown when verbosity is set to 0 (errors only)."""
    result = runner.invoke(
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
            test_data_upload_path / "example_synthetic_bids_metadata.tsv",
            "--output",
            tmp_path / "bids.jsonld",
            "--verbosity",
            "0",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert result.output.strip() == ""


def test_only_errors_and_warnings_logged_for_verbosity_level_1(
    runner,
    test_data_upload_path,
    test_data,
    tmp_path,
    caplog,
):
    """Test that info logs are suppressed when verbosity is set to 1 (warnings logs and above only)."""
    result = runner.invoke(
        bagel,
        [
            "create",
            "--pheno",
            # example with >1 columns annotated to sex and diagnosis - warning expected
            test_data / "example20.tsv",
            "--dictionary",
            test_data / "example20.json",
            "--dataset-description",
            test_data_upload_path / "synthetic_dataset_description.json",
            "--processing-status",
            # example with subject IDs missing from phenotypic data - error expected
            test_data / "proc_status_unique_subs.tsv",
            "--output",
            tmp_path / "pheno_derivatives.jsonld",
            "--verbosity",
            "1",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code != 0
    captured_log_levels = {record.levelno for record in caplog.records}
    assert set(captured_log_levels) == {logging.WARNING, logging.ERROR}
