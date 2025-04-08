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
