import pandas as pd
import pytest

from bagel import mappings
from bagel.pheno_utils import (
    are_not_missing,
    generate_context,
    get_columns_about,
    get_transformed_values,
    is_missing_value,
    map_categories_to_columns,
    map_tools_to_columns,
    transform_age,
)


@pytest.fixture
def get_test_context():
    """Generate an @context dictionary to test against."""
    return generate_context()


def test_get_columns_that_are_about_concept(test_data, load_test_json):
    """Test that matching annotated columns are returned as a list,
    and that empty list is returned if nothing matches"""
    data_dict = load_test_json(test_data / "example1.json")

    assert ["participant_id"] == get_columns_about(
        data_dict, concept=mappings.NEUROBAGEL["participant"]
    )
    assert [] == get_columns_about(data_dict, concept="does not exist concept")


def test_map_categories_to_columns(test_data, load_test_json):
    """Test that inverse mapping of concepts to columns is correctly created"""
    data_dict = load_test_json(test_data / "example2.json")

    result = map_categories_to_columns(data_dict)

    assert {"participant", "session", "sex"}.issubset(result.keys())
    assert ["participant_id"] == result["participant"]
    assert ["session_id"] == result["session"]
    assert ["sex"] == result["sex"]


@pytest.mark.parametrize(
    "tool, columns",
    [
        ("cogAtlas:1234", ["tool_item1", "tool_item2"]),
        ("cogAtlas:4321", ["other_tool_item1"]),
    ],
)
def test_map_tools_to_columns(test_data, load_test_json, tool, columns):
    data_dict = load_test_json(test_data / "example6.json")

    result = map_tools_to_columns(data_dict)

    assert result[tool] == columns


def test_get_transformed_categorical_value(test_data, load_test_json):
    """Test that the correct transformed value is returned for a categorical variable"""
    data_dict = load_test_json(test_data / "example2.json")
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


@pytest.mark.parametrize(
    "subject_idx, is_avail",
    [(0, False), (2, False), (4, True)],
)
def test_get_assessment_tool_availability(
    test_data, load_test_json, subject_idx, is_avail
):
    """
    Ensure that subjects who have one or more missing values in columns mapped to an assessment
    tool are correctly identified as not having this assessment tool
    """
    data_dict = load_test_json(test_data / "example6.json")
    pheno = pd.read_csv(test_data / "example6.tsv", sep="\t")
    test_columns = ["tool_item1", "tool_item2"]

    assert (
        are_not_missing(test_columns, pheno.iloc[subject_idx], data_dict)
        is is_avail
    )


@pytest.mark.parametrize(
    "raw_age,expected_age,heuristic",
    [
        ("11.0", 11.0, "bg:float"),
        ("11", 11.0, "bg:int"),
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


@pytest.mark.parametrize(
    "raw_age, incorrect_heuristic",
    [
        ("11,0", "bg:float"),
        ("11.0", "bg:iso8601"),
        ("11+", "bg:range"),
        ("20-30", "bg:bounded"),
    ],
)
def test_incorrect_age_heuristic(raw_age, incorrect_heuristic):
    """Given an age transformation that does not match the type of age value provided, returns an informative error."""
    with pytest.raises(ValueError) as e:
        transform_age(raw_age, incorrect_heuristic)

    assert (
        f"problem with applying the age transformation: {incorrect_heuristic}."
        in str(e.value)
    )


def test_invalid_age_heuristic():
    """Given an age transformation that is not recognized, returns an informative ValueError."""
    with pytest.raises(ValueError) as e:
        transform_age("11,0", "bg:birthyear")

    assert "unrecognized age transformation: bg:birthyear" in str(e.value)


@pytest.mark.parametrize(
    "model, attributes",
    [
        ("Bagel", ["identifier"]),
        ("Image", ["identifier", "schemaKey"]),
        ("Acquisition", ["hasContrastType", "schemaKey"]),
        ("Diagnosis", ["identifier", "schemaKey"]),
        ("Assessment", ["identifier", "schemaKey"]),
        ("Session", ["label", "filePath", "hasAcquisition", "schemaKey"]),
        (
            "Subject",
            [
                "label",
                "hasSession",
                "age",
                "sex",
                "isSubjectGroup",
                "diagnosis",
                "assessment",
                "schemaKey",
            ],
        ),
        ("Dataset", ["label", "hasSamples", "schemaKey"]),
    ],
)
def test_generate_context(get_test_context, model, attributes):
    """Test that each model and its set of attributes have corresponding entries in @context."""
    assert model in get_test_context["@context"]
    for attribute in attributes:
        assert attribute in get_test_context["@context"]
