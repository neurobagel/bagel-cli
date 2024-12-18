from __future__ import annotations

import warnings
from collections import defaultdict
from typing import Optional, Union

import isodate
import jsonschema
import pandas as pd
import pydantic
from typer import BadParameter

from bagel import dictionary_models, mappings
from bagel.mappings import ALL_NAMESPACES, NB

DICTIONARY_SCHEMA = dictionary_models.DataDictionary.model_json_schema()

AGE_HEURISTICS = {
    "float": NB.pf + ":FromFloat",
    "int": NB.pf + ":FromInt",
    "euro": NB.pf + ":FromEuro",
    "bounded": NB.pf + ":FromBounded",
    "iso8601": NB.pf + ":FromISO8601",
}


def validate_portal_uri(portal: Optional[str]) -> Optional[str]:
    """Custom validation that portal is a valid HttpUrl"""
    # NOTE: We need Optional in the validation type below to account for --portal being an optional argument in the pheno command
    try:
        pydantic.TypeAdapter(Optional[pydantic.HttpUrl]).validate_python(
            portal
        )
    except pydantic.ValidationError as err:
        raise BadParameter(
            "Not a valid http or https URL: "
            f"{err.errors()[0]['msg']} \nPlease try again."
        ) from err

    return portal


def get_columns_about(data_dict: dict, concept: str) -> list:
    """
    Returns all column names that have been annotated as "IsAbout" the desired concept.
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
        for col, content in get_annotated_columns(data_dict)
        if content["Annotations"]["IsAbout"]["TermURL"] == concept
    ]


def get_annotated_columns(data_dict: dict) -> list[tuple[str, dict]]:
    """
    Return a list of all columns that have Neurobagel 'Annotations' in a data dictionary,
    where each column is represented as a tuple of the column name (dictionary key from the data dictionary) and
    properties (all dictionary contents from the data dictionary).
    """
    return [
        (col, content)
        for col, content in data_dict.items()
        if "Annotations" in content
    ]


def recursive_find_values_for_key(data: dict, target: str) -> list:
    """
    Recursively search for a key in a possibly nested dictionary and return a list of all values found for that key.

    TODO: This function currently only considers nested dicts, and would need to be expanded if Neurobagel
    data dictionaries grow to have controlled terms inside list objects.
    """
    target_values = []
    if isinstance(data, dict):
        for key, value in data.items():
            if key == target:
                target_values.append(value)
            else:
                target_values.extend(
                    recursive_find_values_for_key(data=value, target=target)
                )
    return target_values


def find_unrecognized_namespaces_and_term_urls(
    data_dict: dict,
) -> tuple[list, dict]:
    """
    From a provided data dictionary, find all term URLs that contain an unrecognized namespace prefix.
    Return a tuple of unrecognized prefixes and a dictionary of the offending column names and their unrecognized term URLs.
    """
    known_namespace_prefixes = [ns.pf for ns in ALL_NAMESPACES]
    unrecognized_prefixes = set()
    unrecognized_term_urls = {}

    for col, content in get_annotated_columns(data_dict):
        for col_term_url in recursive_find_values_for_key(
            content["Annotations"], "TermURL"
        ):
            prefix = col_term_url.split(":")[0]
            if prefix not in known_namespace_prefixes:
                unrecognized_prefixes.add(prefix)
                unrecognized_term_urls[col] = col_term_url

    # sort the prefixes for a predictable order in the error message
    return sorted(unrecognized_prefixes), unrecognized_term_urls


def map_categories_to_columns(data_dict: dict) -> dict:
    """
    Maps all pre-defined Neurobagel categories (e.g. "Sex") to a list containing all column names (if any) that
    have been linked to this category.

    Returns a dictionary where the keys are the Neurobagel categories and the values are lists of column names.
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

    Returns a dictionary where the keys are the assessment tool IRIs and the values are lists of column names.
    """
    out_dict = defaultdict(list)
    for col, content in get_annotated_columns(data_dict):
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
    if "Levels" in data_dict[column]["Annotations"]:
        return True
    return False


def map_cat_val_to_term(
    value: Union[str, int], column: str, data_dict: dict
) -> str:
    """Take a raw categorical value and return the controlled term it has been mapped to"""
    return data_dict[column]["Annotations"]["Levels"][value]["TermURL"]


def get_age_heuristic(column: str, data_dict: dict) -> str:
    return data_dict[column]["Annotations"]["Transformation"]["TermURL"]


def transform_age(value: str, heuristic: str) -> float:
    is_recognized_heuristic = True
    try:
        if heuristic in [
            AGE_HEURISTICS["float"],
            AGE_HEURISTICS["int"],
        ]:
            return float(value)
        if heuristic == AGE_HEURISTICS["euro"]:
            return float(value.replace(",", "."))
        if heuristic == AGE_HEURISTICS["bounded"]:
            return float(value.strip("+"))
        if heuristic == AGE_HEURISTICS["iso8601"]:
            if not value.startswith("P"):
                value = "P" + value
            duration = isodate.parse_duration(value)
            return float(duration.years + duration.months / 12)
        else:
            is_recognized_heuristic = False
    except (ValueError, isodate.isoerror.ISO8601Error) as e:
        raise ValueError(
            f"There was a problem with applying the age transformation: {heuristic}. Error: {str(e)}\n"
            f"Check that the transformation specified in the data dictionary ({heuristic}) is correct for the age values in your phenotypic file, "
            "and that you correctly annotated any missing values in your age column."
        ) from e
    if not is_recognized_heuristic:
        raise ValueError(
            f"The provided data dictionary contains an unrecognized age transformation: {heuristic}. "
            f"Ensure that the transformation TermURL is one of {list(AGE_HEURISTICS.values())}."
        )


def get_transformed_values(
    columns: list, row: pd.Series, data_dict: dict
) -> list:
    """Convert a list of raw phenotypic values to the corresponding controlled terms, from columns that have not been annotated as being about an assessment tool."""
    transf_vals = []
    for col in columns:
        value = row[col]
        if is_missing_value(value, col, data_dict):
            continue
        if is_column_categorical(col, data_dict):
            transf_vals.append(map_cat_val_to_term(value, col, data_dict))
        else:
            # TODO: replace with more flexible solution when we have more
            # continuous variables than just age
            transf_vals.append(
                transform_age(str(value), get_age_heuristic(col, data_dict))
            )

    return transf_vals


# TODO: Check all columns and then return list of offending columns' names
def categorical_cols_have_bids_levels(data_dict: dict) -> bool:
    for col, content in get_annotated_columns(data_dict):
        if (
            is_column_categorical(col, data_dict)
            and content.get("Levels") is None
        ):
            return False

    return True


def get_mismatched_categorical_levels(data_dict: dict) -> list:
    """
    Returns list of any categorical columns from a data dictionary that have different entries
    for the "Levels" key between the column's BIDS and Neurobagel annotations.
    """
    mismatched_cols = []
    for col, content in get_annotated_columns(data_dict):
        if is_column_categorical(col, data_dict):
            known_levels = list(
                content["Annotations"]["Levels"].keys()
            ) + content["Annotations"].get("MissingValues", [])
            if set(content.get("Levels", {}).keys()).difference(known_levels):
                mismatched_cols.append(col)

    return mismatched_cols


def are_any_available(columns: list, row: pd.Series, data_dict: dict) -> bool:
    """
    Checks that at least one of the values in the specified columns is not a missing value.
    This is mainly useful to determine the availability of an assessment tool
    """
    return any(
        not is_missing_value(value, column, data_dict)
        for column, value in row[columns].items()
    )


def are_inputs_compatible(data_dict: dict, pheno_df: pd.DataFrame) -> bool:
    """
    Determines whether the provided data dictionary and phenotypic file make sense together
    """
    return all(
        [
            col in pheno_df.columns
            for col, _ in get_annotated_columns(data_dict)
        ]
    )


def find_undefined_cat_col_values(
    data_dict: dict, pheno_df: pd.DataFrame
) -> dict:
    """
    Checks that all categorical column values have annotations. Returns a dictionary containing
    any categorical column names and specific column values not defined in the corresponding data
    dictionary entry.
    """
    all_undefined_values = {}
    for col, content in get_annotated_columns(data_dict):
        if is_column_categorical(col, data_dict):
            known_values = list(
                content["Annotations"]["Levels"].keys()
            ) + content["Annotations"].get("MissingValues", [])
            unknown_values = []
            for value in pheno_df[col].unique():
                if value not in known_values:
                    unknown_values.append(value)
            if unknown_values:
                all_undefined_values[col] = unknown_values

    return all_undefined_values


def find_unused_missing_values(
    data_dict: dict, pheno_df: pd.DataFrame
) -> dict:
    """
    Checks if missing values annotated in the data dictionary appear at least once in the phenotypic file.
    Returns a dictionary containing any column names and annotated missing values not found in the phenotypic
    file column.
    """
    all_unused_missing_vals = {}
    for col, content in get_annotated_columns(data_dict):
        unused_missing_vals = []
        for missing_val in content["Annotations"].get("MissingValues", []):
            if missing_val not in pheno_df[col].unique():
                unused_missing_vals.append(missing_val)
        if unused_missing_vals:
            all_unused_missing_vals[col] = unused_missing_vals

    return all_unused_missing_vals


def get_rows_with_empty_strings(df: pd.DataFrame, columns: list) -> list:
    """For specified columns, returns the indices of rows with empty strings"""
    # NOTE: Profile this section if things get slow, transforming "" -> nan and then
    # using .isna() will very likely be much faster
    empty_row = df[columns].eq("").any(axis=1)
    return list(empty_row[empty_row].index)


def validate_data_dict(data_dict: dict) -> None:
    try:
        jsonschema.validate(data_dict, DICTIONARY_SCHEMA)
    except jsonschema.ValidationError as e:
        # TODO: When *every* item in an input JSON is not schema valid,
        # jsonschema.validate will raise a ValidationError for only *one* item among them.
        # Weirdly, the item that is chosen can vary, possibly due to jsonschema internally processing/validating
        # items in an inconsistent order.
        # You can reproduce this by running `bagel pheno` on the example_invalid input pair.
        # This isn't necessarily a problem as the error will not be wrong, but if we care about
        # returning ALL invalid items, we may want to use something like a Draft7Validator instance instead.
        # NOTE: If the validation error occurs at the root level (i.e., the entire JSON object fails),
        # e.path may be empty. We have a backup descriptor "Entire document" for the offending item in this case.
        raise ValueError(
            "The provided data dictionary is not a valid Neurobagel data dictionary.\n"
            "Details:\n"
            f"Entry that failed validation: {e.path[-1] if e.path else 'Entire document'}\n"
            f"{e.message}\n"
            "Tip: Make sure that each annotated column contains an 'Annotations' key."
        ) from e

    if get_annotated_columns(data_dict) == []:
        raise LookupError(
            "The provided data dictionary must contain at least one column with Neurobagel annotations."
        )

    if (
        len(
            get_columns_about(
                data_dict, concept=mappings.NEUROBAGEL["participant"]
            )
        )
        == 0
    ):
        raise LookupError(
            "The provided data dictionary must contain at least one column annotated as being about participant ID."
        )

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
            "The provided data dictionary has more than one column about participant ID or session ID. "
            "Please make sure that only one column is annotated for participant and session IDs."
        )

    if (
        len(get_columns_about(data_dict, concept=mappings.NEUROBAGEL["sex"]))
        > 1
    ):
        warnings.warn(
            "The provided data dictionary indicates more than one column about sex. "
            "Neurobagel cannot resolve multiple sex values per subject-session, and so will only consider the first of these columns for sex data."
        )

    if (
        len(get_columns_about(data_dict, concept=mappings.NEUROBAGEL["age"]))
        > 1
    ):
        warnings.warn(
            "The provided data dictionary indicates more than one column about age. "
            "Neurobagel cannot resolve multiple sex values per subject-session, so will only consider the first of these columns for age data."
        )

    if not categorical_cols_have_bids_levels(data_dict):
        warnings.warn(
            "The data dictionary contains at least one column that looks categorical but lacks a BIDS 'Levels' attribute."
        )

    if mismatched_cols := get_mismatched_categorical_levels(data_dict):
        warnings.warn(
            f"The data dictionary contains columns with mismatched levels between the BIDS and Neurobagel annotations: {mismatched_cols}"
        )


def check_for_duplicate_ids(data_dict: dict, pheno_df: pd.DataFrame):
    """Raise an error if there are duplicate participant IDs or duplicate combinations of participant and session IDs, if both are present."""
    id_columns = get_columns_about(
        data_dict, concept=mappings.NEUROBAGEL["participant"]
    ) + get_columns_about(data_dict, concept=mappings.NEUROBAGEL["session"])
    if pheno_df.duplicated(subset=id_columns).any():
        raise LookupError(
            "The rows of the provided phenotypic file do not have unique combinations of participant and session IDs. "
            "Please ensure that each row uniquely identifies one participant or one participant-session (if a column describing session is present)."
        )


def validate_inputs(data_dict: dict, pheno_df: pd.DataFrame) -> None:
    """Determines whether input data are valid"""
    validate_data_dict(data_dict)

    if not are_inputs_compatible(data_dict, pheno_df):
        raise LookupError(
            "The provided data dictionary and phenotypic file are individually valid, "
            "but are not compatible. Make sure that you selected the correct data "
            "dictionary for your phenotypic file. Every column described in the data "
            "dictionary has to have a corresponding column with the same name in the "
            "phenotypic file"
        )

    check_for_duplicate_ids(data_dict, pheno_df)

    undefined_cat_col_values = find_undefined_cat_col_values(
        data_dict, pheno_df
    )
    if undefined_cat_col_values:
        raise LookupError(
            "Categorical column(s) in the phenotypic file have values not annotated in the data dictionary "
            f"(shown as <column_name>: [<undefined values>]): {undefined_cat_col_values}. "
            "Please check that the correct data dictionary has been selected or make sure to annotate the missing values."
        )

    unused_missing_values = find_unused_missing_values(data_dict, pheno_df)
    if unused_missing_values:
        warnings.warn(
            "The following values annotated as missing values in the data dictionary were not found "
            "in the corresponding phenotypic file column(s) (<column_name>: [<unused missing values>]): "
            f"{unused_missing_values}. If this is not intentional, please check your data dictionary "
            "and phenotypic file."
        )

    unrecognized_namespaces, unrecognized_term_urls = (
        find_unrecognized_namespaces_and_term_urls(data_dict)
    )
    if unrecognized_namespaces:
        raise LookupError(
            f"The provided data dictionary contains unrecognized vocabulary namespace prefixes: {unrecognized_namespaces}\n"
            f"The unrecognized vocabularies are used for terms in the following columns' annotations: {unrecognized_term_urls}\n"
            "Please ensure that the data dictionary only includes terms from Neurobagel recognized vocabularies. "
            "(For more info, see https://neurobagel.org/data_models/dictionaries/.)"
        )

    # TODO: see if we can save ourselves the call to map_categories_to_columns here.
    # We cannot do the call earlier in the CLI (because it might fail for data invalid dictionaries)
    # and we need to know the column mappings in order to do the subject and session validation
    column_map = map_categories_to_columns(data_dict)
    columns_about_ids = column_map.get("participant", []) + column_map.get(
        "session", []
    )
    if row_indices := get_rows_with_empty_strings(pheno_df, columns_about_ids):
        raise LookupError(
            "We have detected missing values in participant or session id columns. "
            "Please make sure that every row has a non-empty participant id (and session id where applicable). "
            f"We found missing values in the following rows (first row is zero): {row_indices}."
        )
