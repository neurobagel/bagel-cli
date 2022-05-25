from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def bids_synthetic():
    bids_examples = Path(__file__).absolute().parent / "data"
    return bids_examples / "synthetic"
