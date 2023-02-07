from pathlib import Path
import json
import jsonschema

import typer
import pandas as pd

from bagelbids import dictionary_models


bagel = typer.Typer()

DICTIONARY_SCHEMA = dictionary_models.DataDictionary.schema()


def get_columns_about(data_dict: dict, concept: str) -> list:
    """
    Returns column names that have been annotated as "IsAbout" the desired concept.
    Parameters
    ----------
    data_dict: dict
        A valid Neurobagel annotated data dictionary must be provided.
    concept: str
        A (shorthand) IRI for a concept that a column can be "about"

    Returns
    list
        List of column names that are "about" the desired concept

    -------

    """
    return [col for col, annotations in data_dict.items()
            if annotations["Annotations"]["IsAbout"]["TermURL"] == concept]


def load_json(input_p: Path) -> dict:
    with open(input_p, "r") as f:
        return json.load(f)


def are_inputs_compatible(data_dict: dict, pheno_df: pd.DataFrame) -> bool:
    """
    Determines whether the provided data dictionary and phenotypic file make sense together
    """
    return all([key in pheno_df.columns for key in data_dict.keys()])


def validate_inputs(data_dict: dict, pheno_df: pd.DataFrame) -> None:
    """Determines whether input data are valid"""
    try:
        jsonschema.validate(data_dict, DICTIONARY_SCHEMA)
    except jsonschema.ValidationError as e:
        raise ValueError("The provided data dictionary is not a valid Neurobagel data dictionary. "
                         "Make sure that each annotated column contains an 'Annotations' key.") from e
    
    if not are_inputs_compatible(data_dict, pheno_df):
        raise LookupError("The provided data dictionary and phenotypic file are individually valid, "
                          "but are not compatible. Make sure that you selected the correct data "
                          "dictionary for your phenotyic file. Every column described in the data "
                          "dictionary has to have a corresponding column with the same name in the "
                          "phenotypic file")


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
    data_dictionary = load_json(dictionary)
    pheno_df = pd.read_csv(pheno, sep="\t")
    validate_inputs(data_dictionary, pheno_df)
