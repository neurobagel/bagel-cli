from pathlib import Path
import shutil

import pytest


@pytest.fixture(scope="session")
def bids_path(tmp_path_factory):
    bids_examples = Path(__file__).absolute().parent / "data"
    bids_tmp_path = tmp_path_factory.mktemp("bids_examples") / "data"
    shutil.copytree(bids_examples, bids_tmp_path)
    return bids_tmp_path


@pytest.fixture(scope="session")
def bids_synthetic(bids_path):
    return bids_path / "synthetic"


@pytest.fixture(scope="session")
def bids_invalid_synthetic(bids_path, bids_synthetic):
    invalid_path = bids_path / "synthetic_invalid"
    # We make a copy of the valid BIDS dataset and delete a required file to make it invalid
    shutil.copytree(bids_synthetic, invalid_path)
    (invalid_path / "dataset_description.json").unlink()
    return invalid_path
