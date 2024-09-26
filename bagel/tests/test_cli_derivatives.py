import pytest

from bagel.cli import bagel


def test_derivatives_valid_inputs_run_successfully(
    runner,
    test_data,
    test_data_upload_path,
):
    """Basic smoke test for the "pheno" subcommand"""
    example = "proc_status_synthetic"
    output_file = "pheno_derivatives.jsonld"

    result = runner.invoke(
        bagel,
        [
            "derivatives",
            "-t",
            test_data / f"{example}.tsv",
            "-p",
            test_data_upload_path / "example_synthetic.jsonld",
            "-o",
            output_file,
        ],
    )

    assert result.exit_code == 0, f"Errored out. STDOUT: {result.output}"
    # assert (
    #     output_file
    # ).exists(), "The pheno.jsonld output was not created."


@pytest.mark.parametrize(
    "example,expected_message,expected_error",
    [
        (
            "proc_status_synthetic_incomplete.tsv",
            ["missing", "status"],
            LookupError,
        ),
        (
            "proc_status_synthetic.csv",
            ["processing status", "not a .tsv file"],
            ValueError,
        ),
    ],
)
def test_derivatives_invalid_inputs_fail(
    runner,
    test_data,
    test_data_upload_path,
    example,
    expected_message,
    expected_error,
):
    """Basic smoke test for the "pheno" subcommand"""
    output_file = "pheno_derivatives.jsonld"

    with pytest.raises(expected_error) as e:
        runner.invoke(
            bagel,
            [
                "derivatives",
                "-t",
                test_data / example,
                "-p",
                test_data_upload_path / "example_synthetic.jsonld",
                "-o",
                output_file,
            ],
            catch_exceptions=False,
        )

    for substring in expected_message:
        assert substring in str(e.value)
