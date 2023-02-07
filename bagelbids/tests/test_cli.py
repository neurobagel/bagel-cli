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
