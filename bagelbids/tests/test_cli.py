import pytest
from typer.testing import CliRunner

from bagelbids.cli import bagel


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
