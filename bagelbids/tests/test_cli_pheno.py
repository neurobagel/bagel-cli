import json

import pandas as pd
import pytest
from typer.testing import CliRunner

from bagelbids import mappings
from bagelbids.cli import (
    are_not_missing,
    bagel,
    get_columns_about,
    get_transformed_values,
    is_missing_value,
    map_categories_to_columns,
    map_tools_to_columns,
    transform_age,
)


@pytest.fixture
def runner():
    return CliRunner()


@pytest.mark.parametrize("example", ["example2", "example4", "example6"])
def test_valid_inputs_run_successfully(runner, test_data, tmp_path, example):
    """Basic smoke test for the "pheno" subcommand"""
    # TODO: when we have more than one subcommand, the CLI runner will have
    # to specify the subcommand - until then the CLI behaves as if there was no subcommand

    result = runner.invoke(
        bagel,
        [
            "--pheno",
            test_data / f"{example}.tsv",
            "--dictionary",
            test_data / f"{example}.json",
            "--output",
            tmp_path,
            "--name",
            "do not care name",
        ],
    )
    assert result.exit_code == 0, f"Errored out. STDOUT: {result.output}"
    assert (
        tmp_path / "pheno.jsonld"
    ).exists(), "The pheno.jsonld output was not created."


@pytest.mark.parametrize(
    "example,expected_exception,expected_message",
    [
        ("example3", ValueError, "not a valid Neurobagel data dictionary"),
        (
            "example_invalid",
            ValueError,
            "not a valid Neurobagel data dictionary",
        ),
        ("example7", LookupError, "not compatible"),
        ("example8", ValueError, "more than one column"),
    ],
)
def test_invalid_inputs_are_handled_gracefully(
    runner, test_data, tmp_path, example, expected_exception, expected_message
):
    """Assures that we handle expected user errors in the input files gracefully"""
    with pytest.raises(expected_exception) as e:
        runner.invoke(
            bagel,
            [
                "--pheno",
                test_data / f"{example}.tsv",
                "--dictionary",
                test_data / f"{example}.json",
                "--output",
                tmp_path,
                "--name",
                "do not care name",
            ],
            catch_exceptions=False,
        )

    assert expected_message in str(e.value)


def test_get_columns_that_are_about_concept(test_data):
    """Test that matching annotated columns are returned as a list,
    and that empty list is returned if nothing matches"""
    with open(test_data / "example1.json", "r") as f:
        data_dict = json.load(f)

    assert ["participant_id"] == get_columns_about(
        data_dict, concept=mappings.NEUROBAGEL["participant"]
    )
    assert [] == get_columns_about(data_dict, concept="does not exist concept")


def test_map_categories_to_columns(test_data):
    """Test that inverse mapping of concepts to columns is correctly created"""
    with open(test_data / "example2.json", "r") as f:
        data_dict = json.load(f)

    result = map_categories_to_columns(data_dict)

    assert {"participant", "session", "sex"}.issubset(result.keys())
    assert ["participant_id"] == result["participant"]
    assert ["session_id"] == result["session"]
    assert ["sex"] == result["sex"]


def test_map_tools_to_columns(test_data):
    with open(test_data / "example6.json", "r") as f:
        data_dict = json.load(f)

    result = map_tools_to_columns(data_dict)

    assert result["cogAtlas:1234"] == ["tool_item1", "tool_item2"]
    assert result["cogAtlas:4321"] == ["other_tool_item1"]


def test_get_transformed_categorical_value(test_data):
    """Test that the correct transformed value is returned for a categorical variable"""
    with open(test_data / "example2.json", "r") as f:
        data_dict = json.load(f)
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


def test_that_output_file_contains_name(runner, test_data, tmp_path):
    runner.invoke(
        bagel,
        [
            "--pheno",
            test_data / "example2.tsv",
            "--dictionary",
            test_data / "example2.json",
            "--output",
            tmp_path,
            "--name",
            "my_dataset_name",
        ],
    )

    with open(tmp_path / "pheno.jsonld", "r") as f:
        pheno = json.load(f)

    assert pheno.get("label") == "my_dataset_name"


def test_diagnosis_and_control_status_handled(runner, test_data, tmp_path):
    runner.invoke(
        bagel,
        [
            "--pheno",
            test_data / "example6.tsv",
            "--dictionary",
            test_data / "example6.json",
            "--output",
            tmp_path,
            "--name",
            "my_dataset_name",
        ],
    )

    with open(tmp_path / "pheno.jsonld", "r") as f:
        pheno = json.load(f)

    assert (
        pheno["hasSamples"][0]["diagnosis"][0]["identifier"]
        == "snomed:49049000"
    )
    assert "diagnosis" not in pheno["hasSamples"][1].keys()
    assert "diagnosis" not in pheno["hasSamples"][2].keys()
    assert pheno["hasSamples"][2]["isSubjectGroup"] == "purl:NCIT_C94342"


def test_get_assessment_tool_availability(test_data):
    """
    Ensure that subjects who have one or more missing values in columns mapped to an assessment
    tool are correctly identified as not having this assessment tool
    """
    with open(test_data / "example6.json", "r") as f:
        data_dict = json.load(f)
    pheno = pd.read_csv(test_data / "example6.tsv", sep="\t")
    test_columns = ["tool_item1", "tool_item2"]

    assert are_not_missing(test_columns, pheno.iloc[0], data_dict) is False
    assert are_not_missing(test_columns, pheno.iloc[2], data_dict) is False
    assert are_not_missing(test_columns, pheno.iloc[4], data_dict) is True


def test_assessment_data_are_parsed_correctly(runner, test_data, tmp_path):
    runner.invoke(
        bagel,
        [
            "--pheno",
            test_data / "example6.tsv",
            "--dictionary",
            test_data / "example6.json",
            "--output",
            tmp_path,
            "--name",
            "my_dataset_name",
        ],
    )

    with open(tmp_path / "pheno.jsonld", "r") as f:
        pheno = json.load(f)

    assert pheno["hasSamples"][0].get("assessment") is None
    assert pheno["hasSamples"][1].get("assessment") is None
    assert [
        {"identifier": "cogAtlas:1234"},
        {"identifier": "cogAtlas:4321"},
    ] == pheno["hasSamples"][2].get("assessment")


@pytest.mark.parametrize(
    "raw_age,expected_age,heuristic",
    [
        ("11,0", 11.0, "bg:euro"),
        ("90+", 90.0, "bg:bounded"),
        ("20-30", 25.0, "bg:range"),
        ("20-21", 20.5, "bg:range"),
        ("20Y6M", 20.5, "bg:iso8601"),
        ("P20Y6M", 20.5, "bg:iso8601"),
        ("20Y9M", 20.75, "bg:iso8601"),
    ],
)
def test_age_gets_converted(raw_age, expected_age, heuristic):
    assert expected_age == transform_age(raw_age, heuristic)


def test_cli_age_is_processed(runner, test_data, tmp_path):
    runner.invoke(
        bagel,
        [
            "--pheno",
            test_data / "example2.tsv",
            "--dictionary",
            test_data / "example2.json",
            "--output",
            tmp_path,
            "--name",
            "my_dataset_name",
        ],
    )

    with open(tmp_path / "pheno.jsonld", "r") as f:
        pheno = json.load(f)

    assert 20.5 == pheno["hasSamples"][0]["age"]
    assert pytest.approx(25.66, 0.01) == pheno["hasSamples"][1]["age"]
