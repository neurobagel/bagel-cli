import pandas as pd
import pytest
import typer

from bagel import mappings
from bagel.utilities import derivative_utils


@pytest.fixture(scope="session")
def known_pipeline_uris():
    """Return a dictionary of known pipeline URIs as parsed from the pipeline catalog."""
    return {
        "fmriprep": "np:fmriprep",
        "freesurfer": "np:freesurfer",
    }


@pytest.fixture(scope="session")
def known_pipeline_versions():
    """Return a dictionary of known pipeline versions as parsed from the pipeline catalog."""
    return {
        "fmriprep": ["20.2.7", "23.1.3"],
        "freesurfer": ["6.0.1", "7.3.2"],
    }


def test_pipeline_uris_are_loaded():
    """Test that pipeline URIs are loaded from the pipeline-catalog submodule."""

    uri_dict, _ = derivative_utils.parse_pipeline_catalog(
        mappings.PIPELINE_CATALOG
    )
    assert all(
        ((mappings.NP.pf in pipe_uri) and (" " not in pipe_uri))
        for pipe_uri in uri_dict.values()
    )


def test_pipeline_versions_are_loaded():
    """Test that pipeline versions are loaded from the pipeline-catalog submodule."""

    _, version_dict = derivative_utils.parse_pipeline_catalog(
        mappings.PIPELINE_CATALOG
    )
    assert all(
        isinstance(pipe_versions, list) and len(pipe_versions) > 0
        for pipe_versions in version_dict.values()
    )


def test_warning_raised_when_some_pipeline_names_unrecognized(
    caplog, propagate_warnings, known_pipeline_uris
):
    """
    Test that when a subset of pipeline names are not found in the pipeline catalog,
    an informative warning is raised but the recognized pipeline names are successfully returned.
    """
    pipelines = ["fmriprep", "fakepipeline1"]

    recognized_pipelines = derivative_utils.get_recognized_pipelines(
        pipelines, known_pipeline_uris
    )

    assert all(
        substr in caplog.text
        for substr in ["unrecognized pipelines", "fakepipeline1"]
    )
    assert recognized_pipelines == ["fmriprep"]


def test_error_raised_when_no_pipeline_names_recognized(
    caplog, propagate_errors, known_pipeline_uris
):
    """
    Test that when no provided pipeline names are found in the pipeline catalog,
    an informative error is raised.
    """
    pipelines = ["fakepipeline1", "fakepipeline2"]

    with pytest.raises(typer.Exit):
        derivative_utils.get_recognized_pipelines(
            pipelines, known_pipeline_uris
        )

    assert "no recognized pipelines" in caplog.text


@pytest.mark.parametrize(
    "fmriprep_versions, expected_recog_versions, expected_unrecog_versions",
    [
        (["20.2.7", "vA.B"], ["20.2.7"], ["vA.B"]),
        (["C.D.E", "F.G.H"], [], ["C.D.E", "F.G.H"]),
    ],
)
def test_pipeline_versions_classified_correctly(
    fmriprep_versions,
    expected_recog_versions,
    expected_unrecog_versions,
    known_pipeline_versions,
):
    """Test that versions of a pipeline are correctly classified as recognized or unrecognized according to the pipeline catalog."""
    recog_versions, unrecog_versions = (
        derivative_utils.validate_pipeline_versions(
            pipeline="fmriprep",
            versions=fmriprep_versions,
            known_pipeline_versions=known_pipeline_versions,
        )
    )
    # The order of the versions in the lists is not guaranteed
    assert set(recog_versions) == set(expected_recog_versions)
    assert set(unrecog_versions) == set(expected_unrecog_versions)


def test_create_completed_pipelines(
    known_pipeline_uris, known_pipeline_versions
):
    """
    Test that completed pipelines for a subject-session are accurately identified,
    where a completed pipeline is one meeting the condition that *all* steps of that pipeline
    that were run for the session are marked with a status of "SUCCESS".
    """
    sub_ses_data = [
        [
            "01",
            "sub-01",
            "01",
            "ses-01",
            "fmriprep",
            "20.2.7",
            "step1",
            "SUCCESS",
        ],
        [
            "01",
            "sub-01",
            "01",
            "ses-01",
            "fmriprep",
            "20.2.7",
            "step2",
            "FAIL",
        ],
        [
            "01",
            "sub-01",
            "01",
            "ses-01",
            "fmriprep",
            "23.1.3",
            "default",
            "SUCCESS",
        ],
    ]
    example_ses_proc_df = pd.DataFrame.from_records(
        columns=[
            "participant_id",
            "bids_participant_id",
            "session_id",
            "bids_session_id",
            "pipeline_name",
            "pipeline_version",
            "pipeline_step",
            "status",
        ],
        data=sub_ses_data,
    )
    completed_pipelines = derivative_utils.create_completed_pipelines(
        session_proc_df=example_ses_proc_df,
        known_pipeline_uris=known_pipeline_uris,
        known_pipeline_versions=known_pipeline_versions,
    )

    assert len(completed_pipelines) == 1
    assert (
        completed_pipelines[0].hasPipelineName.identifier
        == f"{mappings.NP.pf}:fmriprep"
    )
    assert completed_pipelines[0].hasPipelineVersion == "23.1.3"


def test_parse_pipeline_catalog():
    """Test the function correctly parses a pipeline catalog file into two dictionaries for pipeline URIs and recognized versions."""
    mock_pipeline_catalog = [
        {
            "name": "fmriprep",
            "versions": [
                "20.2.0",
                "20.2.7",
                "23.1.3",
            ],
        },
        {"name": "freesurfer", "versions": ["6.0.1", "7.3.2"]},
    ]
    uri_dict, version_dict = derivative_utils.parse_pipeline_catalog(
        mock_pipeline_catalog
    )
    assert uri_dict == {
        "fmriprep": "np:fmriprep",
        "freesurfer": "np:freesurfer",
    }
    assert version_dict == {
        "fmriprep": ["20.2.0", "20.2.7", "23.1.3"],
        "freesurfer": ["6.0.1", "7.3.2"],
    }
