import pandas as pd
import pytest

from bagel.cli import bagel


@pytest.fixture(scope="function")
def valid_synthetic_phenotypic_inputs(
    test_data_upload_path, example_dataset_description
):
    """
    Return option values for the example valid phenotypic input files
    corresponding to the synthetic dataset.
    """
    return [
        "--pheno",
        test_data_upload_path / "example_synthetic.tsv",
        "--dictionary",
        test_data_upload_path / "example_synthetic.json",
        "--dataset-description",
        example_dataset_description,
    ]


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
    temp_output_jsonld_path,
    valid_synthetic_phenotypic_inputs,
    caplog,
    propagate_errors,
    additional_cli_option,
    is_output_expected,
):
    """
    Test that regardless of whether the CLI is running in strict or non-strict mode,
    any parsing errors for input files are always collected and returned together.
    """
    runner.invoke(
        bagel,
        [
            "create",
            *valid_synthetic_phenotypic_inputs,
            "--bids-table",
            # not a real BIDS table, just a placeholder for a non-UTF-8 encoded TSV file
            test_data / "example_iso88591.tsv",
            "--processing-status",
            # not a real processing status table, just a placeholder for a non-UTF-8 encoded TSV file
            test_data / "example_iso88591.tsv",
            "--output",
            temp_output_jsonld_path,
            *additional_cli_option,
        ],
        catch_exceptions=False,
    )

    assert len(caplog.records) == 2
    assert "Error parsing BIDS table" in caplog.text
    assert "Error parsing processing status TSV" in caplog.text
    assert temp_output_jsonld_path.exists() == is_output_expected


def test_partial_jsonld_created_when_only_phenotypic_inputs_valid(
    runner,
    test_data,
    tmp_path,
    temp_output_jsonld_path,
    valid_synthetic_phenotypic_inputs,
    caplog,
    propagate_warnings,
    load_test_json,
):
    """
    Test that in non-strict mode, when only the phenotypic inputs pass validation,
    a partial JSON-LD is still created and informative errors and warnings are logged for the
    incomplete BIDS and derivative metadata processing.
    """

    expected_errors = [
        "subject IDs not found in the phenotypic table",
        "no recognized versions of any pipelines",
    ]
    expected_warnings = [
        "Imaging metadata could not be added",
        "Processing pipeline metadata could not be added",
    ]

    invalid_bids_table_path = tmp_path / "bids_with_unrecognized_subjects.tsv"
    invalid_bids_table = pd.DataFrame(
        [
            [
                "sub-990",
                "ses-01",
                "T1w",
                "/data/synthetic/sub-01/ses-01/anat/sub-990_ses-01_T1w.nii.gz",
            ],
            [
                "sub-990",
                "ses-01",
                "bold",
                "/data/synthetic/sub-01/ses-01/func/sub-990_ses-01_task-nback_run-01_bold.nii.gz",
            ],
            [
                "sub-991",
                "ses-01",
                "T1w",
                "/data/synthetic/sub-02/ses-01/anat/sub-991_ses-01_T1w.nii.gz",
            ],
            [
                "sub-991",
                "ses-01",
                "bold",
                "/data/synthetic/sub-02/ses-01/func/sub-991_ses-01_task-nback_run-01_bold.nii.gz",
            ],
        ],
        columns=["sub", "ses", "suffix", "path"],
    )
    invalid_bids_table.to_csv(invalid_bids_table_path, sep="\t", index=False)
    invalid_proc_status_table_path = (
        test_data / "proc_status_no_recognized_pipelines.tsv"
    )

    result = runner.invoke(
        bagel,
        [
            "create",
            *valid_synthetic_phenotypic_inputs,
            "--bids-table",
            invalid_bids_table_path,
            "--processing-status",
            invalid_proc_status_table_path,
            "--output",
            temp_output_jsonld_path,
        ],
        catch_exceptions=False,
    )
    output = load_test_json(temp_output_jsonld_path)

    warnings = [
        record for record in caplog.records if record.levelname == "WARNING"
    ]
    errors = [
        record for record in caplog.records if record.levelname == "ERROR"
    ]

    assert result.exit_code == 0
    assert len(errors) == 2
    assert len(warnings) == 2
    for expected_error in expected_errors:
        assert any(expected_error in record.message for record in errors)
    for expected_warning in expected_warnings:
        assert any(expected_warning in record.message for record in warnings)
    for sub in output["hasSamples"]:
        session_types = [ses["schemaKey"] for ses in sub["hasSession"]]
        assert session_types.count("PhenotypicSession") == 2
        assert session_types.count("ImagingSession") == 0


def test_partial_jsonld_created_when_only_phenotypic_and_derivatives_inputs_valid(
    runner,
    test_data_upload_path,
    tmp_path,
    temp_output_jsonld_path,
    valid_synthetic_phenotypic_inputs,
    caplog,
    propagate_warnings,
    load_test_json,
):
    """
    Test that in non-strict mode, when the phenotypic and derivatives inputs pass validation
    but the BIDS inputs do not, a partial JSON-LD is still created and an informative error
    and warning are logged for the incomplete BIDS metadata processing.
    """

    invalid_bids_table = pd.DataFrame(
        [
            [
                "sub-990",
                "ses-01",
                "T1w",
                "/data/synthetic/sub-01/ses-01/anat/sub-990_ses-01_T1w.nii.gz",
            ],
            [
                "sub-990",
                "ses-01",
                "bold",
                "/data/synthetic/sub-01/ses-01/func/sub-990_ses-01_task-nback_run-01_bold.nii.gz",
            ],
            [
                "sub-991",
                "ses-01",
                "T1w",
                "/data/synthetic/sub-02/ses-01/anat/sub-991_ses-01_T1w.nii.gz",
            ],
            [
                "sub-991",
                "ses-01",
                "bold",
                "/data/synthetic/sub-02/ses-01/func/sub-991_ses-01_task-nback_run-01_bold.nii.gz",
            ],
        ],
        columns=["sub", "ses", "suffix", "path"],
    )
    invalid_bids_table.to_csv(
        tmp_path / "bids_with_unrecognized_subjects.tsv", sep="\t", index=False
    )

    result = runner.invoke(
        bagel,
        [
            "create",
            *valid_synthetic_phenotypic_inputs,
            "--bids-table",
            tmp_path / "bids_with_unrecognized_subjects.tsv",
            "--processing-status",
            test_data_upload_path / "nipoppy_proc_status_synthetic.tsv",
            "--output",
            temp_output_jsonld_path,
        ],
        catch_exceptions=False,
    )
    output = load_test_json(temp_output_jsonld_path)

    imaging_sessions = []
    for sub in output["hasSamples"]:
        for ses in sub["hasSession"]:
            if ses["schemaKey"] == "ImagingSession":
                imaging_sessions.append(ses)

    warnings = [
        record for record in caplog.records if record.levelname == "WARNING"
    ]
    errors = [
        record for record in caplog.records if record.levelname == "ERROR"
    ]

    assert result.exit_code == 0
    assert len(errors) == 1
    assert len(warnings) == 1
    assert "subject IDs not found in the phenotypic table" in errors[0].message
    assert "Imaging metadata could not be added" in warnings[0].message
    assert len(imaging_sessions) > 0
    assert not any("hasContrastType" in ses for ses in imaging_sessions)
    assert any("hasCompletedPipeline" in ses for ses in imaging_sessions)
