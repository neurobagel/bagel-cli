import pytest
from typer.testing import CliRunner

from bagelbids.cli import bagel


@pytest.fixture
def runner():
    return CliRunner()


@pytest.mark.parametrize(
    "example", ["example2", "example4", "example6", "example_synthetic"]
)
def test_valid_inputs_run_successfully(runner, test_data, tmp_path, example):
    """Basic smoke test for the "pheno" subcommand"""
    # TODO: when we have more than one subcommand, the CLI runner will have
    # to specify the subcommand - until then the CLI behaves as if there was no subcommand

    result = runner.invoke(
        bagel,
        [
            "pheno",
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
                "pheno",
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


def test_that_output_file_contains_name(
    runner, test_data, tmp_path, load_test_json
):
    runner.invoke(
        bagel,
        [
            "pheno",
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

    pheno = load_test_json(tmp_path / "pheno.jsonld")

    assert pheno.get("label") == "my_dataset_name"


def test_diagnosis_and_control_status_handled(
    runner, test_data, tmp_path, load_test_json
):
    runner.invoke(
        bagel,
        [
            "pheno",
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

    pheno = load_test_json(tmp_path / "pheno.jsonld")

    assert (
        pheno["hasSamples"][0]["diagnosis"][0]["identifier"]
        == "snomed:49049000"
    )
    assert "diagnosis" not in pheno["hasSamples"][1].keys()
    assert "diagnosis" not in pheno["hasSamples"][2].keys()
    assert pheno["hasSamples"][2]["isSubjectGroup"] == "purl:NCIT_C94342"


@pytest.mark.parametrize(
    "assessment, subject",
    [
        (None, 0),
        (None, 1),
        (
            [
                {"identifier": "cogAtlas:1234", "schemaKey": "Assessment"},
                {"identifier": "cogAtlas:4321", "schemaKey": "Assessment"},
            ],
            2,
        ),
    ],
)
def test_assessment_data_are_parsed_correctly(
    runner, test_data, tmp_path, load_test_json, assessment, subject
):
    runner.invoke(
        bagel,
        [
            "pheno",
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

    pheno = load_test_json(tmp_path / "pheno.jsonld")

    assert assessment == pheno["hasSamples"][subject].get("assessment")


@pytest.mark.parametrize(
    "expected_age, subject",
    [(20.5, 0), (pytest.approx(25.66, 0.01), 1)],
)
def test_cli_age_is_processed(
    runner, test_data, tmp_path, load_test_json, expected_age, subject
):
    runner.invoke(
        bagel,
        [
            "pheno",
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

    pheno = load_test_json(tmp_path / "pheno.jsonld")

    assert expected_age == pheno["hasSamples"][subject]["age"]


def test_output_includes_context(runner, test_data, tmp_path, load_test_json):
    runner.invoke(
        bagel,
        [
            "pheno",
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

    pheno = load_test_json(tmp_path / "pheno.jsonld")

    assert pheno.get("@context") is not None
    assert all(
        [sub.get("identifier") is not None for sub in pheno["hasSamples"]]
    )
