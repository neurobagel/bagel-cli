import json
from pathlib import Path
from typing import Any

import httpx
import pandas as pd
import typer

from ..logger import logger
from .exceptions import BagelFileError


def file_encoding_error_message(input_p: Path) -> str:
    """Return a message for when a file cannot be read due to encoding issues."""
    return (
        f"Failed to read {input_p} due to a character encoding error. "
        "Please ensure all input files are UTF-8 encoded. "
        "[italic]TIP: Need help converting your file? Try iconv (http://linux.die.net/man/1/iconv) or https://www.freeformatter.com/convert-file-encoding.html.[/italic]"
    )


# TODO: Consider adding a function parameter to allow enabling `keep_default_na`.
# For some tables the CLI reads (e.g., BIDS tables), parsing empty strings as NaN is useful
# and saves us from needing additional custom string validation to catch empty cells.
# See https://github.com/neurobagel/bagel-cli/issues/505
def load_tabular(
    input_p: Path, input_type: str = "phenotypic"
) -> pd.DataFrame:
    """Load a .tsv file and do some basic validation of the file type."""
    if input_p.suffix != ".tsv":
        raise BagelFileError(
            f"{input_p} does not have a .tsv extension. Please provide a valid TSV file.",
        )

    try:
        tabular_df = pd.read_csv(
            input_p,
            sep="\t",
            keep_default_na=False,
            dtype=str,
            encoding="utf-8",
        )
    except UnicodeDecodeError as exc:
        raise BagelFileError(file_encoding_error_message(input_p)) from exc

    if tabular_df.shape[1] == 1:
        # If we have only one column, but splitting by ',' gives us several elements
        # then there is a good chance the user accidentally renamed a .csv into .tsv
        # and we should give them some extra info with our error message to fix this.
        looks_like_csv = len(tabular_df.columns[0].split(",")) > 1
        misnamed_csv_note = (
            "[italic]NOTE: Your table resembles a .csv file "
            "as it contains several ',' commas. Check that you have not "
            "accidentally renamed a .csv file to a .tsv.[/italic]"
            if looks_like_csv
            else ""
        )
        raise BagelFileError(
            f"{input_p} is not a valid Neurobagel {input_type} table (.tsv). "
            "This file is expected to have multiple columns but only one column was found. "
            f"\n{misnamed_csv_note}",
        )

    return tabular_df


def load_json(input_p: Path) -> Any:
    """Load a user-specified json type file."""
    try:
        with open(input_p, "r", encoding="utf-8") as f:
            return json.load(f)
    except UnicodeDecodeError as exc:
        raise BagelFileError(file_encoding_error_message(input_p)) from exc
    except json.JSONDecodeError as exc:
        raise BagelFileError(
            f"{input_p} is not valid JSON. Please provide a valid JSON file."
        ) from exc


def check_overwrite(output: Path, overwrite: bool):
    """Exit program gracefully if an output file already exists but --overwrite has not been set."""
    if output.exists() and not overwrite:
        raise typer.Exit(
            typer.style(
                f"Output file {output} already exists. Use --overwrite or -f to overwrite.",
                fg=typer.colors.RED,
            )
        )


def save_jsonld(data: dict, filename: Path):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(json.dumps(data, indent=2, ensure_ascii=False))
    logger.info(f"Saved output to:  {filename}")


def request_file(url: str, backup_path: Path) -> tuple[list, str | None]:
    contents = []
    err = None

    try:
        response = httpx.get(url)
        response.raise_for_status()
        contents = response.json()
    except (httpx.HTTPError, json.JSONDecodeError) as request_err:
        try:
            with open(backup_path, "r", encoding="utf-8") as f:
                contents = json.load(f)
                err = str(request_err)
        except Exception as load_err:
            # We don't want to raise an error here since this function is called to populate global constants in mappings.py
            # (needed to dynamically load configuration names for the help text of --config for 'bagel create')
            # and we want to avoid exceptions on import (so there aren't errors if the user runs just bagel --help)
            err = str(load_err)

    return contents, err
