import logging

import pytest

from bagel.cli import bagel


@pytest.mark.parametrize(
    "verbosity_level,expected_log_levels",
    [("1", {logging.INFO, logging.ERROR}), ("0", {logging.ERROR})],
)
def test_verbosity_level(
    runner,
    test_data,
    tmp_path,
    verbosity_level,
    expected_log_levels,
    caplog,
):
    """Test that for invalid inputs, the correct level of logs are produced based on the set verbosity."""
    result = runner.invoke(
        bagel,
        [
            "pheno",
            "--pheno",
            test_data / "example1.tsv",
            "--dictionary",
            test_data / "example1.json",
            "--output",
            tmp_path / "pheno.jsonld",
            "--name",
            "testing dataset",
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


@pytest.mark.parametrize(
    "verbosity_level,is_progress_bar_shown",
    [("0", False), ("1", True)],
)
def test_no_progress_graphic_with_min_verbosity(
    runner,
    test_data_upload_path,
    tmp_path,
    verbosity_level,
    is_progress_bar_shown,
):
    """Test that progress bar is not shown when verbosity is set to 0 (errors only)."""
    result = runner.invoke(
        bagel,
        [
            "bids",
            "--bids-table",
            test_data_upload_path / "example_synthetic_bids_metadata.tsv",
            "--jsonld-path",
            test_data_upload_path / "example_synthetic.jsonld",
            "--output",
            tmp_path / "bids.jsonld",
            "--verbosity",
            verbosity_level,
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert (
        "Processing BIDS subjects..." in result.output
    ) is is_progress_bar_shown
