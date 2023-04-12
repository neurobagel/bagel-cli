import pytest

from bagel.cli import bagel


@pytest.mark.parametrize(
    "example", ["example2", "example4", "example6", "example_synthetic"]
)
def test_pheno_valid_inputs_run_successfully(
    runner, test_data, tmp_path, example
):
    """Basic smoke test for the "pheno" subcommand"""
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
        (
            "example9",
            LookupError,
            "values not found in the data dictionary (shown as <column_name>: [<undefined values>]): {'group': ['SIB']}",
        ),
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


def test_unused_missing_values_raises_warning(
    runner,
    test_data,
    tmp_path,
):
    """
    Tests that an informative warning is raised when annotated missing values are not found in the
    phenotypic file.
    """
    with pytest.warns(UserWarning) as w:
        runner.invoke(
            bagel,
            [
                "pheno",
                "--pheno",
                test_data / "example10.tsv",
                "--dictionary",
                test_data / "example10.json",
                "--output",
                tmp_path,
                "--name",
                "testing dataset",
            ],
            catch_exceptions=False,
        )

    assert len(w) == 1
    assert (
        "missing values in the data dictionary were not found in the corresponding phenotypic file column(s) "
        "(<column_name>: [<unused missing values>]): {'group': ['MISSING'], 'tool_item1': ['none', ''], 'tool_item2': ['none', '']}"
    ) in str(w[0].message.args[0])


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
    assert (
        pheno["hasSamples"][2]["isSubjectGroup"]["identifier"]
        == "purl:NCIT_C94342"
    )


@pytest.mark.parametrize(
    "attribute", ["sex", "diagnosis", "assessment", "isSubjectGroup"]
)
def test_controlled_terms_have_identifiers(
    attribute, runner, test_data, tmp_path, load_test_json
):
    runner.invoke(
        bagel,
        [
            "pheno",
            "--pheno",
            test_data / "example_synthetic.tsv",
            "--dictionary",
            test_data / "example_synthetic.json",
            "--output",
            tmp_path,
            "--name",
            "do not care name",
        ],
    )

    pheno = load_test_json(tmp_path / "pheno.jsonld")

    for sub in pheno["hasSamples"]:
        if attribute in sub.keys():
            value = sub.get(attribute)
            if not isinstance(value, list):
                value = [value]
            assert all(
                ["identifier" in entry for entry in value]
            ), f"{attribute}: did not have an identifier for subject {sub} and value {value}"


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
