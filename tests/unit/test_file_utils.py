import httpx
import pytest
import typer

from bagel import mappings
from bagel.utilities import file_utils


@pytest.mark.parametrize(
    "unreadable_json,expected_message",
    [
        ("example_iso88591.json", "Failed to decode the input file"),
        ("example_invalid_json.json", "not valid JSON"),
    ],
)
def test_failed_json_reading_raises_informative_error(
    test_data, unreadable_json, expected_message, caplog, propagate_errors
):
    """Test that when there is an issue reading an input JSON file, the CLI exits with an informative error message."""
    with pytest.raises(typer.Exit):
        file_utils.load_json(test_data / unreadable_json)

    assert expected_message in caplog.text


def test_unsupported_tsv_encoding_raises_informative_error(
    test_data, caplog, propagate_errors
):
    """Test that given an input phenotypic TSV with an unsupported encoding, the CLI exits with an informative error message."""
    with pytest.raises(typer.Exit):
        file_utils.load_tabular(test_data / "example_iso88591.tsv")

    assert "Failed to decode the input file" in caplog.text


@pytest.mark.parametrize(
    "backup_path",
    [
        mappings.PROCESSING_PIPELINE_PATH,
        mappings.CONFIG_NAMESPACES_PATH,
    ],
)
def test_load_backup_file_if_remote_fails(monkeypatch, backup_path):
    """
    Test that a requested resource file is loaded from the local backup if the remote location is unreachable.

    NOTE: This test will fail if a required submodule has not been correctly initialized.
    """
    nonsense_url = "https://does.not.exist.url"
    request_err = "Network unreachable"

    def mock_httpx_get(*args, **kwargs):
        raise httpx.ConnectError(request_err)

    monkeypatch.setattr(httpx, "get", mock_httpx_get)

    result, err = file_utils.request_file(
        url=nonsense_url, backup_path=backup_path
    )

    assert all(isinstance(item, dict) for item in result)
    assert request_err in err


def test_resource_empty_if_remote_and_local_file_fetching_fail(
    monkeypatch, tmp_path
):
    """
    If I cannot get the requested resource from both the remote location and the local backup,
    the resulting resource should be empty.
    """
    nonsense_url = "https://does.not.exist.url"

    def mock_httpx_get(*args, **kwargs):
        raise httpx.ConnectError("Network unreachable")

    monkeypatch.setattr(httpx, "get", mock_httpx_get)

    result, err = file_utils.request_file(
        url=nonsense_url, backup_path=tmp_path / "does_not_exist.json"
    )

    assert result == []
    assert err is not None
