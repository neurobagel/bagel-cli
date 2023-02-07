import json

import pytest

from bagelbids.cli import is_valid_data_dictionary


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
