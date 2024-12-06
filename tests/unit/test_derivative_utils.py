import httpx
import pandas as pd
import pytest

from bagel import mappings
from bagel.utilities import derivative_utils


def test_get_pipeline_from_backup_if_remote_fails(monkeypatch):
    """
    Test that the pipeline catalog is loaded from the local backup if the remote location is unreachable.

    NOTE: This test will fail if the submodule has not been correctly initialized.
    """
    nonsense_url = "https://does.not.exist.url"

    def mock_httpx_get(*args, **kwargs):
        response = httpx.Response(
            status_code=400,
            json={},
            text="Some error",
            request=httpx.Request("GET", nonsense_url),
        )
        # This slightly odd construction is necessary to create a Response object
        # that has the correct URL already baked in (I think), because otherwise we get the following
        # RuntimeError: Cannot call `raise_for_status` as the request instance has not been set on this response.
        return response

    monkeypatch.setattr(httpx, "get", mock_httpx_get)

    with pytest.warns(UserWarning) as w:
        result = mappings.get_pipeline_catalog(
            url=nonsense_url, path=mappings.PROCESSING_PIPELINE_PATH
        )

    assert all(isinstance(item, dict) for item in result)
    assert "Unable to download pipeline catalog" in w[0].message.args[0]


def test_raises_exception_if_remote_and_local_pipeline_catalog_fails(
    monkeypatch, tmp_path
):
    """
    If I cannot get the pipeline catalog from the remote location and the local backup, I should raise an exception.
    """
    nonsense_url = "https://does.not.exist.url"

    def mock_httpx_get(*args, **kwargs):
        response = httpx.Response(
            status_code=400,
            json={},
            text="Some error",
            request=httpx.Request("GET", nonsense_url),
        )
        # This slightly odd construction is necessary to create a Response object
        # that has the correct URL already baked in (I think), because otherwise we get the following
        # RuntimeError: Cannot call `raise_for_status` as the request instance has not been set on this response.
        return response

    monkeypatch.setattr(httpx, "get", mock_httpx_get)

    with pytest.raises(FileNotFoundError) as e:
        mappings.get_pipeline_catalog(
            url=nonsense_url, path=tmp_path / "does_not_exist.json"
        )

    assert "Have you correctly initialized the submodules" in str(e.value)


def test_get_pipeline_from_remote_succeeds(monkeypatch):
    nonsense_url = "https://made.up.url/pipeline_catalog.json"
    mock_pipeline_catalog = [
        {"name": "sillypipe", "versions": ["1", "2"]},
        {"name": "funpipe", "versions": ["10", "11"]},
    ]

    def mock_httpx_get(*args, **kwargs):
        response = httpx.Response(
            status_code=200,
            json=mock_pipeline_catalog,
            request=httpx.Request("GET", nonsense_url),
        )
        # This slightly odd construction is necessary to create a Response object
        # that has the correct URL already baked in (I think), because otherwise we get the following
        # RuntimeError: Cannot call `raise_for_status` as the request instance has not been set on this response.
        return response

    monkeypatch.setattr(httpx, "get", mock_httpx_get)

    result = mappings.get_pipeline_catalog(
        url=nonsense_url, path=mappings.PROCESSING_PIPELINE_PATH
    )

    assert result == mock_pipeline_catalog


def test_pipeline_uris_are_loaded():
    """Test that pipeline URIs are loaded from the pipeline-catalog submodule."""

    uri_dict, _ = mappings.parse_pipeline_catalog()
    assert all(
        ((mappings.NP.pf in pipe_uri) and (" " not in pipe_uri))
        for pipe_uri in uri_dict.values()
    )


def test_pipeline_versions_are_loaded():
    """Test that pipeline versions are loaded from the pipeline-catalog submodule."""

    _, version_dict = mappings.parse_pipeline_catalog()
    assert all(
        isinstance(pipe_versions, list) and len(pipe_versions) > 0
        for pipe_versions in version_dict.values()
    )


def test_warning_raised_when_some_pipeline_names_unrecognized():
    """
    Test that when a subset of pipeline names are not found in the pipeline catalog,
    an informative warning is raised but the recognized pipeline names are successfully returned.
    """
    pipelines = ["fmriprep", "fakepipeline1"]

    with pytest.warns(UserWarning) as w:
        recognized_pipelines = derivative_utils.get_recognized_pipelines(
            pipelines
        )

    assert all(
        substr in str(w[0].message.args[0])
        for substr in ["unrecognized pipelines", "fakepipeline1"]
    )
    assert recognized_pipelines == ["fmriprep"]


def test_error_raised_when_no_pipeline_names_recognized():
    """
    Test that when no provided pipeline names are found in the pipeline catalog,
    an informative error is raised.
    """
    pipelines = ["fakepipeline1", "fakepipeline2"]

    with pytest.raises(LookupError) as e:
        derivative_utils.get_recognized_pipelines(pipelines)

    assert "no recognized pipelines" in str(e.value)


@pytest.mark.parametrize(
    "fmriprep_versions, expctd_recog_versions, expctd_unrecog_versions",
    [
        (["20.2.7", "vA.B"], ["20.2.7"], ["vA.B"]),
        (["C.D.E", "F.G.H"], [], ["C.D.E", "F.G.H"]),
    ],
)
def test_pipeline_versions_classified_correctly(
    fmriprep_versions, expctd_recog_versions, expctd_unrecog_versions
):
    """Test that versions of a pipeline are correctly classified as recognized or unrecognized according to the pipeline catalog."""
    recog_versions, unrecog_versions = (
        derivative_utils.validate_pipeline_versions(
            "fmriprep", fmriprep_versions
        )
    )
    # The order of the versions in the lists is not guaranteed
    assert set(recog_versions) == set(expctd_recog_versions)
    assert set(unrecog_versions) == set(expctd_unrecog_versions)


def test_create_completed_pipelines():
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
        example_ses_proc_df
    )

    assert len(completed_pipelines) == 1
    assert (
        completed_pipelines[0].hasPipelineName.identifier
        == f"{mappings.NP.pf}:fmriprep"
    )
    assert completed_pipelines[0].hasPipelineVersion == "23.1.3"
