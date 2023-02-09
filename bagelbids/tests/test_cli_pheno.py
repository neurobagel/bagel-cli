import json

import pytest
from typer.testing import CliRunner

from bagelbids import mappings
from bagelbids.cli import bagel, get_columns_about


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
