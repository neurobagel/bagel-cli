import json
from pathlib import Path
from typing import Any

import httpx
import pandas as pd
import typer

from ..logger import log_error, logger


def file_encoding_error_message(input_p: Path) -> str:
    """Return a message for when a file cannot be read due to encoding issues."""
    return (
        f"Failed to decode the input file {input_p}. "
        "Please ensure that both your phenotypic .tsv file and .json data dictionary have UTF-8 encoding.\n"
        "Tip: Need help converting your file? Try a tool like iconv (http://linux.die.net/man/1/iconv) or https://www.freeformatter.com/convert-file-encoding.html."
    )


# TODO: Consider adding a function parameter to allow enabling `keep_default_na`.
# For some tables the CLI reads (e.g., BIDS tables), parsing empty strings as NaN is useful
# and saves us from needing additional custom string validation to catch empty cells.
# See https://github.com/neurobagel/bagel-cli/issues/505
def load_tabular(
    input_p: Path, input_type: str = "phenotypic"
) -> pd.DataFrame:
    """Load a .tsv pheno file and do some basic validation of the file type."""
    if input_p.suffix == ".tsv":
        try:
            tabular_df = pd.read_csv(
                input_p,
                sep="\t",
                keep_default_na=False,
                dtype=str,
                encoding="utf-8",
            )
        except UnicodeDecodeError:
            log_error(
                logger,
                file_encoding_error_message(input_p),
            )

        if tabular_df.shape[1] > 1:
            return tabular_df

        # If we have only one column, but splitting by ',' gives us several elements
        # then there is a good chance the user accidentally renamed a .csv into .tsv
        # and we should give them some extra info with our error message to fix this.
        note_misnamed_csv = (
            f"Note that your {input_type} input file also looks like a .csv file "
            "as it contains several ',' commas. It is possible that "
            "you have accidentally renamed a .csv file as a .tsv."
        )
        log_error(
            logger,
            f"Your {input_type} input file {input_p} has only one column "
            f"and is therefore not valid as a Neurobagel {input_type} file. "
            f"Please provide a valid .tsv {input_type} file!"
            f"\n{note_misnamed_csv if len(tabular_df.columns[0].split(',')) > 1 else ''}",
        )

    log_error(
        logger,
        f"Your ({input_p}) is not a .tsv file. "
        f"Please provide a valid .tsv {input_type} file!",
    )


def load_json(input_p: Path) -> Any:
    """Load a user-specified json type file."""
    try:
        with open(input_p, "r", encoding="utf-8") as f:
            return json.load(f)
    except UnicodeDecodeError:
        log_error(
            logger,
            file_encoding_error_message(input_p),
        )
    except json.JSONDecodeError:
        log_error(
            logger,
            f"The provided file is not valid JSON: {input_p}. Please provide a valid JSON file.",
        )


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
    with open(filename, "w") as f:
        f.write(json.dumps(data, indent=2))
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
            # We don't use file_utils.load_json() here because we don't want to throw an error yet if there are problems with the file.
            # Otherwise, since this function is called to populate global constants in mappings.py, there may be exceptions on import,
            # meaning there will be errors even if the user runs just bagel --help.
            with open(backup_path, "r", encoding="utf-8") as f:
                contents = json.load(f)
                err = str(request_err)
        except Exception as load_err:
            err = str(load_err)

    return contents, err
