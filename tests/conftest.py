import json
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner


@pytest.fixture(scope="session")
def runner():
    return CliRunner()


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
