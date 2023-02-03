from pathlib import Path

import typer

bagel = typer.Typer()


@bagel.command()
def pheno(
        pheno: Path = typer.Option(..., help="The path to a demographic .tsv file.",
                                   exists=True, file_okay=True, dir_okay=False),
        dictionary: Path = typer.Option(..., help="The path to the .json data dictionary "
                                                  "corresponding to the demographic .tsv file.",
                                        exists=True, file_okay=True, dir_okay=False),
        output: Path = typer.Option(..., help="The directory where outputs should be created",
                                    exists=True, file_okay=False, dir_okay=True)
):
    pass
