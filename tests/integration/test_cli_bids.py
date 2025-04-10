from pathlib import Path

import pytest

from bagel.cli import bagel


@pytest.fixture(scope="function")
def default_pheno_bids_output_path(tmp_path):
    "Return temporary bids command output filepath that uses the default filename."
    return tmp_path / "pheno_bids.jsonld"


def test_bids_valid_inputs_run_successfully(
    runner,
    test_data_upload_path,
    bids_synthetic,
    default_pheno_bids_output_path,
):
    """Basic smoke test for the "add-bids" subcommand"""
    result = runner.invoke(
        bagel,
        [
            "bids",
            "--jsonld-path",
            test_data_upload_path / "example_synthetic.jsonld",
            "--input-bids-dir",
            bids_synthetic,
            "--bids-dir",
            bids_synthetic,
            "--output",
            default_pheno_bids_output_path,
        ],
    )
    assert result.exit_code == 0, f"Errored out. STDOUT: {result.output}"
    assert (
        default_pheno_bids_output_path
    ).exists(), "The pheno_bids.jsonld output was not created."


def test_imaging_sessions_have_expected_labels(
    runner,
    test_data_upload_path,
    bids_synthetic,
    default_pheno_bids_output_path,
    load_test_json,
):
    """Check that the imaging sessions in the JSONLD output have the expected session labels."""
    runner.invoke(
        bagel,
        [
            "bids",
            "--jsonld-path",
            test_data_upload_path / "example_synthetic.jsonld",
            "--input-bids-dir",
            bids_synthetic,
            "--bids-dir",
            bids_synthetic,
            "--output",
            default_pheno_bids_output_path,
        ],
    )

    output = load_test_json(default_pheno_bids_output_path)

    for sub in output["hasSamples"]:
        # all subjects in the BIDS synthetic dataset are expected to have 4 sessions total
        assert 4 == len(sub["hasSession"])

        imaging_ses_labels = [
            ses["hasLabel"]
            for ses in sub["hasSession"]
            if ses["schemaKey"] == "ImagingSession"
        ]

        assert sorted(imaging_ses_labels) == ["ses-01", "ses-02"]


@pytest.mark.parametrize(
    "jsonld_path,expected_sessions_with_acq_and_pipe_metadata",
    [
        ("example_synthetic.jsonld", 0),
        (
            "pheno-derivatives-output/example_synthetic_pheno-derivatives.jsonld",
            3,
        ),
    ],
)
def test_imaging_sessions_have_expected_metadata(
    runner,
    test_data_upload_path,
    bids_synthetic,
    default_pheno_bids_output_path,
    load_test_json,
    jsonld_path,
    expected_sessions_with_acq_and_pipe_metadata,
):
    """
    Check that the JSONLD output contains the expected total number of imaging sessions with
    acquisition and completed pipeline metadata, based on whether a phenotypic-only JSONLD or
    JSONLD with both phenotypic and processing pipeline metadata is provided as input.
    """
    runner.invoke(
        bagel,
        [
            "bids",
            "--jsonld-path",
            test_data_upload_path / jsonld_path,
            "--input-bids-dir",
            bids_synthetic,
            "--bids-dir",
            bids_synthetic,
            "--output",
            default_pheno_bids_output_path,
        ],
    )

    output = load_test_json(default_pheno_bids_output_path)

    sessions_with_acq_metadata = []
    sessions_with_acq_and_pipe_metadata = []
    for sub in output["hasSamples"]:
        for ses in sub["hasSession"]:
            if (
                ses["schemaKey"] == "ImagingSession"
                and ses.get("hasAcquisition") is not None
            ):
                sessions_with_acq_metadata.append(ses)
                if ses.get("hasCompletedPipeline") is not None:
                    sessions_with_acq_and_pipe_metadata.append(ses)

    assert len(sessions_with_acq_metadata) == 10
    assert (
        len(sessions_with_acq_and_pipe_metadata)
        == expected_sessions_with_acq_and_pipe_metadata
    )


def test_bids_data_with_sessions_have_correct_paths(
    runner,
    test_data_upload_path,
    bids_synthetic,
    default_pheno_bids_output_path,
    load_test_json,
):
    """
    Check that BIDS session paths added to pheno_bids.jsonld match the parent
    session/subject labels and have the correct base directory path matching the provided --bids-dir.
    """
    runner.invoke(
        bagel,
        [
            "bids",
            "--jsonld-path",
            test_data_upload_path / "example_synthetic.jsonld",
            "--input-bids-dir",
            bids_synthetic,
            "--bids-dir",
            Path(__file__).absolute().parent
            / "example_public_datasets"
            / "public_synthetic",
            "--output",
            default_pheno_bids_output_path,
        ],
    )

    pheno_bids = load_test_json(default_pheno_bids_output_path)
    for sub in pheno_bids["hasSamples"]:
        for imaging_session in [
            ses
            for ses in sub["hasSession"]
            if ses["schemaKey"] == "imaging_session"
        ]:
            assert (
                f"example_public_datasets/public_synthetic/{sub['hasLabel']}/{imaging_session['hasLabel']}"
                in imaging_session["hasFilePath"]
            )
            assert Path(imaging_session["hasFilePath"]).is_absolute()
            assert Path(imaging_session["hasFilePath"]).is_dir()


def test_relative_bids_dir_path_raises_error(
    runner,
    test_data_upload_path,
    default_pheno_bids_output_path,
    disable_rich_markup,
):
    """Check that a relative BIDS directory path raises an error."""
    result = runner.invoke(
        bagel,
        [
            "bids",
            "--jsonld-path",
            test_data_upload_path / "example_synthetic.jsonld",
            "--bids-dir",
            "data/bids",
            "--output",
            default_pheno_bids_output_path,
        ],
        catch_exceptions=False,
    )
    assert result.exit_code != 0
    assert "must be an absolute path" in result.output
