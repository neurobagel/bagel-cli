import json

import pytest
from typer.testing import CliRunner

from bagelbids.cli import bagel, is_valid_data_dictionary, load_json


@pytest.fixture
def runner():
    return CliRunner()


def test_cli_validates_dictionary(runner, tmp_path, test_data):
    dir_p = tmp_path
    demo_p = dir_p / "demo.tsv"
    dict_p = test_data / "example1.json"
    demo_p.touch()
    dict_p.touch()

    result = runner.invoke(bagel, ["--pheno", demo_p, "--dictionary", dict_p, "--output", dir_p])
    assert result.exit_code == 0, f"Errored out. STDOUT: {result.output}"


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
