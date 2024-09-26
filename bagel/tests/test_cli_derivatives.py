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
