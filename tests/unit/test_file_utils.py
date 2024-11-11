import pytest
import typer

from bagel.utilities import file_utils


@pytest.mark.parametrize(
    "unreadable_json,expected_message",
    [
        ("example_iso88591.json", "Failed to decode the input file"),
        ("example_invalid_json.json", "not valid JSON"),
    ],
)
def test_failed_json_reading_raises_informative_error(
    test_data, unreadable_json, expected_message, capsys
):
    """Test that when there is an issue reading an input JSON file, the CLI exits with an informative error message."""
    with pytest.raises(typer.Exit):
        file_utils.load_json(test_data / unreadable_json)
    captured = capsys.readouterr()

    assert expected_message in captured.err


def test_unsupported_tsv_encoding_raises_informative_error(test_data, capsys):
    """Test that given an input phenotypic TSV with an unsupported encoding, the CLI exits with an informative error message."""
    with pytest.raises(typer.Exit):
        file_utils.load_tabular(test_data / "example_iso88591.tsv")
    captured = capsys.readouterr()

    assert "Failed to decode the input file" in captured.err
