import json
from pathlib import Path

import pandas as pd
import typer


def file_encoding_error_message(input_p: Path) -> str:
    """Return a message for when a file cannot be read due to encoding issues."""
    return typer.style(
        f"Failed to decode the input file {input_p}. "
        "Please ensure that both your phenotypic .tsv file and .json data dictionary have UTF-8 encoding.\n"
        "Tip: Need help converting your file? Try a tool like iconv (http://linux.die.net/man/1/iconv) or https://www.freeformatter.com/convert-file-encoding.html.",
        fg=typer.colors.RED,
    )


def load_tabular(
    input_p: Path, input_type: str = "phenotypic"
) -> pd.DataFrame | None:
    """Load a .tsv pheno file and do some basic validation."""
    if input_p.suffix == ".tsv":
        try:
            tabular_df = pd.read_csv(
                input_p,
                sep="\t",
                keep_default_na=False,
                dtype=str,
                encoding="utf-8",
            )
        except UnicodeDecodeError as e:
            # TODO: Refactor once https://github.com/neurobagel/bagel-cli/issues/218 is addressed
            typer.echo(
                file_encoding_error_message(input_p),
                err=True,
            )
            raise typer.Exit(code=1) from e

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
        raise ValueError(
            f"Your {input_type} input file {input_p} has only one column "
            f"and is therefore not valid as a Neurobagel {input_type} file. "
            f" Please provide a valid .tsv {input_type} file!"
            f"\n\n{note_misnamed_csv if len(tabular_df.columns[0].split(',')) > 1 else ''}"
        )

    raise ValueError(
        f"Your ({input_p}) is not a .tsv file."
        f" Please provide a valid .tsv {input_type} file!"
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


def get_subjects_missing_from_pheno_data(
    subjects: list, pheno_subjects: list
) -> list:
    """Raises informative error if subject IDs exist that are found only in the BIDS directory."""
    return list(set(subjects).difference(pheno_subjects))
