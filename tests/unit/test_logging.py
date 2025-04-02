import pytest

from bagel.cli import bagel


@pytest.mark.parametrize(
    "extra_flag,should_error_include_traceback",
    [
        ("", False),
        ("--debug", True),
    ],
)
def test_debug_level(
    runner,
    test_data,
    tmp_path,
    extra_flag,
    should_error_include_traceback,
    caplog,
    propagate_errors,
):
    result = runner.invoke(
        bagel,
        [
            "pheno",
            "--pheno",
            test_data / "example_iso88591.tsv",
            "--dictionary",
            test_data / "example_iso88591.json",
            "--output",
            tmp_path / "pheno.jsonld",
            "--name",
            "testing dataset",
            extra_flag,
        ],
        catch_exceptions=False,
    )

    assert result.exit_code != 0
    assert ("Traceback" in caplog.text) == should_error_include_traceback
