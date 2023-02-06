from pathlib import Path

import typer

bagel = typer.Typer()


@bagel.command()
def pheno(
        pheno: Path = typer.Option(..., help="The path to a phenotypic .tsv file.",
                                   exists=True, file_okay=True, dir_okay=False),
        dictionary: Path = typer.Option(..., help="The path to the .json data dictionary "
                                                  "corresponding to the phenotypic .tsv file.",
                                        exists=True, file_okay=True, dir_okay=False),
        output: Path = typer.Option(..., help="The directory where outputs should be created",
                                    exists=True, file_okay=False, dir_okay=True)
):
    """
    Process a tabular phenotypic file (.tsv) that has been successfully annotated
    with the Neurobagel annotation tool. The annotations are expected to be stored
    in a data dictionary (.json).

    This tool will create a valid, subject-level instance of the Neurobagel
    graph datamodel for the provided phenotypic file in the .jsonld format.
    You can upload this .jsonld file to the Neurobagel graph.
    """
