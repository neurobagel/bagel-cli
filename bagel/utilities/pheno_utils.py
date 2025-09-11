from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from typing import Optional, Union

import isodate
import jsonschema
import pandas as pd
import pydantic
from typer import BadParameter, CallbackParam

from bagel import dictionary_models, mappings
from bagel.logger import log_error, logger
from bagel.mappings import DEPRECATED_NAMESPACE_PREFIXES, NB

# TODO: Once we remove support for v1 annotation tool data dictionaries, revert to using this version for data dictionary schema validation
# DICTIONARY_SCHEMA = dictionary_models.DataDictionary.model_json_schema()

AGE_FORMATS = {
    "float": NB.pf + ":FromFloat",
    "int": NB.pf + ":FromInt",
    "euro": NB.pf + ":FromEuro",
    "bounded": NB.pf + ":FromBounded",
    "iso8601": NB.pf + ":FromISO8601",
    "range": NB.pf + ":FromRange",
}


def get_available_configs(config_namespaces_mapping: list) -> list:
    """Return the list of names of available community configurations."""
    return [config["config_name"] for config in config_namespaces_mapping]


def additional_config_help_text() -> str:
    """
    Construct a warning to be added in the help text for the --config option when no configurations are available.
    This is to inform the user explicitly in the rare case when no configurations are available, i.e. when fetching the remote file fails and there is no local backup found
    (if submodules were not properly initialized). In this case, allowed choices for --config would be shown as an empty list [],
    meaning even the default "Neurobagel" option would result in an invalid parameter error (and the `pheno` command cannot run).
    """
    if mappings.CONFIG_NAMESPACES_MAPPING == []:
        return (
            "[bold red]WARNING: Failed to locate any community configurations. "
            "Please check that you have an internet connection, or open an issue in https://github.com/neurobagel/bagel-cli/issues if the problem persists.[/bold red]"
        )
    return ""


def check_if_remote_config_namespaces_used():
    """Warn if the community configuration namespaces could not be fetched from the remote source."""
    if (
        mappings.CONFIG_NAMESPACES_FETCHING_ERR
        and mappings.CONFIG_NAMESPACES_MAPPING != []
    ):
        logger.warning(
            f"Failed to fetch configuration from {mappings.CONFIG_NAMESPACES_URL}. Error: {mappings.CONFIG_NAMESPACES_FETCHING_ERR}. "
            "Using a packaged backup configuration instead *which may be outdated*. "
            "Check your internet connection?"
        )


def get_supported_namespaces_for_config(config_name: str) -> dict:
    """Return a dictionary of supported namespace prefixes and their corresponding full URLs for a given community configuration."""
    config_namespaces = next(
        config["namespaces"]
        for config in mappings.CONFIG_NAMESPACES_MAPPING
        if config["config_name"] == config_name
    )

    config_namespaces_dict = {}
    for namespace_group in config_namespaces.values():
        for namespace in namespace_group:
            config_namespaces_dict[namespace["namespace_prefix"]] = namespace[
                "namespace_url"
            ]

    return config_namespaces_dict


def check_param_not_whitespace(param: CallbackParam, value: str) -> str:
    """Custom validation that the value for a string argument is not an empty string or just whitespace."""
    if value.isspace() or value == "":
        raise BadParameter(f"{param.name} cannot be an empty string.")
    return value


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


def find_unsupported_namespaces_and_term_urls(
    data_dict: dict,
    config: str,
) -> tuple[list, dict]:
    """
    From a provided data dictionary, find all term URLs that contain an unsupported namespace prefix.
    Return a tuple of unsupported prefixes and a dictionary of the offending column names and their unrecognized term URLs.
    """
    unsupported_prefixes = set()
    unrecognized_term_urls = {}

    supported_namespaces = get_supported_namespaces_for_config(config)

    for col, content in get_annotated_columns(data_dict):
        for col_term_url in recursive_find_values_for_key(
            content["Annotations"], "TermURL"
        ):
            prefix = col_term_url.split(":")[0]
            if prefix not in supported_namespaces:
                unsupported_prefixes.add(prefix)
                unrecognized_term_urls[col] = col_term_url

    # sort the prefixes for a predictable order in the error message
    return sorted(unsupported_prefixes), unrecognized_term_urls


def find_deprecated_namespaces(namespaces: list) -> list:
    """Return the deprecated vocabulary namespace prefixes found in a list of namespace prefixes."""
    return [ns for ns in namespaces if ns in DEPRECATED_NAMESPACE_PREFIXES]


def map_categories_to_columns(data_dict: dict) -> dict[str, list]:
    """
    Maps all pre-defined Neurobagel categories (e.g. "Sex") to a list containing all column names (if any) that
    have been linked to this category.

    Returns a dictionary where the keys are the aliases for Neurobagel categories and the values are lists of column names.
    """
    return {
        cat_name: get_columns_about(data_dict, cat_iri)
        for cat_name, cat_iri in mappings.NEUROBAGEL.items()
        if get_columns_about(data_dict, cat_iri)
    }


def map_tools_to_columns(data_dict: dict) -> dict[str, list]:
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
    column_annotation = data_dict[column]["Annotations"]

    try:
        dictionary_models.CategoricalNeurobagel.model_validate(
            column_annotation
        )
        return True
    except pydantic.ValidationError:
        return False


def map_cat_val_to_term(
    value: Union[str, int], column: str, data_dict: dict
) -> str:
    """Take a raw categorical value and return the controlled term it has been mapped to"""
    return data_dict[column]["Annotations"]["Levels"][value]["TermURL"]


def get_age_format(column: str, data_dict: dict) -> str:
    return data_dict[column]["Annotations"]["Format"]["TermURL"]


def transform_age(value: str, value_format: str) -> float:
    try:
        if value_format in [
            AGE_FORMATS["float"],
            AGE_FORMATS["int"],
        ]:
            return float(value)
        if value_format == AGE_FORMATS["euro"]:
            return float(value.replace(",", "."))
        if value_format == AGE_FORMATS["bounded"]:
            return float(value.strip("+"))
        if value_format == AGE_FORMATS["iso8601"]:
            if not value.startswith("P"):
                pvalue = "P" + value
            else:
                pvalue = value
            duration = isodate.parse_duration(pvalue)
            return float(duration.years + duration.months / 12)
        if value_format == AGE_FORMATS["range"]:
            a_min, a_max = value.split("-")
            return sum(map(float, [a_min, a_max])) / 2
        log_error(
            logger,
            f"The data dictionary contains an unrecognized age format: {value_format}. "
            f"Ensure that the format TermURL is one of {list(AGE_FORMATS.values())}.",
        )
    except (ValueError, isodate.isoerror.ISO8601Error) as e:
        log_error(
            logger,
            f"Error applying the format {value_format} to the age value: {value}. Error: {e}\n"
            f"Check your data dictionary to ensure that the annotated age format matches the age values in your phenotypic table, "
            "and that any missing values in your age column have been correctly annotated. "
            "For examples of acceptable values for specific age formats, see https://neurobagel.org/data_models/dictionaries/#age.",
        )


def get_transformed_values(
    columns: list, row: pd.Series, data_dict: dict
) -> list:
    """Convert a list of raw phenotypic values to the corresponding controlled terms, from columns that have not been annotated as being about an assessment tool."""
    transf_vals: list[float | str] = []
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
                transform_age(str(value), get_age_format(col, data_dict))
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


def find_missing_annotated_cols(
    data_dict: dict, pheno_df: pd.DataFrame
) -> list:
    """
    Find columns that are annotated in the data dictionary but not present in the phenotypic file.
    """
    missing_annotated_cols = []
    for col, _ in get_annotated_columns(data_dict):
        if col not in pheno_df.columns:
            missing_annotated_cols.append(col)

    return missing_annotated_cols


def find_undefined_cat_col_values(
    data_dict: dict, pheno_df: pd.DataFrame
) -> dict[str, list]:
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
) -> dict[str, list]:
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
    # Return the row index as it would look in a spreadsheet program, 1-based and including the header
    return [idx + 2 for idx in empty_row[empty_row].index]


def construct_dictionary_schema_for_validation() -> dict:
    """
    For backwards compatibility with the v1 annotation tool, we patch the data dictionary schema
    to allow for either a 'Format' or 'Transformation' key (but not both) for continuous columns.
    This ensures that v1 annotation tool data dictionaries still pass the initial schema validation (for now),
    without encoding the 'Transformation' key in the updated data dictionary model itself.

    TODO: Remove once we no longer support data dictionaries annotated using annotation tool v1.
    """
    patched_schema = deepcopy(
        dictionary_models.DataDictionary.model_json_schema()
    )
    continuous_schema = patched_schema["$defs"]["ContinuousNeurobagel"]
    continuous_schema["properties"]["Transformation"] = deepcopy(
        continuous_schema["properties"]["Format"]
    )
    if "Format" in continuous_schema.get("required", []):
        continuous_schema["required"].remove("Format")
    continuous_schema["oneOf"] = [
        {"required": ["Transformation"], "not": {"required": ["Format"]}},
        {"required": ["Format"], "not": {"required": ["Transformation"]}},
    ]
    return patched_schema


def validate_data_dict(data_dict: dict, config: str) -> None:
    try:
        jsonschema.validate(
            data_dict, construct_dictionary_schema_for_validation()
        )
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
        log_error(
            logger,
            "The data dictionary is not a valid Neurobagel data dictionary. "
            f"Entry that failed validation: {e.path[-1] if e.path else 'Entire document'}\n"
            f"Details: {e.message}\n"
            "[italic]TIP: Ensure each annotated column contains an 'Annotations' key.[/italic]",
        )

    if get_annotated_columns(data_dict) == []:
        log_error(
            logger,
            "The data dictionary must contain at least one column with Neurobagel annotations.",
        )

    unsupported_namespaces, unrecognized_term_urls = (
        find_unsupported_namespaces_and_term_urls(data_dict, config)
    )
    if unsupported_namespaces:
        namespace_deprecation_msg = ""
        if config == mappings.DEFAULT_CONFIG:
            if deprecated_namespaces := find_deprecated_namespaces(
                unsupported_namespaces
            ):
                namespace_deprecation_msg = (
                    f"\n\nMore info: The following vocabularies have been deprecated by Neurobagel: {deprecated_namespaces}. "
                    "Please update your data dictionary using the latest version of the annotation tool at https://annotate.neurobagel.org."
                )
        log_error(
            logger,
            f"The data dictionary contains unsupported vocabulary namespace prefixes: {unsupported_namespaces}\n"
            f"Unsupported vocabularies are used for terms in the following columns' annotations: {unrecognized_term_urls}\n"
            f"Please ensure the data dictionary only includes terms from vocabularies recognized by {config}. "
            f"{namespace_deprecation_msg}",
        )

    if (
        len(
            get_columns_about(
                data_dict, concept=mappings.NEUROBAGEL["participant"]
            )
        )
        == 0
    ):
        log_error(
            logger,
            "The data dictionary must contain at least one column annotated as being about participant ID.",
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
        log_error(
            logger,
            "The data dictionary has more than one column about participant ID or session ID. "
            "Please ensure only one column is annotated for participant and session IDs.",
        )

    if (
        set(map_categories_to_columns(data_dict).keys())
        == {"participant", "session"}
    ) or (set(map_categories_to_columns(data_dict).keys()) == {"participant"}):
        logger.warning(
            "The only columns annotated in the data dictionary are participant ID or session ID columns. "
            "As a result, the generated graph-ready data will not contain any subject phenotypic characteristics. "
            "Check that all relevant phenotypic columns in your data table have been annotated."
        )

    if (
        len(get_columns_about(data_dict, concept=mappings.NEUROBAGEL["sex"]))
        > 1
    ):
        logger.warning(
            "The data dictionary indicates more than one column about sex. "
            "Neurobagel cannot resolve multiple sex values per subject-session, and so will only consider the first identified column for sex data."
        )

    if (
        len(get_columns_about(data_dict, concept=mappings.NEUROBAGEL["age"]))
        > 1
    ):
        logger.warning(
            "The data dictionary indicates more than one column about age. "
            "Neurobagel cannot resolve multiple age values per subject-session, and so will use only the first identified column for age data."
        )

    if (
        len(
            get_columns_about(
                data_dict, concept=mappings.NEUROBAGEL["subject_group"]
            )
        )
        > 1
    ):
        logger.warning(
            "The data dictionary indicates more than one column about subject group. "
            "Neurobagel cannot resolve multiple subject group values per subject-session, and so will use only the first identified column for subject group data."
        )

    if not categorical_cols_have_bids_levels(data_dict):
        logger.warning(
            "The data dictionary contains at least one column that looks categorical but lacks a BIDS 'Levels' attribute."
        )

    if mismatched_cols := get_mismatched_categorical_levels(data_dict):
        logger.warning(
            f"The data dictionary contains columns with mismatched levels between the BIDS and Neurobagel annotations: {mismatched_cols}"
        )


def check_for_duplicate_ids(data_dict: dict, pheno_df: pd.DataFrame):
    """Log an error if there are duplicate participant IDs or duplicate combinations of participant and session IDs, if both are present."""
    id_columns = get_columns_about(
        data_dict, concept=mappings.NEUROBAGEL["participant"]
    ) + get_columns_about(data_dict, concept=mappings.NEUROBAGEL["session"])
    duplicates_mask = pheno_df.duplicated(subset=id_columns, keep=False)
    if duplicates_mask.any():
        duplicate_indices = [
            idx + 2 for idx in pheno_df[duplicates_mask].index
        ]
        log_error(
            logger,
            "The phenotypic table contains duplicate participant IDs or duplicate combinations of participant and session IDs. "
            f"Duplicate IDs were found in these rows (header row is 1): {duplicate_indices}. "
            "Ensure that each row represents a unique participant or participant-session (if a session column is present).",
        )


def validate_inputs(
    data_dict: dict, pheno_df: pd.DataFrame, config: str
) -> None:
    """Determines whether input data are valid"""
    validate_data_dict(data_dict, config)

    if missing_annotated_cols := find_missing_annotated_cols(
        data_dict, pheno_df
    ):
        log_error(
            logger,
            "The provided phenotypic table and data dictionary are incompatible. "
            f"The following columns are annotated in the data dictionary but are missing from the phenotypic table: {missing_annotated_cols}. "
            "Check that you've selected the correct data dictionary for your phenotypic table. "
            "Each column described in the data dictionary must have a corresponding column with the same name in the phenotypic table.",
        )

    columns_about_ids = get_columns_about(
        data_dict, concept=mappings.NEUROBAGEL["participant"]
    ) + get_columns_about(data_dict, concept=mappings.NEUROBAGEL["session"])
    if row_indices := get_rows_with_empty_strings(pheno_df, columns_about_ids):
        log_error(
            logger,
            "The phenotypic table contains missing values in participant or session ID columns. "
            "Ensure that each row includes a non-empty participant ID (and session ID, if the table contains a session ID column). "
            f"Missing IDs were found in these rows (header row is 1): {row_indices}. "
            "[italic]TIP: Check that your table does not have any completely empty rows.[/italic]",
        )

    check_for_duplicate_ids(data_dict, pheno_df)

    undefined_cat_col_values = find_undefined_cat_col_values(
        data_dict, pheno_df
    )
    if undefined_cat_col_values:
        log_error(
            logger,
            "One or more unique values found in annotated categorical columns of the phenotypic table are missing annotations in the data dictionary "
            f"(shown by column as 'column_name': [unannotated_values]): {undefined_cat_col_values}. "
            "Check that you've selected the correct data dictionary or annotate the values that are missing. "
            "[italic]TIP: Ensure that column values in the table exactly match the values annotated in the data dictionary.[/italic]",
        )

    unused_missing_values = find_unused_missing_values(data_dict, pheno_df)
    if unused_missing_values:
        logger.warning(
            "Some values annotated as missing values in the data dictionary were not found "
            "in the corresponding phenotypic table column(s) (shown as 'column_name': [unused_missing_values]): "
            f"{unused_missing_values}. If this is not intentional, please check your data dictionary "
            "and phenotypic table."
        )


def convert_transformation_to_format(data_dict: dict) -> dict:
    """
    If the uploaded data dictionary contains any "Transformation" keys, rename the key(s) to "Format"
    internally for downstream operations involving the data dictionary.
    This ensures compatibility with both v1 and v2 annotation tool-generated data dictionaries.

    TODO: Remove when we no longer support data dictionaries annotated using annotation tool v1.
    """
    age_column_names = get_columns_about(
        data_dict, concept=mappings.NEUROBAGEL["age"]
    )
    if age_column_names:
        age_cols_using_transformation = []
        for age_column_name in age_column_names:
            age_annotations = data_dict[age_column_name]["Annotations"]
            if "Transformation" in age_annotations:
                age_cols_using_transformation.append(age_column_name)
                age_annotations["Format"] = age_annotations.pop(
                    "Transformation"
                )

        if age_cols_using_transformation:
            logger.warning(
                f"The data dictionary contains a deprecated 'Transformation' key in the annotations for the column(s): {age_cols_using_transformation}. "
                "This key has been replaced by 'Format'. For now, 'Transformation' will be interpreted as equivalent to 'Format', "
                "but support for 'Transformation' will be removed in a future release. "
                "We recommend updating your data dictionary using the latest version of the Neurobagel annotation tool."
            )

    return data_dict
