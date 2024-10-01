import pytest

from bagel.cli import bagel


@pytest.fixture(scope="function")
def default_derivatives_output_path(tmp_path):
    "Return temporary derivatives command output filepath that uses the default filename."
    return tmp_path / "pheno_derivatives.jsonld"


@pytest.mark.parametrize(
    "valid_proc_status_file",
    [
        "proc_status_synthetic.tsv",
        "proc_status_unique_sessions.tsv",
    ],
)
def test_derivatives_valid_inputs_run_successfully(
    runner,
    test_data,
    test_data_upload_path,
    default_derivatives_output_path,
    valid_proc_status_file,
):
    """Basic smoke test for the "pheno" subcommand"""
    result = runner.invoke(
        bagel,
        [
            "derivatives",
            "-t",
            test_data / valid_proc_status_file,
            "-p",
            test_data_upload_path / "example_synthetic.jsonld",
            "-o",
            default_derivatives_output_path,
        ],
    )

    assert result.exit_code == 0, f"Errored out. STDOUT: {result.output}"
    assert (
        default_derivatives_output_path
    ).exists(), "The pheno.jsonld output was not created."


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
        (
            "proc_status_unique_subs.tsv",
            ["processing status file", "subject IDs not found"],
            LookupError,
        ),
    ],
)
def test_derivatives_invalid_inputs_fail(
    runner,
    test_data,
    test_data_upload_path,
    default_derivatives_output_path,
    example,
    expected_message,
    expected_error,
):
    """Assure that we handle expected user errors in the input files for the bagel derivatives command gracefully."""
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
                default_derivatives_output_path,
            ],
            catch_exceptions=False,
        )

    for substring in expected_message:
        assert substring in str(e.value)

    assert (
        not default_derivatives_output_path.exists()
    ), "The JSONLD output was still created."


@pytest.mark.parametrize(
    "proc_status_file,completed_pipes_for_missing_ses_sub",
    [
        ("proc_status_missing_sessions.tsv", {"sub-02": 2}),
        # TODO: Revisit this example once the updated Nipoppy proc status file schema is available
        # This example assumes that
        # 1. It is possible to have a subject with missing values in bids_session but not in session_id
        # 2. Duplicate entries of pipeline name, version, and step for an apparent subject-session based on bids_participant and bids_session
        # (i.e., the two columns Neurobagel looks at) are allowed (see rows 8 and 9)
        ("proc_status_no_bids_sessions.tsv", {"sub-01": 3, "sub-02": 2}),
    ],
)
def test_custom_imaging_sessions_created_for_missing_session_labels(
    runner,
    test_data,
    test_data_upload_path,
    default_derivatives_output_path,
    load_test_json,
    proc_status_file,
    completed_pipes_for_missing_ses_sub,
):
    """Test that pipeline records for a subject with missing session labels are aggregated into a custom, Neurobagel-created session."""
    result = runner.invoke(
        bagel,
        [
            "derivatives",
            "-t",
            test_data / proc_status_file,
            "-p",
            test_data_upload_path / "example_synthetic.jsonld",
            "-o",
            default_derivatives_output_path,
        ],
    )
    assert result.exit_code == 0, f"Errored out. STDOUT: {result.output}"

    output = load_test_json(default_derivatives_output_path)

    custom_ses_completed_pipes = {}
    for sub in output["hasSamples"]:
        for ses in sub["hasSession"]:
            if (
                ses["schemaKey"] == "ImagingSession"
                and ses["hasLabel"] == "ses-nb01"
            ):
                custom_ses_completed_pipes[sub["hasLabel"]] = len(
                    ses["hasCompletedPipeline"]
                )

    # Note: order of items does not matter for dict comparison
    assert custom_ses_completed_pipes == completed_pipes_for_missing_ses_sub
