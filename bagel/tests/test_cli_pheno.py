import pytest

from bagel.cli import bagel


@pytest.mark.parametrize(
    "example",
    [
        "example2",
        "example4",
        "example6",
        "example12",
        "example13",
        "example14",
        "example_synthetic",
    ],
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
        (
            "example3",
            LookupError,
            ["must contain at least one column with Neurobagel annotations"],
        ),
        (
            "example_invalid",
            ValueError,
            ["not a valid Neurobagel data dictionary"],
        ),
        ("example7", LookupError, ["not compatible"]),
        ("example8", ValueError, ["more than one column"]),
        (
            "example9",
            LookupError,
            [
                "values not annotated in the data dictionary",
                "'group': ['UNANNOTATED']",
            ],
        ),
        (
            "example11",
            LookupError,
            ["missing values in participant or session id"],
        ),
        (
            "example15",
            LookupError,
            [
                "must contain at least one column annotated as being about participant ID"
            ],
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

    for substring in expected_message:
        assert substring in str(e.value)


# def test_no_annotated_columns_returns_error(runner, test_data, tmp_path):
#     """Tests that a dataset with no annotated columns returns an error"""
#     with pytest.raises(ValueError) as e:
#         runner.invoke(
#             bagel,
#             [
#                 "pheno",
#                 "--pheno",
#                 test_data / "example10.tsv",
#                 "--dictionary",
#                 test_data / "example10.json",
#                 "--output",
#                 tmp_path,
#                 "--name",
#                 "do not care name",
#             ],
#             catch_exceptions=False,
#         )

#     assert


@pytest.mark.parametrize(
    "portal",
    [
        "openneuro.org/datasets/ds002080",
        "https://openneuro",
        "not a url",
        "www.github.com/mycoolrepo/mycooldataset",
    ],
)
def test_invalid_portal_uris_produces_error(
    runner,
    test_data,
    tmp_path,
    portal,
):
    """Tests that invalid or non-HTTP/HTTPS URLs result in a user-friendly error."""
    result = runner.invoke(
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
            "test dataset 2",
            "--portal",
            portal,
        ],
        catch_exceptions=False,
    )

    assert result.exit_code != 0
    # For some reason, it seems the Rich formatting of the error causes problems
    # with matching the entire error substring at once
    assert all(
        word in str(result.output) for word in "not a valid http or https URL"
    )


def test_missing_bids_levels_raises_warning(
    runner,
    test_data,
    tmp_path,
):
    with pytest.warns(UserWarning) as w:
        runner.invoke(
            bagel,
            [
                "pheno",
                "--pheno",
                test_data / "example12.tsv",
                "--dictionary",
                test_data / "example12.json",
                "--output",
                tmp_path,
                "--name",
                "testing dataset",
            ],
            catch_exceptions=False,
        )

    assert len(w) == 1
    assert "looks categorical but lacks a BIDS 'Levels' attribute" in str(
        w[0].message.args[0]
    )


def test_bids_neurobagel_levels_mismatch_raises_warning(
    runner,
    test_data,
    tmp_path,
):
    with pytest.warns(UserWarning) as w:
        runner.invoke(
            bagel,
            [
                "pheno",
                "--pheno",
                test_data / "example13.tsv",
                "--dictionary",
                test_data / "example13.json",
                "--output",
                tmp_path,
                "--name",
                "testing dataset",
            ],
            catch_exceptions=False,
        )

    assert len(w) == 1
    assert all(
        warn_substring in str(w[0].message.args[0])
        for warn_substring in [
            "columns with mismatched levels",
            "['pheno_sex']",
        ]
    )


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
    for warn_substring in [
        "missing values in the data dictionary were not found",
        "'group': ['NOT IN TSV']",
        "'tool_item1': ['NOT IN TSV 1', 'NOT IN TSV 2']",
        "'tool_item2': ['NOT IN TSV 1', 'NOT IN TSV 2']",
    ]:
        assert warn_substring in str(w[0].message.args[0])


def test_that_output_file_contains_dataset_level_attributes(
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
            "--portal",
            "http://my_dataset_site.com",
        ],
    )

    pheno = load_test_json(tmp_path / "pheno.jsonld")

    assert pheno.get("hasLabel") == "my_dataset_name"
    assert pheno.get("hasPortalURI") == "http://my_dataset_site.com"


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
        pheno["hasSamples"][0]["hasDiagnosis"][0]["identifier"]
        == "snomed:49049000"
    )
    assert "hasDiagnosis" not in pheno["hasSamples"][1].keys()
    assert "hasDiagnosis" not in pheno["hasSamples"][2].keys()
    assert (
        pheno["hasSamples"][2]["isSubjectGroup"]["identifier"]
        == "purl:NCIT_C94342"
    )


@pytest.mark.parametrize(
    "attribute", ["hasSex", "hasDiagnosis", "hasAssessment", "isSubjectGroup"]
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


def test_controlled_term_classes_have_uri_type(
    runner, test_data, tmp_path, load_test_json
):
    """Tests that classes specified as schemaKeys (@type) for subject-level attributes in a .jsonld are also defined in the context."""
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

    pheno = load_test_json(test_data / "example_synthetic.jsonld")

    for sub in pheno["hasSamples"]:
        for key, value in sub.items():
            if not isinstance(value, (list, dict)):
                continue
            if isinstance(value, dict):
                value = [value]
            assert all(
                entry.get("schemaKey", "no schemaKey set") in pheno["@context"]
                for entry in value
            ), f"Attribute {key} for subject {sub} has a schemaKey that does not have a corresponding URI in the context."


@pytest.mark.parametrize(
    "assessment, subject",
    [
        (None, 0),
        (None, 1),
        (
            [
                {"identifier": "cogatlas:1234", "schemaKey": "Assessment"},
                {"identifier": "cogatlas:4321", "schemaKey": "Assessment"},
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

    assert assessment == pheno["hasSamples"][subject].get("hasAssessment")


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

    assert expected_age == pheno["hasSamples"][subject]["hasAge"]


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


@pytest.mark.parametrize(
    "sub_id, missing_val_property",
    [
        ("sub-02", ["hasAge"]),
        ("sub-03", ["hasSex"]),
        ("sub-03", ["hasDiagnosis", "isSubjectGroup"]),
    ],
)
def test_output_excludes_properties_for_missing_vals(
    runner, test_data, tmp_path, load_test_json, sub_id, missing_val_property
):
    """
    Tests that for occurrences of values annotated as missing for a Neurobagel variable, the corresponding property does not exist
    for the subject node in the output .jsonld. NOTE: Excludes Assessment tool columns because these are treated (and tested) separately,
    see https://www.neurobagel.org/documentation/dictionaries/#assessment-tool for reference.
    """
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
            "BIDS synthetic test",
        ],
    )

    pheno = load_test_json(tmp_path / "pheno.jsonld")
    for sub in pheno["hasSamples"]:
        if sub["hasLabel"] == sub_id:
            for entry in missing_val_property:
                assert (
                    sub.get(entry) is None
                ), f"{sub_id} output contains value for {entry} where annotated as missing"
