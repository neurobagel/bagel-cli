from collections import defaultdict

import pytest

from bagel import mappings
from bagel.cli import bagel


@pytest.fixture(scope="function")
def synthetic_dataset_phenotypic_inputs(
    test_data_upload_path, example_dataset_description
):
    """Return option values for the example phenotypic input files corresponding to the synthetic dataset."""
    return [
        "--pheno",
        test_data_upload_path / "example_synthetic.tsv",
        "--dictionary",
        test_data_upload_path / "example_synthetic.json",
        "--dataset-description",
        example_dataset_description,
    ]


@pytest.mark.parametrize(
    "valid_proc_status_file,num_expected_imaging_sessions",
    [
        ("proc_status_synthetic.tsv", {"sub-01": 1, "sub-02": 2}),
        ("proc_status_unique_sessions.tsv", {"sub-01": 2, "sub-02": 2}),
    ],
)
def test_valid_derivatives_input_is_successful(
    runner,
    synthetic_dataset_phenotypic_inputs,
    test_data,
    temp_output_jsonld_path,
    load_test_json,
    valid_proc_status_file,
    num_expected_imaging_sessions,
):
    """
    Test that when a valid processing status TSV is included as an input,
    the "create" command successfully creates an output JSONLD where subjects have the expected number
    of imaging sessions created based on pipeline completion data.

    Also performs a sanity check that an @context is present in the output JSONLD.
    """
    result = runner.invoke(
        bagel,
        [
            "create",
            *synthetic_dataset_phenotypic_inputs,
            "-n",
            test_data / valid_proc_status_file,
            "-o",
            temp_output_jsonld_path,
        ],
    )

    assert result.exit_code == 0, f"Errored out. STDOUT: {result.output}"

    output = load_test_json(temp_output_jsonld_path)
    num_created_imaging_sessions = defaultdict(int)
    for sub in output["hasSamples"]:
        for ses in sub["hasSession"]:
            if ses["schemaKey"] == "ImagingSession":
                num_created_imaging_sessions[sub["hasLabel"]] += 1

    assert (
        output.get("@context") is not None
    ), "The output JSONLD is missing an @context."
    assert num_created_imaging_sessions == num_expected_imaging_sessions


def test_pipeline_info_added_to_existing_imaging_sessions(
    runner,
    test_data,
    synthetic_dataset_phenotypic_inputs,
    temp_output_jsonld_path,
    load_test_json,
):
    """
    Test that when both a valid processing status TSV and BIDS metadata TSV
    are supplied as inputs, the bagel derivatives command successfully creates an output JSONLD
    where pipeline completion info is correctly matched to BIDS imaging sessions.
    """
    result = runner.invoke(
        bagel,
        [
            "create",
            *synthetic_dataset_phenotypic_inputs,
            "-b",
            test_data / "bids_metadata_synthetic.tsv",
            "-n",
            test_data / "proc_status_unique_sessions.tsv",
            "-o",
            temp_output_jsonld_path,
        ],
    )

    assert result.exit_code == 0, f"Errored out. STDOUT: {result.output}"
    output = load_test_json(temp_output_jsonld_path)

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
    "example,expected_message",
    [
        (
            "proc_status_synthetic_incomplete.tsv",
            ["missing", "status"],
        ),
        (
            "proc_status_synthetic.csv",
            ["processing status", "not a .tsv file"],
        ),
        (
            "proc_status_unique_subs.tsv",
            ["processing status file", "subject IDs not found"],
        ),
    ],
)
def test_derivatives_invalid_inputs_fail(
    runner,
    test_data,
    synthetic_dataset_phenotypic_inputs,
    temp_output_jsonld_path,
    example,
    expected_message,
    caplog,
    propagate_errors,
):
    """Assure that we handle expected user errors from the processing status file gracefully."""
    result = runner.invoke(
        bagel,
        [
            "create",
            *synthetic_dataset_phenotypic_inputs,
            "-n",
            test_data / example,
            "-o",
            temp_output_jsonld_path,
        ],
        catch_exceptions=False,
    )

    assert result.exit_code != 0
    assert len(caplog.records) == 1
    for substring in expected_message:
        assert substring in caplog.text

    assert (
        not temp_output_jsonld_path.exists()
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
    synthetic_dataset_phenotypic_inputs,
    temp_output_jsonld_path,
    load_test_json,
    proc_status_file,
    completed_pipes_for_missing_ses_sub,
):
    """Test that pipeline records for a subject with missing session labels are aggregated into a custom, Neurobagel-created session."""
    result = runner.invoke(
        bagel,
        [
            "create",
            *synthetic_dataset_phenotypic_inputs,
            "-n",
            test_data / proc_status_file,
            "-o",
            temp_output_jsonld_path,
        ],
    )
    assert result.exit_code == 0, f"Errored out. STDOUT: {result.output}"

    output = load_test_json(temp_output_jsonld_path)

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
    synthetic_dataset_phenotypic_inputs,
    temp_output_jsonld_path,
    load_test_json,
    caplog,
    propagate_warnings,
):
    """
    Test that when a subset of pipelines or versions from a processing status file are unrecognized,
    they are excluded from the output JSONLD with informative warnings, without causing the command to fail.
    """
    result = runner.invoke(
        bagel,
        [
            "create",
            *synthetic_dataset_phenotypic_inputs,
            "-n",
            test_data / "proc_status_unrecognized_pipelines.tsv",
            "-o",
            temp_output_jsonld_path,
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

    output = load_test_json(temp_output_jsonld_path)

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
    synthetic_dataset_phenotypic_inputs,
    temp_output_jsonld_path,
    caplog,
    propagate_errors,
):
    """
    Test that when there is no recognized pipeline-version combination in the processing status file,
    the app exits with an error and no output JSONLD is created.
    """
    result = runner.invoke(
        bagel,
        [
            "create",
            *synthetic_dataset_phenotypic_inputs,
            "-n",
            test_data / "proc_status_no_recognized_pipelines.tsv",
            "-o",
            temp_output_jsonld_path,
        ],
        catch_exceptions=False,
    )

    assert result.exit_code != 0
    assert len(caplog.records) == 1
    assert "no recognized versions" in caplog.text
    assert (
        not temp_output_jsonld_path.exists()
    ), "A JSONLD was created despite inputs being invalid."


def test_failed_pipeline_catalog_fetching_does_not_raise_error_for_help(
    runner, caplog, propagate_warnings, monkeypatch, disable_rich_markup
):
    """
    Test that if the pipeline catalog fetching fails when a processing status file has not been provided,
    this happens silently and the CLI does not raise an error.
    """
    monkeypatch.setattr(mappings, "PIPELINE_CATALOG", [])
    monkeypatch.setattr(
        mappings, "PIPELINES_FETCHING_ERR", "Network unreachable"
    )

    result = runner.invoke(
        bagel,
        ["--help"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert len(caplog.records) == 0
    assert (
        "Run 'bagel COMMAND --help' for more information on a command"
        in result.output
    )
    assert "Failed to locate a pipeline catalog" not in result.output


@pytest.mark.parametrize(
    "mock_pipeline_catalog_fetching_result,expected_exit_code,expected_err,output_created_expectation",
    [
        (
            [
                {
                    "name": "fmriprep",
                    "versions": ["20.2.0", "20.2.7", "23.1.3", "24.1.1"],
                },
                {"name": "freesurfer", "versions": ["6.0.1", "7.3.2"]},
            ],
            0,
            "Using a packaged backup pipeline catalog",
            True,
        ),
        ([], 1, "Failed to load the pipeline catalog", False),
    ],
)
def test_failed_pipeline_catalog_fetching_raises_err_for_derivatives_input(
    runner,
    test_data,
    synthetic_dataset_phenotypic_inputs,
    temp_output_jsonld_path,
    caplog,
    propagate_warnings,
    monkeypatch,
    mock_pipeline_catalog_fetching_result,
    expected_exit_code,
    expected_err,
    output_created_expectation,
):
    """
    Test that when a processing status file is provided and the pipeline catalog fetching fails,
    the command raises an appropriate warning or error depending on if the backup catalog could be loaded.
    """
    monkeypatch.setattr(
        mappings, "PIPELINE_CATALOG", mock_pipeline_catalog_fetching_result
    )
    monkeypatch.setattr(
        mappings, "PIPELINES_FETCHING_ERR", "Network unreachable"
    )

    result = runner.invoke(
        bagel,
        [
            "create",
            *synthetic_dataset_phenotypic_inputs,
            "-n",
            test_data / "proc_status_synthetic.tsv",
            "-o",
            temp_output_jsonld_path,
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == expected_exit_code
    assert len(caplog.records) == 1
    assert expected_err in caplog.text
    assert temp_output_jsonld_path.exists() is output_created_expectation
