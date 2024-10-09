import os

import pytest

from bagel.cli import bagel


@pytest.fixture(scope="function")
def default_pheno_output_path(tmp_path):
    "Return temporary pheno command output filepath that uses the default filename."
    return tmp_path / "pheno.jsonld"


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
        "example17",
        "example19",
        "example20",
        "example21",
    ],
)
def test_pheno_valid_inputs_run_successfully(
    runner,
    test_data,
    test_data_upload_path,
    default_pheno_output_path,
    example,
):
    """Basic smoke test for the "pheno" subcommand"""
    if example == "example_synthetic":
        result = runner.invoke(
            bagel,
            [
                "pheno",
                "--pheno",
                test_data_upload_path / f"{example}.tsv",
                "--dictionary",
                test_data_upload_path / f"{example}.json",
                "--output",
                default_pheno_output_path,
                "--name",
                "synthetic",
            ],
        )
    else:
        result = runner.invoke(
            bagel,
            [
                "pheno",
                "--pheno",
                test_data / f"{example}.tsv",
                "--dictionary",
                test_data / f"{example}.json",
                "--output",
                default_pheno_output_path,
                "--name",
                "do not care name",
            ],
        )
    assert result.exit_code == 0, f"Errored out. STDOUT: {result.output}"
    assert (
        default_pheno_output_path
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
        (
            "example1",
            LookupError,
            ["do not have unique combinations of participant and session IDs"],
        ),
        (
            "example18",
            LookupError,
            ["do not have unique combinations of participant and session IDs"],
        ),
    ],
)
def test_invalid_inputs_are_handled_gracefully(
    runner,
    test_data,
    default_pheno_output_path,
    example,
    expected_exception,
    expected_message,
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
                default_pheno_output_path,
                "--name",
                "do not care name",
            ],
            catch_exceptions=False,
        )

    for substring in expected_message:
        assert substring in str(e.value)


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
    default_pheno_output_path,
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
            default_pheno_output_path,
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


def test_multiple_age_or_sex_columns_raises_warning(
    runner,
    test_data,
    default_pheno_output_path,
):
    """Test that an informative warning is raised when multiple columns in the phenotypic file have been annotated as being about age or sex."""
    with pytest.warns(UserWarning) as w:
        runner.invoke(
            bagel,
            [
                "pheno",
                "--pheno",
                test_data / "example20.tsv",
                "--dictionary",
                test_data / "example20.json",
                "--output",
                default_pheno_output_path,
                "--name",
                "Multiple age/sex columns dataset",
            ],
            catch_exceptions=False,
        )

    assert len(w) == 2
    warnings = [warning.message.args[0] for warning in w]
    for warn_substring in [
        "more than one column about age",
        "more than one column about sex",
    ]:
        assert [any(warn_substring in warning_str for warning_str in warnings)]


def test_missing_bids_levels_raises_warning(
    runner,
    test_data,
    default_pheno_output_path,
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
                default_pheno_output_path,
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
    default_pheno_output_path,
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
                default_pheno_output_path,
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
    default_pheno_output_path,
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
                default_pheno_output_path,
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


@pytest.mark.parametrize(
    "pheno_file,dictionary_file",
    [
        ("example2.csv", "example2.json"),
        ("example16.tsv", "example16.json"),
        ("example2.txt", "example2.json"),
    ],
)
def test_providing_csv_file_raises_error(
    pheno_file,
    dictionary_file,
    runner,
    test_data,
    tmp_path,
    default_pheno_output_path,
):
    """Providing a .csv file or a file with .tsv extension but incorrect encoding should be handled with an
    informative error."""
    with pytest.raises(ValueError) as e:
        runner.invoke(
            bagel,
            [
                "pheno",
                "--pheno",
                test_data / pheno_file,
                "--dictionary",
                test_data / dictionary_file,
                "--output",
                default_pheno_output_path,
                "--name",
                "testing dataset",
            ],
            catch_exceptions=False,
        )

    assert "Please provide a valid .tsv phenotypic file" in str(e.value)


def test_that_output_file_contains_dataset_level_attributes(
    runner, test_data, default_pheno_output_path, load_test_json
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
            default_pheno_output_path,
            "--name",
            "my_dataset_name",
            "--portal",
            "http://my_dataset_site.com",
        ],
    )

    pheno = load_test_json(default_pheno_output_path)

    assert pheno.get("hasLabel") == "my_dataset_name"
    assert pheno.get("hasPortalURI") == "http://my_dataset_site.com"


def test_diagnosis_and_control_status_handled(
    runner, test_data, default_pheno_output_path, load_test_json
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
            default_pheno_output_path,
            "--name",
            "my_dataset_name",
        ],
    )

    pheno = load_test_json(default_pheno_output_path)

    assert (
        pheno["hasSamples"][0]["hasSession"][0]["hasDiagnosis"][0][
            "identifier"
        ]
        == "snomed:49049000"
    )
    assert "hasDiagnosis" not in pheno["hasSamples"][1]["hasSession"][0].keys()
    assert "hasDiagnosis" not in pheno["hasSamples"][2]["hasSession"][0].keys()
    assert (
        pheno["hasSamples"][2]["hasSession"][0]["isSubjectGroup"]["identifier"]
        == "ncit:C94342"
    )


@pytest.mark.parametrize(
    "attribute", ["hasSex", "hasDiagnosis", "hasAssessment", "isSubjectGroup"]
)
def test_controlled_terms_have_identifiers(
    attribute,
    runner,
    test_data_upload_path,
    default_pheno_output_path,
    load_test_json,
):
    runner.invoke(
        bagel,
        [
            "pheno",
            "--pheno",
            test_data_upload_path / "example_synthetic.tsv",
            "--dictionary",
            test_data_upload_path / "example_synthetic.json",
            "--output",
            default_pheno_output_path,
            "--name",
            "do not care name",
        ],
    )

    pheno = load_test_json(default_pheno_output_path)

    for sub in pheno["hasSamples"]:
        for ses in sub["hasSession"]:
            if attribute in ses.keys():
                value = ses.get(attribute)
                if not isinstance(value, list):
                    value = [value]
                assert all(
                    ["identifier" in entry for entry in value]
                ), f"{attribute}: did not have an identifier for subject {sub} and value {value}"


def test_controlled_term_classes_have_uri_type(
    runner, test_data_upload_path, default_pheno_output_path, load_test_json
):
    """Tests that classes specified as schemaKeys (@type) for subject-level attributes in a .jsonld are also defined in the context."""
    runner.invoke(
        bagel,
        [
            "pheno",
            "--pheno",
            test_data_upload_path / "example_synthetic.tsv",
            "--dictionary",
            test_data_upload_path / "example_synthetic.json",
            "--output",
            default_pheno_output_path,
            "--name",
            "do not care name",
        ],
    )

    pheno = load_test_json(test_data_upload_path / "example_synthetic.jsonld")

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
    "assessment, subject_idx",
    [
        (
            [{"identifier": "cogatlas:1234", "schemaKey": "Assessment"}],
            0,
        ),
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
    runner,
    test_data,
    default_pheno_output_path,
    load_test_json,
    assessment,
    subject_idx,
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
            default_pheno_output_path,
            "--name",
            "my_dataset_name",
        ],
    )

    pheno = load_test_json(default_pheno_output_path)

    assert assessment == pheno["hasSamples"][subject_idx]["hasSession"][0].get(
        "hasAssessment"
    )


@pytest.mark.parametrize(
    "expected_age, subject",
    [(20.5, 0), (pytest.approx(25.66, 0.01), 1)],
)
def test_cli_age_is_processed(
    runner,
    test_data,
    default_pheno_output_path,
    load_test_json,
    expected_age,
    subject,
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
            default_pheno_output_path,
            "--name",
            "my_dataset_name",
        ],
    )

    pheno = load_test_json(default_pheno_output_path)

    assert (
        expected_age == pheno["hasSamples"][subject]["hasSession"][0]["hasAge"]
    )


def test_output_includes_context(
    runner, test_data, default_pheno_output_path, load_test_json
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
            default_pheno_output_path,
            "--name",
            "my_dataset_name",
        ],
    )

    pheno = load_test_json(default_pheno_output_path)

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
    runner,
    test_data_upload_path,
    default_pheno_output_path,
    load_test_json,
    sub_id,
    missing_val_property,
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
            test_data_upload_path / "example_synthetic.tsv",
            "--dictionary",
            test_data_upload_path / "example_synthetic.json",
            "--output",
            default_pheno_output_path,
            "--name",
            "BIDS synthetic test",
        ],
    )

    pheno = load_test_json(default_pheno_output_path)
    for sub in pheno["hasSamples"]:
        if sub["hasLabel"] == sub_id:
            for entry in missing_val_property:
                assert (
                    sub.get(entry) is None
                ), f"{sub_id} output contains value for {entry} where annotated as missing"


def test_default_output_filename(runner, test_data_upload_path, tmp_path):
    """Tests that the default output filename is used correctly when --output is not set."""
    os.chdir(tmp_path)

    runner.invoke(
        bagel,
        [
            "pheno",
            "--pheno",
            test_data_upload_path / "example_synthetic.tsv",
            "--dictionary",
            test_data_upload_path / "example_synthetic.json",
            "--name",
            "BIDS synthetic test",
        ],
    )

    assert (tmp_path / "pheno.jsonld").exists()


@pytest.mark.parametrize(
    "overwrite_flag, expected_stdout",
    [
        ([], "already exists"),
        (["--overwrite"], "Saved output to"),
    ],
)
def test_overwrite_flag_behaviour(
    runner, test_data_upload_path, tmp_path, overwrite_flag, expected_stdout
):
    """Tests that an existing output file is only overwritten if --overwrite is used."""
    runner.invoke(
        bagel,
        [
            "pheno",
            "--pheno",
            test_data_upload_path / "example_synthetic.tsv",
            "--dictionary",
            test_data_upload_path / "example_synthetic.json",
            "--name",
            "BIDS synthetic test",
            "--output",
            tmp_path / "synthetic_dataset.jsonld",
        ],
    )

    overwrite_result = runner.invoke(
        bagel,
        [
            "pheno",
            "--pheno",
            test_data_upload_path / "example_synthetic.tsv",
            "--dictionary",
            test_data_upload_path / "example_synthetic.json",
            "--name",
            "BIDS synthetic test",
            "--output",
            tmp_path / "synthetic_dataset.jsonld",
        ]
        + overwrite_flag,
    )

    assert expected_stdout in overwrite_result.output


def test_pheno_sessions_have_correct_labels(
    runner,
    test_data_upload_path,
    tmp_path,
    load_test_json,
):
    """Check that sessions added to pheno_bids.jsonld have the expected labels."""
    runner.invoke(
        bagel,
        [
            "pheno",
            "--pheno",
            test_data_upload_path / "example_synthetic.tsv",
            "--dictionary",
            test_data_upload_path / "example_synthetic.json",
            "--name",
            "don't matter",
            "--portal",
            "https://www.google.com",
            "--output",
            tmp_path / "example_synthetic.jsonld",
        ],
    )

    pheno = load_test_json(tmp_path / "example_synthetic.jsonld")
    for sub in pheno["hasSamples"]:
        assert 2 == len(sub["hasSession"])

        phenotypic_session = [
            ses
            for ses in sub["hasSession"]
            if ses["schemaKey"] == "PhenotypicSession"
        ]
        assert 2 == len(phenotypic_session)

        # We also need to make sure that we do not have duplicate phenotypic session labels
        assert set(["ses-01", "ses-02"]) == set(
            [ses["hasLabel"] for ses in phenotypic_session]
        )


def test_pheno_session_created_for_missing_session_column(
    runner,
    test_data,
    default_pheno_output_path,
    load_test_json,
):
    """
    Check that a new phenotypic session is created with an appropriate label when there are subject data
    in the phenotypic TSV but no column about sessions.
    """
    runner.invoke(
        bagel,
        [
            "pheno",
            "--pheno",
            test_data / "example17.tsv",
            "--dictionary",
            test_data / "example17.json",
            "--name",
            "Missing session column dataset",
            "--output",
            default_pheno_output_path,
        ],
    )

    pheno = load_test_json(default_pheno_output_path)
    for sub in pheno["hasSamples"]:
        assert 1 == len(sub["hasSession"])
        assert sub["hasSession"][0]["schemaKey"] == "PhenotypicSession"
        assert sub["hasSession"][0]["hasLabel"] == "ses-unnamed"


def test_multicolumn_diagnosis_annot_is_handled(
    runner,
    test_data,
    default_pheno_output_path,
    load_test_json,
):
    """Test that when a subject has a non-healthy control diagnosis across multiple columns, they are all correctly parsed and stored as part of the subject's data."""
    runner.invoke(
        bagel,
        [
            "pheno",
            "--pheno",
            test_data / "example19.tsv",
            "--dictionary",
            test_data / "example19.json",
            "--name",
            "Multi-column annotation dataset",
            "--output",
            default_pheno_output_path,
        ],
    )

    pheno = load_test_json(default_pheno_output_path)
    # Check the subject with only disease diagnoses
    sub_01_diagnoses = [
        diagnosis["identifier"]
        for diagnosis in pheno["hasSamples"][0]["hasSession"][0][
            "hasDiagnosis"
        ]
    ]
    assert sub_01_diagnoses == ["snomed:49049000", "snomed:724761004"]


@pytest.mark.parametrize("sub_idx", [1, 2])
def test_multicolumn_diagnosis_annot_with_healthy_control_is_handled(
    runner, test_data, default_pheno_output_path, load_test_json, sub_idx
):
    """
    Test that when there are multiple columns about diagnosis and a subject has a healthy control status in one column,
    the healthy control status is used and any other diagnoses are ignored.
    """
    runner.invoke(
        bagel,
        [
            "pheno",
            "--pheno",
            test_data / "example19.tsv",
            "--dictionary",
            test_data / "example19.json",
            "--name",
            "Multi-column annotation dataset",
            "--output",
            default_pheno_output_path,
        ],
    )

    pheno = load_test_json(default_pheno_output_path)
    sub_with_healthy_control_annotation = pheno["hasSamples"][sub_idx][
        "hasSession"
    ][0]

    assert "hasDiagnosis" not in sub_with_healthy_control_annotation.keys()
    assert (
        sub_with_healthy_control_annotation["isSubjectGroup"]["identifier"]
        == "ncit:C94342"
    )


def test_pheno_command_succeeds_with_short_option_names(
    runner,
    test_data,
    default_pheno_output_path,
):
    """Test that the pheno command does not error when invoked with short option names."""
    example = "example2"
    result = runner.invoke(
        bagel,
        [
            "pheno",
            "-t",
            test_data / f"{example}.tsv",
            "-d",
            test_data / f"{example}.json",
            "-o",
            default_pheno_output_path,
            "-n",
            "Test dataset",
        ],
    )
    assert result.exit_code == 0, f"Errored out. STDOUT: {result.output}"
    assert (
        default_pheno_output_path
    ).exists(), "The pheno.jsonld output was not created."
