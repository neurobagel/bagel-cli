from click.testing import CliRunner
from bagelbids.cli import main


def test_hello_world():
    runner = CliRunner()
    result = runner.invoke(main, ["Peter"])
    assert result.exit_code == 0
    assert result.output == "Bagels are good for you, Peter!\n"
