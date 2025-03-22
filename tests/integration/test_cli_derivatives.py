from collections import defaultdict

import pytest

from bagel import mappings
from bagel.cli import bagel


@pytest.fixture(scope="function")
def default_derivatives_output_path(tmp_path):
    "Return temporary derivatives command output filepath that uses the default filename."
    return tmp_path / "pheno_derivatives.jsonld"


@pytest.mark.parametrize(
    "valid_proc_status_file,num_expected_imaging_sessions",
    [
        ("proc_status_synthetic.tsv", {"sub-01": 1, "sub-02": 2}),
        ("proc_status_unique_sessions.tsv", {"sub-01": 2, "sub-02": 2}),
    ],
)
def test_derivatives_cmd_with_valid_TSV_and_pheno_jsonlds_is_successful(
    runner,
    test_data,
    test_data_upload_path,
    default_derivatives_output_path,
    load_test_json,
    valid_proc_status_file,
    num_expected_imaging_sessions,
):
    """
    Test that when a valid processing status TSV and bagel pheno-created JSONLD are supplied as inputs,
    the bagel derivatives command successfully creates an output JSONLD where subjects have the expected number
    of imaging sessions created based on pipeline completion data.
    """
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

    output = load_test_json(default_derivatives_output_path)
    num_created_imaging_sessions = defaultdict(int)
    for sub in output["hasSamples"]:
        for ses in sub["hasSession"]:
            if ses["schemaKey"] == "ImagingSession":
                num_created_imaging_sessions[sub["hasLabel"]] += 1

    assert num_created_imaging_sessions == num_expected_imaging_sessions


def test_pipeline_info_added_to_existing_imaging_sessions(
    runner,
    test_data,
    test_data_upload_path,
    default_derivatives_output_path,
    load_test_json,
):
    """
    Test that when a valid processing status TSV and bagel pheno- and bagel bids-created JSONLD
    are supplied as inputs, the bagel derivatives command successfully creates an output JSONLD
    where pipeline completion info is correctly added to existing or newly created imaging sessions.
    """
    result = runner.invoke(
        bagel,
        [
            "derivatives",
            "-t",
            test_data / "proc_status_unique_sessions.tsv",
            "-p",
            test_data_upload_path
            / "pheno-bids-output"
            / "example_synthetic_pheno-bids.jsonld",
            "-o",
            default_derivatives_output_path,
        ],
    )

    assert result.exit_code == 0, f"Errored out. STDOUT: {result.output}"
    output = load_test_json(default_derivatives_output_path)

    # Only consider sub-01 for simplicity
    ses_with_raw_imaging = []
    ses_with_derivatives = []
    for sub01_ses in output["hasSamples"][0]["hasSession"]:
        if sub01_ses["schemaKey"] == "ImagingSession":
            if sub01_ses.get("hasAcquisition") is not None:
                ses_with_raw_imaging.append(sub01_ses["hasLabel"])
            if sub01_ses.get("hasCompletedPipeline") is not None:
                ses_with_derivatives.append(sub01_ses["hasLabel"])

    assert sorted(ses_with_raw_imaging) == ["ses-01", "ses-02"]
    assert sorted(ses_with_derivatives) == ["ses-01", "ses-03"]


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
    ), "The JSONLD output was created despite inputs being invalid."


@pytest.mark.parametrize(
    "proc_status_file,completed_pipes_for_missing_ses_sub",
    [
        ("proc_status_missing_sessions.tsv", {"sub-02": 2}),
        # TODO: Revisit this example once the updated Nipoppy proc status file schema is available
        # This example assumes that
        # 1. It is possible to have a subject with missing values in bids_session_id but not in session_id
        # 2. Duplicate entries of pipeline name, version, and step for an apparent subject-session based on bids_participant_id and bids_session_id
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
                and ses["hasLabel"] == "ses-unnamed"
            ):
                custom_ses_completed_pipes[sub["hasLabel"]] = len(
                    ses["hasCompletedPipeline"]
                )

    # Note: order of items does not matter for dict comparison
    assert custom_ses_completed_pipes == completed_pipes_for_missing_ses_sub


def test_unrecognized_pipelines_and_versions_excluded_from_output(
    runner,
    test_data,
    test_data_upload_path,
    default_derivatives_output_path,
    load_test_json,
    caplog,
    propagate_warnings,
):
    """
    Test that when a subset of pipelines or versions from a processing status file are unrecognized,
    they are excluded from the output JSONLD with informative warnings, without causing the derivatives command to fail.
    """
    result = runner.invoke(
        bagel,
        [
            "derivatives",
            "-t",
            test_data / "proc_status_unrecognized_pipelines.tsv",
            "-p",
            test_data_upload_path / "example_synthetic.jsonld",
            "-o",
            default_derivatives_output_path,
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, f"Errored out. STDOUT: {result.output}"

    assert len(caplog.records) == 2
    for warning in caplog.records:
        assert (
            "unrecognized pipelines" in warning.message
            and "unknown-pipeline" in warning.message
        ) or (
            "unrecognized versions" in warning.message
            and "{'fmriprep': ['unknown.version']}" in warning.message
        )

    output = load_test_json(default_derivatives_output_path)

    sessions_with_completed_pipes = {}
    for sub in output["hasSamples"]:
        if sub["hasLabel"] == "sub-01":
            for ses in sub["hasSession"]:
                if (
                    ses["schemaKey"] == "ImagingSession"
                    and "hasCompletedPipeline" in ses
                ):
                    sessions_with_completed_pipes[ses["hasLabel"]] = ses[
                        "hasCompletedPipeline"
                    ]

    ses01_completed_pipes = sessions_with_completed_pipes.get("ses-01")
    assert sessions_with_completed_pipes.keys() == {"ses-01"}
    assert len(ses01_completed_pipes) == 1
    assert (
        ses01_completed_pipes[0]["hasPipelineName"]["identifier"]
        == f"{mappings.NP.pf}:freesurfer"
    )
    assert ses01_completed_pipes[0]["hasPipelineVersion"] == "7.3.2"


def test_error_when_no_pipeline_version_combos_recognized(
    runner,
    test_data,
    test_data_upload_path,
    default_derivatives_output_path,
    load_test_json,
):
    """
    Test that when there is no recognized pipeline-version combination in the processing status file,
    an error is raised and no output JSONLD is created.
    """
    with pytest.raises(LookupError) as e:
        runner.invoke(
            bagel,
            [
                "derivatives",
                "-t",
                test_data / "proc_status_no_recognized_pipelines.tsv",
                "-p",
                test_data_upload_path / "example_synthetic.jsonld",
                "-o",
                default_derivatives_output_path,
            ],
            catch_exceptions=False,
        )

    assert "no recognized versions" in str(e.value)
    assert (
        not default_derivatives_output_path.exists()
    ), "A JSONLD was created despite inputs being invalid."
