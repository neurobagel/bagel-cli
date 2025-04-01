import json
import logging
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from bagel.logger import logger


@pytest.fixture(scope="session")
def runner():
    return CliRunner()


@pytest.fixture(scope="function")
def propagate_logs(monkeypatch):
    """Ensure that Pytest captures the logs from the CLI."""
    monkeypatch.setattr(logger, "propagate", True)


@pytest.fixture(scope="function")
def propagate_warnings(propagate_logs, caplog):
    """Only capture WARNING logs and above from the CLI."""
    caplog.set_level(logging.WARNING)


@pytest.fixture(scope="function")
def propagate_info(propagate_logs, caplog):
    """Only capture INFO logs and above from the CLI."""
    caplog.set_level(logging.INFO)


@pytest.fixture(scope="function")
def propagate_errors(propagate_logs, caplog):
    """Only capture ERROR logs and above from the CLI."""
    caplog.set_level(logging.ERROR)


@pytest.fixture(scope="session")
def bids_path(tmp_path_factory):
    return Path(__file__).absolute().parent / "bids-examples"


@pytest.fixture(scope="session")
def bids_synthetic(bids_path):
    return bids_path / "synthetic"


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
