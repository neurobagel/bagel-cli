import json

import pandas as pd
import pytest
from typer.testing import CliRunner

from bagelbids.cli import bagel, are_inputs_compatible


@pytest.fixture
def runner():
    return CliRunner()


def test_cli_can_run_pheno_subcommand(runner, test_data, tmp_path):
    """Basic smoke test for the "pheno" subcommand"""
    # TODO: when we have more than one subcommand, the CLI runner will have
    # to specify the subcommand - until then the CLI behaves as if there was no subcommand

    result = runner.invoke(bagel, ["--pheno", test_data / "example2.tsv",
                                   "--dictionary", test_data / "example2.json",
                                   "--output", tmp_path])
    assert result.exit_code == 0, f"Errored out. STDOUT: {result.output}"


def test_valid_but_incompatible_inputs_fails(runner, test_data, tmp_path):
    """Providing two individually valid files that are incompatible should be caught by validation"""
    with pytest.raises(LookupError) as val_error:
        result = runner.invoke(bagel, ["--pheno", test_data / "example7.tsv",
                                       "--dictionary", test_data / "example7.json",
                                       "--output", tmp_path],
                               catch_exceptions=False)

    assert "not compatible" in str(val_error.value)


def test_valid_but_non_neurobagel_dictionary_fails(runner, test_data, tmp_path):
    """A valid (BIDS) data dictionary without Neurobagel annotations should be caught by validation"""
    with pytest.raises(ValueError) as val_err:
        result = runner.invoke(bagel, ["--pheno", test_data / "example3.tsv",
                                       "--dictionary", test_data / "example3.json",
                                       "--output", tmp_path],
                               catch_exceptions=False)

    assert "data dictionary is not a valid Neurobagel data dictionary" in str(val_err.value)


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
