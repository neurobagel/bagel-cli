import pytest
from typer.testing import CliRunner

from bagelbids.cli import bagel


@pytest.fixture
def runner():
    return CliRunner()


def test_cli_can_be_invoked(runner, tmp_path):
    dir_p = tmp_path
    demo_p = dir_p / "demo.tsv"
    dict_p = dir_p / "dict.json"
    demo_p.touch()
    dict_p.touch()

    result = runner.invoke(bagel, ["--pheno", demo_p, "--dictionary", dict_p, "--output", dir_p])
    assert result.exit_code == 0
