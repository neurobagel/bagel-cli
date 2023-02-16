import json

import pandas as pd
import pytest

from bagelbids import mappings
from bagelbids.cli import (
    are_not_missing,
    get_columns_about,
    get_transformed_values,
    is_missing_value,
    map_categories_to_columns,
    map_tools_to_columns,
    transform_age,
)


@pytest.fixture
def load_ex_json(test_data):
    def _read_file(example_json):
        with open(test_data / example_json, "r") as f:
            data_dict = json.load(f)
            return data_dict

    return _read_file


def test_get_columns_that_are_about_concept(load_ex_json):
    """Test that matching annotated columns are returned as a list,
    and that empty list is returned if nothing matches"""
    data_dict = load_ex_json("example1.json")

    assert ["participant_id"] == get_columns_about(
        data_dict, concept=mappings.NEUROBAGEL["participant"]
    )
    assert [] == get_columns_about(data_dict, concept="does not exist concept")


def test_map_categories_to_columns(load_ex_json):
    """Test that inverse mapping of concepts to columns is correctly created"""
    data_dict = load_ex_json("example2.json")

    result = map_categories_to_columns(data_dict)

    assert {"participant", "session", "sex"}.issubset(result.keys())
    assert ["participant_id"] == result["participant"]
    assert ["session_id"] == result["session"]
    assert ["sex"] == result["sex"]


def test_map_tools_to_columns(load_ex_json):
    data_dict = load_ex_json("example6.json")

    result = map_tools_to_columns(data_dict)

    assert result["cogAtlas:1234"] == ["tool_item1", "tool_item2"]
    assert result["cogAtlas:4321"] == ["other_tool_item1"]


def test_get_transformed_categorical_value(test_data, load_ex_json):
    """Test that the correct transformed value is returned for a categorical variable"""
    data_dict = load_ex_json("example2.json")
    pheno = pd.read_csv(test_data / "example2.tsv", sep="\t")

    assert "bids:Male" == get_transformed_values(
        columns=["sex"],
        row=pheno.iloc[0],
        data_dict=data_dict,
    )


@pytest.mark.parametrize(
    "value,column,expected",
    [
        ("test_value", "test_column", True),
        ("does not exist", "test_column", False),
        ("my_value", "empty_column", False),
    ],
)
def test_missing_values(value, column, expected):
    """Test that missing values are correctly detected"""
    test_data_dict = {
        "test_column": {"Annotations": {"MissingValues": ["test_value"]}},
        "empty_column": {"Annotations": {}},
    }

    assert is_missing_value(value, column, test_data_dict) is expected


def test_get_assessment_tool_availability(test_data, load_ex_json):
    """
    Ensure that subjects who have one or more missing values in columns mapped to an assessment
    tool are correctly identified as not having this assessment tool
    """
    data_dict = load_ex_json("example6.json")
    pheno = pd.read_csv(test_data / "example6.tsv", sep="\t")
    test_columns = ["tool_item1", "tool_item2"]

    assert are_not_missing(test_columns, pheno.iloc[0], data_dict) is False
    assert are_not_missing(test_columns, pheno.iloc[2], data_dict) is False
    assert are_not_missing(test_columns, pheno.iloc[4], data_dict) is True


@pytest.mark.parametrize(
    "raw_age,expected_age,heuristic",
    [
        ("11,0", 11.0, "bg:euro"),
        ("90+", 90.0, "bg:bounded"),
        ("20-30", 25.0, "bg:range"),
        ("20Y6M", 20.5, "bg:iso8601"),
        ("P20Y6M", 20.5, "bg:iso8601"),
        ("20Y9M", 20.75, "bg:iso8601"),
    ],
)
def test_age_gets_converted(raw_age, expected_age, heuristic):
    assert expected_age == transform_age(raw_age, heuristic)
