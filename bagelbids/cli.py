from pathlib import Path
import json
import jsonschema

import typer

from bagelbids import dictionary_models


bagel = typer.Typer()

DICTIONARY_SCHEMA = dictionary_models.DataDictionary.schema()


def load_json(data_dict_path: Path) -> dict:
    with open(data_dict_path, "r") as f:
        return json.load(f)


def are_inputs_compatible(data_dict: dict, pheno_df: pd.DataFrame) -> bool:
    """
    Determines whether the provided data dictionary and phenotypic file make sense together
    """
    return all([key in pheno_df.columns for key in data_dict.keys()])


def has_neurobagel_annotations(data_dict: dict) -> bool:
    """Determines whether a data dictionary contains Neurobagel specific "Annotations"."""
    return all([description.get("Annotations") is not None
                for col, description in data_dict.items()
                if not col == "@context"])


def is_valid_data_dictionary(data_dict: dict) -> bool:
    """
    Check if a data dictionary complies with the Neurobagel schema for data dictionaries
    Parameters
    ----------
    data_dict: dict
        A loaded data dictionary.
    """
    try:
        jsonschema.validate(data_dict, DICTIONARY_SCHEMA)
        return has_neurobagel_annotations(data_dict)
    except jsonschema.ValidationError:
        return False


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
    print(is_valid_data_dictionary(data_dictionary))
