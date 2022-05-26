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
