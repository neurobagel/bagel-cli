import pytest
from typer.testing import CliRunner

from bagelbids.cli import bagel


@pytest.fixture
def runner():
    return CliRunner()


def test_cli_can_be_invoked(runner, test_data, tmp_path):

    result = runner.invoke(bagel, ["--pheno", test_data / "example2.tsv",
                                   "--dictionary", test_data / "example2.json",
                                   "--output", tmp_path])
    assert result.exit_code == 0
