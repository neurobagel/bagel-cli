import json

import pytest
import pandas as pd

from bagelbids.cli import is_valid_data_dictionary, are_inputs_compatible


@pytest.mark.parametrize("input_p,is_valid", [
    ("example1.json", True),
    ("example2.json", True),
    ("example3.json", False),
    ("example4.json", True),
    ("example5.json", True),
    ("example_invalid.json", False)
])
def test_validates_data_dictionary(test_data, input_p, is_valid):
    """
    Detects whether the provided data dictionary is valid under the schema.
    Because the data dictionary schema is valid for BIDS data dictionaries without Neurobagel annotations,
    this also detects whether the data dictionary has the required Neurobagel annotations.
    """
    with open(test_data / input_p, "r") as f:
        data_dict = json.load(f)

    result = is_valid_data_dictionary(data_dict)
    assert result == is_valid


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
