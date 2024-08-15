import json
from pathlib import Path

import typer


def file_encoding_error_message(input_p: Path) -> str:
    """Return a message for when a file cannot be read due to encoding issues."""
    return typer.style(
        f"Failed to decode the input file {input_p}. "
        "Please ensure that both your phenotypic .tsv file and .json data dictionary have UTF-8 encoding.\n"
        "Tip: Need help converting your file? Try a tool like iconv (http://linux.die.net/man/1/iconv) or https://www.freeformatter.com/convert-file-encoding.html.",
        fg=typer.colors.RED,
    )


def load_json(input_p: Path) -> dict:
    """Load a user-specified json type file."""
    try:
        with open(input_p, "r", encoding="utf-8") as f:
            return json.load(f)
    except UnicodeDecodeError as e:
        # TODO: Refactor once https://github.com/neurobagel/bagel-cli/issues/218 is addressed
        typer.echo(
            file_encoding_error_message(input_p),
            err=True,
        )
        raise typer.Exit(code=1) from e
    except json.JSONDecodeError as e:
        typer.echo(
            typer.style(
                f"The provided data dictionary {input_p} is not valid JSON. "
                "Please provide a valid JSON file.",
                fg=typer.colors.RED,
            ),
            err=True,
        )
        raise typer.Exit(code=1) from e


def check_overwrite(output: Path, overwrite: bool):
    """Exit program gracefully if an output file already exists but --overwrite has not been set."""
    if output.exists() and not overwrite:
        raise typer.Exit(
            typer.style(
                f"Output file {output} already exists. Use --overwrite to overwrite.",
                fg=typer.colors.RED,
            )
        )
