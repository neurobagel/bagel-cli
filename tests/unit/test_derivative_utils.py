import httpx
import pandas as pd
import pytest

from bagel import mappings
from bagel.utilities import derivative_utils


def test_get_pipeline_from_backup_if_remote_fails(monkeypatch):
    """
    Test that the pipeline catalog is loaded from the local backup if the remote location is unreachable.
    """
    # TODO: Make a proper mock for the requests.get function
    # or switch to httpx for better testing capabilities
    nonsense_url = "https://does.not.exist.url"

    def mock_httpx_get(*args, **kwargs):
        response = httpx.Response(status_code=400, json={"key": "value"})
        # This slightly odd construction is necessary to create a Response object
        # that has the correct URL already baked in (I think), because otherwise we get the following
        # RuntimeError: Cannot call `raise_for_status` as the request instance has not been set on this response.
        # TODO: find a better solution or understand the problem better
        response._request = httpx.Request("GET", nonsense_url)
        return response

    monkeypatch.setattr(httpx, "get", mock_httpx_get)

    with pytest.warns(UserWarning) as w:
        result = mappings.get_pipeline_catalog(
            url=nonsense_url, path=mappings.PROCESSING_PIPELINE_PATH
        )

    assert all(isinstance(item, dict) for item in result)
    assert "Unable to load pipeline catalog" in w[0].message.args[0]


def test_raises_exception_if_remote_and_local_pipeline_catalog_fails(
    monkeypatch, tmp_path
):
    """
    If I cannot get the pipeline catalog from the remote location and the local backup, I should raise an exception.
    """
    # or switch to httpx for better testing capabilities
    nonsense_url = "https://does.not.exist.url"

    def mock_httpx_get(*args, **kwargs):
        response = httpx.Response(status_code=400, json={"key": "value"})
        # This slightly odd construction is necessary to create a Response object
        # that has the correct URL already baked in (I think), because otherwise we get the following
        # RuntimeError: Cannot call `raise_for_status` as the request instance has not been set on this response.
        # TODO: find a better solution or understand the problem better
        response._request = httpx.Request("GET", nonsense_url)
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
        response = httpx.Response(status_code=200, json=mock_pipeline_catalog)
        # This slightly odd construction is necessary to create a Response object
        # that has the correct URL already baked in (I think), because otherwise we get the following
        # RuntimeError: Cannot call `raise_for_status` as the request instance has not been set on this response.
        # TODO: find a better solution or understand the problem better
        response._request = httpx.Request("GET", nonsense_url)
        return response

    monkeypatch.setattr(httpx, "get", mock_httpx_get)

    result = mappings.get_pipeline_catalog(
        url=nonsense_url, path=mappings.PROCESSING_PIPELINE_PATH
    )

    assert all(isinstance(item, dict) for item in result)
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


@pytest.mark.parametrize(
    "pipelines, unrecog_pipelines",
    [
        (["fmriprep", "pipeline1"], ["pipeline1"]),
        (["pipelineA", "pipelineB"], ["pipelineA", "pipelineB"]),
    ],
)
def test_unrecognized_pipeline_names_raise_error(pipelines, unrecog_pipelines):
    """Test that pipeline names not found in the pipeline catalog raise an informative error."""
    with pytest.raises(LookupError) as e:
        derivative_utils.check_pipelines_are_recognized(pipelines)

    assert all(
        substr in str(e.value)
        for substr in ["unrecognized pipelines"] + unrecog_pipelines
    )


@pytest.mark.parametrize(
    "fmriprep_versions, unrecog_versions",
    [
        (["20.2.7", "vA.B"], ["vA.B"]),
        (["C.D.E", "F.G.H"], ["C.D.E", "F.G.H"]),
    ],
)
def test_unrecognized_pipeline_versions_raise_error(
    fmriprep_versions, unrecog_versions
):
    """Test that versions of a pipeline not found in the pipeline catalog raise an informative error."""
    with pytest.raises(LookupError) as e:
        derivative_utils.check_pipeline_versions_are_recognized(
            "fmriprep", fmriprep_versions
        )

    assert all(
        substr in str(e.value)
        for substr in ["unrecognized fmriprep versions"] + unrecog_versions
    )


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
