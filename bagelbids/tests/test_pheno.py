import json

import pytest
import pandas as pd

from bagelbids.cli import are_inputs_compatible


@pytest.mark.parametrize("example,is_valid", [
    ("example1", True),
    ("example2", True),
    ("example3", True),
    ("example4", True),
    ("example5", True),
    ("example6", True),
    ("example7", False),
])
def test_validate_input(test_data, example, is_valid):
    """Assures that two individually valid input files also make sense together"""
    pheno = pd.read_csv(test_data / f"{example}.tsv", sep="\t")
    with open(test_data / f"{example}.json", "r") as f:
        data_dict = json.load(f)

    result = are_inputs_compatible(data_dict=data_dict, pheno_df=pheno)
    assert result == is_valid
