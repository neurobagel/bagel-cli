import json
import logging
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from bagel.cli import bagel


@pytest.fixture(scope="session")
def runner():
    return CliRunner()


@pytest.fixture(scope="function")
def disable_rich_markup(monkeypatch):
    """Disable rich markup for the CLI to assert over messages with formatting stripped."""
    monkeypatch.setattr(bagel, "rich_markup_mode", None)


# TODO: Revisit these fixtures - it seems it's safer to explicitly define the logger name because the CLI uses a named logger ("bagel.logger").
# When the logger name is unset, there can be weird behaviour where caplog will only capture logs from the root logger for certain test modules
# (maybe due to import order?), depending on how pytest is run (e.g., on a specific test file or all tests).
@pytest.fixture(scope="function")
def propagate_warnings(caplog):
    """Only capture WARNING logs and above from the CLI."""
    caplog.set_level(logging.WARNING, logger="bagel.logger")


@pytest.fixture(scope="function")
def propagate_info(caplog):
    """Only capture INFO logs and above from the CLI."""
    caplog.set_level(logging.INFO, logger="bagel.logger")


@pytest.fixture(scope="function")
def propagate_errors(caplog):
    """Only capture ERROR logs and above from the CLI."""
    caplog.set_level(logging.ERROR, logger="bagel.logger")


@pytest.fixture(scope="session")
def neurobagel_test_config():
    """Set the configuration for data dictionaries in the tests."""
    return "Neurobagel"


@pytest.fixture(scope="session")
def bids_path(tmp_path_factory):
    return Path(__file__).absolute().parent / "bids-examples"


@pytest.fixture(scope="session")
def bids_synthetic(bids_path):
    return bids_path / "synthetic"


@pytest.fixture(scope="session")
def tests_base_path():
    return Path(__file__).absolute().parent


@pytest.fixture(scope="session")
def test_data():
    return Path(__file__).absolute().parent / "data"


@pytest.fixture(scope="session")
def neurobagel_examples_path(tmp_path_factory):
    return Path(__file__).absolute().parent / "neurobagel_examples"


@pytest.fixture(scope="session")
def test_data_upload_path(neurobagel_examples_path):
    return neurobagel_examples_path / "data-upload"


@pytest.fixture(scope="session")
def example_dataset_description(test_data_upload_path):
    return test_data_upload_path / "synthetic_dataset_description.json"


@pytest.fixture(scope="session")
def load_test_json():
    def _read_file(file_path):
        with open(file_path, "r") as f:
            return json.load(f)

    return _read_file


@pytest.fixture(scope="session")
def bids_invalid_synthetic(bids_path, bids_synthetic, tmp_path_factory):
    invalid_path = tmp_path_factory.mktemp("tmp_bids") / "synthetic_invalid"
    # We make a copy of the valid BIDS dataset and delete a required file to make it invalid
    shutil.copytree(bids_synthetic, invalid_path)
    (invalid_path / "dataset_description.json").unlink()
    return invalid_path


@pytest.fixture()
def temp_output_jsonld_path(tmp_path):
    """Return temporary output JSONLD file path for tests of CLI commands."""
    return tmp_path / "output.jsonld"
