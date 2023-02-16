import json
from collections import defaultdict
from pathlib import Path
from typing import Union

import isodate
import jsonschema
import pandas as pd
import typer

from bagelbids import dictionary_models, mappings, models

bagel = typer.Typer()

DICTIONARY_SCHEMA = dictionary_models.DataDictionary.schema()


def generate_context():
    # Direct copy of the dandi-schema context generation function
    # https://github.com/dandi/dandi-schema/blob/c616d87eaae8869770df0cb5405c24afdb9db096/dandischema/metadata.py
    import pydantic

    field_preamble = {
        "bg": "http://neurobagel.org/vocab/",
        "snomed": "https://identifiers.org/snomedct:",
        "nidm": "http://purl.org/nidash/nidm#",
    }
    fields = {}
    for val in dir(models):
        klass = getattr(models, val)
        if not isinstance(klass, pydantic.main.ModelMetaclass):
            continue
        fields[klass.__name__] = "bg:" + klass.__name__
        for name, field in klass.__fields__.items():
            if name == "schemaKey":
                fields[name] = "@type"
            elif name == "identifier":
                fields[name] = "@id"
            elif name not in fields:
                fields[name] = {"@id": "bg:" + name}

    field_preamble.update(**fields)

    return {"@context": field_preamble}


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
    return [
        col
        for col, annotations in data_dict.items()
        if annotations["Annotations"]["IsAbout"]["TermURL"] == concept
    ]


def map_categories_to_columns(data_dict: dict) -> dict:
    """
    Maps all pre-defined Neurobagel categories (e.g. "Sex") to a list of column names (if any) that
    have been linked to this category.
    """
    return {
        cat_name: get_columns_about(data_dict, cat_iri)
        for cat_name, cat_iri in mappings.NEUROBAGEL.items()
        if get_columns_about(data_dict, cat_iri)
    }


def map_tools_to_columns(data_dict: dict) -> dict:
    """
    Return a mapping of all assessment tools described in the data dictionary to the columns that
    are mapped to it.
    """
    out_dict = defaultdict(list)
    for col, content in data_dict.items():
        part_of = content["Annotations"].get("IsPartOf")
        if part_of is not None:
            out_dict[part_of.get("TermURL")].append(col)

    return out_dict


def is_missing_value(
    value: Union[str, int], column: str, data_dict: dict
) -> bool:
    """Determine if a raw value is listed as a missing value in the data dictionary entry for this column"""
    return value in data_dict[column]["Annotations"].get("MissingValues", [])


def is_column_categorical(column: str, data_dict: dict) -> bool:
    """Determine whether a column in a Neurobagel data dictionary is categorical"""
    if "Levels" in data_dict[column]:
        return True
    return False


def map_cat_val_to_term(
    value: Union[str, int], column: str, data_dict: dict
) -> str:
    """Take a raw categorical value and return the controlled term it has been mapped to"""
    return data_dict[column]["Annotations"]["Levels"][value]["TermURL"]


def get_age_heuristic(column: str, data_dict: dict) -> str:
    return data_dict[column]["Annotations"]["Transformation"]["TermURL"]


def transform_age(value: Union[int, float, str], heuristic: str) -> float:
    if heuristic == "bg:euro":
        return float(value.replace(",", "."))
    if heuristic == "bg:bounded":
        return float(value.strip("+"))
    if heuristic == "bg:range":
        a_min, a_max = value.split("-")
        return (float(a_min) + float(a_max)) / 2
    if heuristic == "bg:iso8601":
        if not value.startswith("P"):
            value = "P" + value
        duration = isodate.parse_duration(value)
        return float(duration.years + duration.months / 12)
    else:
        raise ValueError(
            "The provided data dictionary contains an unrecognized age transformation. "
            'Ensure that its TermURL is one of the "bg:euro", "bg:bounded", "bg:range", "bg:iso8601"].'
        )


def get_transformed_values(
    columns: list, row: pd.Series, data_dict: dict
) -> Union[str, None]:
    """Convert a raw phenotypic value to the corresponding controlled term"""
    transf_val = []
    # TODO: implement a way to handle cases where more than one column contains information
    for col in columns[:1]:
        value = row[col]
        if is_missing_value(value, col, data_dict):
            continue
        if is_column_categorical(col, data_dict):
            transf_val.append(map_cat_val_to_term(value, col, data_dict))
        else:
            # TODO: replace with more flexible solution when we have more
            # continuous variables than just age
            transf_val.append(
                transform_age(value, get_age_heuristic(col, data_dict))
            )

    # TODO: once we can handle multiple columns, this section should be removed
    # and we should just return an empty list if no transform can be generated
    if not transf_val:
        return None
    return transf_val[0]


def are_not_missing(columns: list, row: pd.Series, data_dict: dict) -> bool:
    """
    Checks that all values in the specified columns are not missing values. This is mainly useful
    to determine the availability of an assessment tool
    """
    return all(
        [
            not is_missing_value(value, column, data_dict)
            for column, value in row[columns].items()
        ]
    )


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
        raise ValueError(
            "The provided data dictionary is not a valid Neurobagel data dictionary. "
            "Make sure that each annotated column contains an 'Annotations' key."
        ) from e

    # TODO: remove this validation when we start handling multiple participant and / or session ID columns
    if (
        len(
            get_columns_about(
                data_dict, concept=mappings.NEUROBAGEL["participant"]
            )
        )
        > 1
    ) | (
        len(
            get_columns_about(
                data_dict, concept=mappings.NEUROBAGEL["session"]
            )
        )
        > 1
    ):
        raise ValueError(
            "The provided data dictionary has more than one column about participant ID or session ID."
            "Please make sure that only one column is annotated for participant and session IDs."
        )

    if not are_inputs_compatible(data_dict, pheno_df):
        raise LookupError(
            "The provided data dictionary and phenotypic file are individually valid, "
            "but are not compatible. Make sure that you selected the correct data "
            "dictionary for your phenotyic file. Every column described in the data "
            "dictionary has to have a corresponding column with the same name in the "
            "phenotypic file"
        )


@bagel.command()
def pheno(
    pheno: Path = typer.Option(
        ...,
        help="The path to a phenotypic .tsv file.",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    dictionary: Path = typer.Option(
        ...,
        help="The path to the .json data dictionary "
        "corresponding to the phenotypic .tsv file.",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    output: Path = typer.Option(
        ...,
        help="The directory where outputs should be created",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    name: str = typer.Option(
        ...,
        help="A descriptive name for the dataset the input belongs to. "
        "This name is expected to match the name field in the BIDS "
        "dataset_description.json file.",
    ),
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

    subject_list = []

    column_mapping = map_categories_to_columns(data_dictionary)
    tool_mapping = map_tools_to_columns(data_dictionary)

    # TODO: needs refactoring once we handle multiple participant IDs
    participants = column_mapping.get("participant")[0]

    for participant in pheno_df[participants].unique():
        # TODO: needs refactoring once we handle phenotypic information at the session level
        # for the moment we are not creating any session instances in the phenotypic graph
        # we treat the phenotypic information in the first row of the _sub_pheno dataframe
        # as reflecting the subject level phenotypic information
        _sub_pheno = pheno_df.query(
            f"{participants} == '{str(participant)}'"
        ).iloc[0]

        subject = models.Subject(label=str(participant))
        if "sex" in column_mapping.keys():
            subject.sex = get_transformed_values(
                column_mapping["sex"], _sub_pheno, data_dictionary
            )

        if "diagnosis" in column_mapping.keys():
            _dx_val = get_transformed_values(
                column_mapping["diagnosis"], _sub_pheno, data_dictionary
            )
            if _dx_val is None:
                pass
            elif _dx_val == mappings.NEUROBAGEL["healthy_control"]:
                subject.isSubjectGroup = mappings.NEUROBAGEL["healthy_control"]
            else:
                subject.diagnosis = [models.Diagnosis(identifier=_dx_val)]

        if "age" in column_mapping.keys():
            subject.age = get_transformed_values(
                column_mapping["age"], _sub_pheno, data_dictionary
            )

        if tool_mapping:
            _assessments = [
                models.Assessment(identifier=tool)
                for tool, columns in tool_mapping.items()
                if are_not_missing(columns, _sub_pheno, data_dictionary)
            ]
            if _assessments:
                # Only set assignments for the subject if at least one is not missing
                subject.assessment = _assessments

        subject_list.append(subject)

    dataset = models.Dataset(label=name, hasSamples=subject_list)
    context = generate_context()
    # We can't just exclude_unset here because the identifier and schemaKey
    # for each instance are created as default values and so technically are never set
    # TODO: we should revisit this because there may be reasons to have None be meaningful in the future
    context.update(**dataset.dict(exclude_none=True))

    with open(output / "pheno.jsonld", "w") as f:
        f.write(json.dumps(context, indent=2))
