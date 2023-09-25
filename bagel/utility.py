import json
from pathlib import Path

import typer


def load_json(input_p: Path) -> dict:
    """Load a user-specified json type file."""
    with open(input_p, "r") as f:
        return json.load(f)


def check_overwrite(output: Path, overwrite: bool):
    """Exit program gracefully if an output file already exists but --overwrite has not been set."""
    if output.exists() and not overwrite:
        raise typer.Exit(
            typer.style(
                f"Output file {output} already exists. Use --overwrite to overwrite.",
                fg=typer.colors.RED,
            )
        )
