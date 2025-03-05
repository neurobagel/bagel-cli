import pandas as pd
import pytest

from bagel import mappings
from bagel.utilities import pheno_utils


@pytest.mark.parametrize(
    "partial_data_dict, invalid_column_name",
    [
        # sex column missing Levels
        (
            {
                "participant_id": {
                    "Description": "A participant ID",
                    "Annotations": {
                        "IsAbout": {
                            "TermURL": "nb:ParticipantID",
                            "Label": "Unique participant identifier",
                        },
                        "Identifies": "participant",
                    },
                },
                "sex": {
                    "Description": "Participant sex",
                    "Annotations": {
                        "IsAbout": {"TermURL": "nb:Sex", "Label": ""}
                    },
                },
            },
            "sex",
        ),
        # age column missing Transformation
        (
            {
                "participant_id": {
                    "Description": "A participant ID",
                    "Annotations": {
                        "IsAbout": {
                            "TermURL": "nb:ParticipantID",
                            "Label": "Unique participant identifier",
                        },
                        "Identifies": "participant",
                    },
                },
                "age": {
                    "Description": "Participant age",
                    "Annotations": {
                        "IsAbout": {
                            "TermURL": "nb:Age",
                            "Label": "Chronological age",
                        }
                    },
                },
            },
            "age",
        ),
    ],
)
def test_schema_invalid_column_raises_error(
    partial_data_dict, invalid_column_name
):
    """
    Test that when an input data dictionary contains a schema invalid column annotation,
    an informative error is raised which includes the name of the offending column.
    """
    with pytest.raises(ValueError) as e:
        pheno_utils.validate_data_dict(partial_data_dict)

    for substring in [
        "not a valid Neurobagel data dictionary",
        invalid_column_name,
    ]:
        assert substring in str(e.value)


def test_get_columns_that_are_about_concept(test_data, load_test_json):
    """Test that matching annotated columns are returned as a list,
    and that empty list is returned if nothing matches"""
    data_dict = load_test_json(test_data / "example14.json")

    assert ["participant_id"] == pheno_utils.get_columns_about(
        data_dict, concept=mappings.NEUROBAGEL["participant"]
    )
    assert [] == pheno_utils.get_columns_about(
        data_dict, concept="does not exist concept"
    )


def test_get_columns_with_annotations():
    example = {
        "someOtherColumn": {
            "Description": "This is cool in BIDS, but not in Neurobagel"
        },
        "participant_id": {
            "Description": "A participant ID",
            "Annotations": {
                "IsAbout": {
                    "TermURL": "nb:ParticipantID",
                    "Label": "Unique participant identifier",
                }
            },
        },
    }
    result = pheno_utils.get_annotated_columns(example)[0]
    assert result[0] == "participant_id"
    assert result[1] == example["participant_id"]


def test_find_unsupported_namespaces_and_term_urls():
    """Test that term URLs with unsupported namespaces are correctly identified in a data dictionary."""
    data_dict = {
        "participant_id": {
            "Description": "Participant ID",
            "Annotations": {
                "IsAbout": {
                    "TermURL": "nb:ParticipantID",
                    "Label": "Unique participant identifier",
                },
                "Identifies": "participant",
            },
        },
        "group": {
            "Description": "Experimental group",
            "Levels": {"PAT": "Patient", "HC": "Healthy control"},
            "Annotations": {
                "IsAbout": {"TermURL": "nb:Diagnosis", "Label": "Diagnosis"},
                "Levels": {
                    "PAT": {
                        "TermURL": "snomed:49049000",
                        "Label": "Parkinson's disease",
                    },
                    "HC": {
                        "TermURL": "unknownvocab:1234",
                        "Label": "Healthy control",
                    },
                },
            },
        },
        "updrs_total": {
            "Description": "Total UPDRS scores",
            "Annotations": {
                "IsAbout": {
                    "TermURL": "nb:Assessment",
                    "Label": "Assessment tool",
                },
                "IsPartOf": {
                    "TermURL": "deprecatedvocab:1234",
                    "Label": "Unified Parkinson's Disease Rating Scale",
                },
            },
        },
    }

    assert pheno_utils.find_unsupported_namespaces_and_term_urls(
        data_dict
    ) == (
        ["deprecatedvocab", "unknownvocab"],
        {
            "group": "unknownvocab:1234",
            "updrs_total": "deprecatedvocab:1234",
        },
    )


@pytest.mark.parametrize(
    "namespaces,deprecated_namespaces",
    [
        (["fakevocab", "unknownvocab"], []),
        (["cogatlas", "unknownvocab"], ["cogatlas"]),
        (["snomed", "cogatlas"], ["cogatlas"]),
    ],
)
def test_find_deprecated_namespaces(namespaces, deprecated_namespaces):
    """Test that vocabulary namespace prefixes deprecated by Neurobagel are correctly identified."""
    assert (
        pheno_utils.find_deprecated_namespaces(namespaces)
        == deprecated_namespaces
    )


def test_map_categories_to_columns(test_data, load_test_json):
    """Test that inverse mapping of concepts to columns is correctly created"""
    data_dict = load_test_json(test_data / "example2.json")

    result = pheno_utils.map_categories_to_columns(data_dict)

    assert {"participant", "session", "sex"}.issubset(result.keys())
    assert ["participant_id"] == result["participant"]
    assert ["session_id"] == result["session"]
    assert ["sex"] == result["sex"]


@pytest.mark.parametrize(
    "tool, columns",
    [
        ("snomed:1234", ["tool_item1", "tool_item2"]),
        ("snomed:4321", ["other_tool_item1"]),
    ],
)
def test_map_tools_to_columns(test_data, load_test_json, tool, columns):
    data_dict = load_test_json(test_data / "example6.json")

    result = pheno_utils.map_tools_to_columns(data_dict)

    assert result[tool] == columns


@pytest.mark.parametrize(
    "example, column_list, expected_values",
    [
        ("example2", ["sex"], ["snomed:248153007"]),
        (
            "example19",
            ["group", "diagnosis"],
            ["snomed:49049000", "snomed:724761004"],
        ),
    ],
)
def test_get_transformed_categorical_values(
    test_data, load_test_json, example, column_list, expected_values
):
    """Test that the correct transformed values are returned for a categorical variable"""
    data_dict = load_test_json(test_data / f"{example}.json")
    pheno = pd.read_csv(test_data / f"{example}.tsv", sep="\t")

    assert expected_values == pheno_utils.get_transformed_values(
        columns=column_list,
        row=pheno.iloc[0],
        data_dict=data_dict,
    )


@pytest.mark.parametrize(
    "example,expected_result",
    [
        (
            {
                "column": {
                    "Annotations": {
                        "IsAbout": {"TermURL": "something", "Labels": "other"},
                        "Levels": {
                            "val1": {"TermURL": "something", "Label": "other"}
                        },
                    }
                }
            },
            True,
        ),
        (
            {
                "column": {
                    "Levels": {"val1": "some description"},
                    "Annotations": {
                        "IsAbout": {"TermURL": "something", "Labels": "other"}
                    },
                }
            },
            False,
        ),
    ],
)
def test_detect_categorical_column(example, expected_result):
    result = pheno_utils.is_column_categorical(
        column="column", data_dict=example
    )

    assert result is expected_result


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

    assert (
        pheno_utils.is_missing_value(value, column, test_data_dict) is expected
    )


@pytest.mark.parametrize(
    "subject_idx, is_avail",
    [(0, True), (2, False), (4, True)],
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
        pheno_utils.are_any_available(
            test_columns, pheno.iloc[subject_idx], data_dict
        )
        is is_avail
    )


@pytest.mark.parametrize(
    "columns, expected_indices",
    [(["participant_id"], [0]), (["session_id"], [2])],
)
def test_missing_ids_in_columns(test_data, columns, expected_indices):
    """
    When a participant or session labeled column has missing values,
    we raise and provide the list of offending row indices
    """
    pheno = pd.read_csv(
        test_data / "example11.tsv", sep="\t", keep_default_na=False, dtype=str
    )
    assert expected_indices == pheno_utils.get_rows_with_empty_strings(
        pheno, columns=columns
    )


@pytest.mark.parametrize(
    "raw_age,expected_age,heuristic",
    [
        ("11.0", 11.0, "nb:FromFloat"),
        ("11", 11.0, "nb:FromInt"),
        ("11,0", 11.0, "nb:FromEuro"),
        ("90+", 90.0, "nb:FromBounded"),
        ("20Y6M", 20.5, "nb:FromISO8601"),
        ("P20Y6M", 20.5, "nb:FromISO8601"),
        ("20Y9M", 20.75, "nb:FromISO8601"),
        ("20-25", 22.5, "nb:FromRange"),
        ("20.5-25.5", 23.0, "nb:FromRange"),
    ],
)
def test_age_gets_converted(raw_age, expected_age, heuristic):
    assert expected_age == pheno_utils.transform_age(raw_age, heuristic)


@pytest.mark.parametrize(
    "raw_age, incorrect_heuristic",
    [
        ("11,0", "nb:FromFloat"),
        ("11.0", "nb:FromISO8601"),
        ("20-30", "nb:FromBounded"),
        ("20+", "nb:FromRange"),
    ],
)
def test_incorrect_age_heuristic(raw_age, incorrect_heuristic):
    """Given an age transformation that does not match the type of age value provided, returns an informative error."""
    with pytest.raises(ValueError) as e:
        pheno_utils.transform_age(raw_age, incorrect_heuristic)

    assert (
        f"problem with applying the age transformation: {incorrect_heuristic}."
        in str(e.value)
    )


def test_invalid_age_heuristic():
    """Given an age transformation that is not recognized, returns an informative ValueError."""
    with pytest.raises(ValueError) as e:
        pheno_utils.transform_age("11,0", "nb:birthyear")

    assert "unrecognized age transformation: nb:birthyear" in str(e.value)
