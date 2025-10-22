import pytest

from bagel.cli import bagel


@pytest.mark.parametrize(
    "command",
    ["bids2tsv", "pheno", "derivatives", "bids"],
)
@pytest.mark.parametrize(
    "help_flag",
    ["--help", "-h"],
)
def test_help_option_override_printed_in_command_help(
    runner, command, help_flag, caplog, disable_rich_markup
):
    """Test that a help option is still displayed in the help text for commands that override the default help option."""
    result = runner.invoke(bagel, [command, help_flag])
    assert result.exit_code == 0
    assert len(caplog.records) == 0
    assert "Show this message and exit" in result.output


@pytest.mark.parametrize(
    "command",
    ["bids2tsv", "pheno", "derivatives", "bids"],
)
def test_help_printed_if_no_args(runner, command, caplog, disable_rich_markup):
    """Test that the command help is printed if no arguments are provided."""
    result = runner.invoke(bagel, [command])
    assert result.exit_code == 0
    assert len(caplog.records) == 0
    assert f"{command} [OPTIONS]" in result.output
