import os

import pytest

from bagel import mappings
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
    temp_output_jsonld_path,
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
                temp_output_jsonld_path,
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
                temp_output_jsonld_path,
                "--name",
                "do not care name",
            ],
        )
    assert result.exit_code == 0, f"Errored out. STDOUT: {result.output}"
    assert (
        temp_output_jsonld_path
    ).exists(), "The pheno.jsonld output was not created."


@pytest.mark.parametrize(
    "example,expected_message",
    [
        (
            "example3",
            ["must contain at least one column with Neurobagel annotations"],
        ),
        (
            "example_invalid",
            ["not a valid Neurobagel data dictionary"],
        ),
        (
            "example7",
            ["incompatible", "missing from the phenotypic table: ['group']"],
        ),
        ("example8", ["more than one column"]),
        (
            "example9",
            [
                "missing annotations in the data dictionary",
                "'group': ['UNANNOTATED']",
            ],
        ),
        (
            "example11",
            [
                "missing values in participant or session ID columns",
                "rows (header row is 1): [2, 4]",
            ],
        ),
        (
            "example22",
            [
                "missing values in participant or session ID columns",
                "rows (header row is 1): [6, 7, 8]",
            ],
        ),
        (
            "example15",
            [
                "must contain at least one column annotated as being about participant ID"
            ],
        ),
        (
            "example1",
            [
                "duplicate participant IDs or duplicate combinations of participant and session IDs"
            ],
        ),
        (
            "example18",
            [
                "duplicate participant IDs or duplicate combinations of participant and session IDs"
            ],
        ),
        (
            "example5",
            [
                "unsupported vocabulary namespace prefixes",
                "['cogatlas', 'unknownvocab']",
                "vocabularies have been deprecated",
                "['cogatlas']",
            ],
        ),
    ],
)
def test_invalid_inputs_are_handled_gracefully(
    runner,
    test_data,
    temp_output_jsonld_path,
    example,
    expected_message,
    caplog,
    propagate_errors,
):
    """Assures that we handle expected user errors in the input files gracefully"""
    result = runner.invoke(
        bagel,
        [
            "pheno",
            "--pheno",
            test_data / f"{example}.tsv",
            "--dictionary",
            test_data / f"{example}.json",
            "--output",
            temp_output_jsonld_path,
            "--name",
            "do not care name",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code != 0
    assert len(caplog.records) == 1
    for substring in expected_message:
        assert substring in caplog.text


@pytest.mark.parametrize(
    # See also https://docs.pydantic.dev/latest/api/networks/#pydantic.networks.HttpUrl for v2 URL requirements
    "portal",
    [
        "openneuro.org/datasets/ds002080",
        "not a url",
        "www.github.com/mycoolrepo/mycooldataset",
    ],
)
def test_invalid_portal_uris_produces_error(
    runner,
    test_data,
    temp_output_jsonld_path,
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
            temp_output_jsonld_path,
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


def test_multiple_columns_about_single_column_variable_raises_warning(
    runner,
    test_data,
    temp_output_jsonld_path,
    caplog,
    propagate_warnings,
):
    """
    Test that an informative warning is logged when multiple columns in the phenotypic file
    have been annotated as being about age, sex, or subject group.
    """
    runner.invoke(
        bagel,
        [
            "pheno",
            "--pheno",
            test_data / "example20.tsv",
            "--dictionary",
            test_data / "example20.json",
            "--output",
            temp_output_jsonld_path,
            "--name",
            "Multiple age/sex/subject group columns dataset",
        ],
        catch_exceptions=False,
    )

    assert len(caplog.records) == 3
    for warn_substring in [
        "more than one column about age",
        "more than one column about sex",
        "more than one column about subject group",
    ]:
        assert warn_substring in caplog.text


def test_missing_bids_levels_raises_warning(
    runner,
    test_data,
    temp_output_jsonld_path,
    caplog,
    propagate_warnings,
):
    runner.invoke(
        bagel,
        [
            "pheno",
            "--pheno",
            test_data / "example12.tsv",
            "--dictionary",
            test_data / "example12.json",
            "--output",
            temp_output_jsonld_path,
            "--name",
            "testing dataset",
        ],
        catch_exceptions=False,
    )

    assert len(caplog.records) == 1
    assert (
        "looks categorical but lacks a BIDS 'Levels' attribute" in caplog.text
    )


def test_bids_neurobagel_levels_mismatch_raises_warning(
    runner,
    test_data,
    temp_output_jsonld_path,
    caplog,
    propagate_warnings,
):
    runner.invoke(
        bagel,
        [
            "pheno",
            "--pheno",
            test_data / "example13.tsv",
            "--dictionary",
            test_data / "example13.json",
            "--output",
            temp_output_jsonld_path,
            "--name",
            "testing dataset",
        ],
        catch_exceptions=False,
    )

    assert len(caplog.records) == 1
    assert all(
        warn_substring in caplog.text
        for warn_substring in [
            "columns with mismatched levels",
            "['pheno_sex']",
        ]
    )


def test_unused_missing_values_raises_warning(
    runner,
    test_data,
    temp_output_jsonld_path,
    caplog,
    propagate_warnings,
):
    """
    Tests that an informative warning is logged when annotated missing values are not found in the
    phenotypic file.
    """
    runner.invoke(
        bagel,
        [
            "pheno",
            "--pheno",
            test_data / "example10.tsv",
            "--dictionary",
            test_data / "example10.json",
            "--output",
            temp_output_jsonld_path,
            "--name",
            "testing dataset",
        ],
        catch_exceptions=False,
    )

    assert len(caplog.records) == 1
    for warn_substring in [
        "missing values in the data dictionary were not found",
        "'group': ['NOT IN TSV']",
        "'tool_item1': ['NOT IN TSV 1', 'NOT IN TSV 2']",
        "'tool_item2': ['NOT IN TSV 1', 'NOT IN TSV 2']",
    ]:
        assert warn_substring in caplog.text


@pytest.mark.parametrize(
    "pheno_file,dictionary_file,expected_err",
    [
        ("example2.csv", "example2.json", ["not a .tsv file"]),
        ("example2.txt", "example2.json", ["not a .tsv file"]),
        (
            "example16.tsv",
            "example16.json",
            [
                "not a valid Neurobagel phenotypic table",
                "resembles a .csv file",
            ],
        ),
    ],
)
def test_providing_non_tsv_file_raises_error(
    pheno_file,
    dictionary_file,
    expected_err,
    runner,
    test_data,
    tmp_path,
    temp_output_jsonld_path,
    caplog,
    propagate_errors,
):
    """
    Providing a non .tsv file or a file with .tsv extension but incorrect encoding
    should be handled with an informative error.
    """
    result = runner.invoke(
        bagel,
        [
            "pheno",
            "--pheno",
            test_data / pheno_file,
            "--dictionary",
            test_data / dictionary_file,
            "--output",
            temp_output_jsonld_path,
            "--name",
            "testing dataset",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code != 0
    assert len(caplog.records) == 1
    for substring in expected_err:
        assert substring in caplog.text


def test_output_file_contains_dataset_level_attributes(
    runner, test_data, temp_output_jsonld_path, load_test_json
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
            temp_output_jsonld_path,
            "--name",
            "my_dataset_name",
            "--portal",
            "http://my_dataset_site.com",
        ],
    )

    pheno = load_test_json(temp_output_jsonld_path)

    assert pheno.get("hasLabel") == "my_dataset_name"
    assert pheno.get("hasPortalURI") == "http://my_dataset_site.com"


def test_diagnosis_and_control_status_handled(
    runner, test_data, temp_output_jsonld_path, load_test_json
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
            temp_output_jsonld_path,
            "--name",
            "my_dataset_name",
        ],
    )

    pheno = load_test_json(temp_output_jsonld_path)

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
    temp_output_jsonld_path,
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
            temp_output_jsonld_path,
            "--name",
            "do not care name",
        ],
    )

    pheno = load_test_json(temp_output_jsonld_path)

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
    runner, test_data_upload_path, temp_output_jsonld_path, load_test_json
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
            temp_output_jsonld_path,
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
            [{"identifier": "snomed:1234", "schemaKey": "Assessment"}],
            0,
        ),
        (None, 1),
        (
            [
                {"identifier": "snomed:1234", "schemaKey": "Assessment"},
                {"identifier": "snomed:4321", "schemaKey": "Assessment"},
            ],
            2,
        ),
    ],
)
def test_assessment_data_are_parsed_correctly(
    runner,
    test_data,
    temp_output_jsonld_path,
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
            temp_output_jsonld_path,
            "--name",
            "my_dataset_name",
        ],
    )

    pheno = load_test_json(temp_output_jsonld_path)

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
    temp_output_jsonld_path,
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
            temp_output_jsonld_path,
            "--name",
            "my_dataset_name",
        ],
    )

    pheno = load_test_json(temp_output_jsonld_path)

    assert (
        expected_age == pheno["hasSamples"][subject]["hasSession"][0]["hasAge"]
    )


def test_output_includes_context(
    runner, test_data, temp_output_jsonld_path, load_test_json
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
            temp_output_jsonld_path,
            "--name",
            "my_dataset_name",
        ],
    )

    pheno = load_test_json(temp_output_jsonld_path)

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
    temp_output_jsonld_path,
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
            temp_output_jsonld_path,
            "--name",
            "BIDS synthetic test",
        ],
    )

    pheno = load_test_json(temp_output_jsonld_path)
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
    "overwrite_flag, should_show_output_exists_message, should_show_output_saved_message",
    [
        ([], True, False),
        (["--overwrite"], False, True),
    ],
)
def test_overwrite_flag_behaviour(
    runner,
    test_data_upload_path,
    tmp_path,
    overwrite_flag,
    should_show_output_exists_message,
    should_show_output_saved_message,
    caplog,
    propagate_info,
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
    # We need to clear the captured logs here so we can assert over only the logs produced by the following invocation
    caplog.clear()

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

    was_output_exists_message_shown = (
        "already exists" in overwrite_result.output
    )
    was_output_saved_message_shown = "Saved output to" in caplog.text

    assert was_output_exists_message_shown == should_show_output_exists_message
    assert was_output_saved_message_shown == should_show_output_saved_message


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
    temp_output_jsonld_path,
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
            temp_output_jsonld_path,
        ],
    )

    pheno = load_test_json(temp_output_jsonld_path)
    for sub in pheno["hasSamples"]:
        assert 1 == len(sub["hasSession"])
        assert sub["hasSession"][0]["schemaKey"] == "PhenotypicSession"
        assert sub["hasSession"][0]["hasLabel"] == "ses-unnamed"


def test_multicolumn_diagnosis_annot_is_handled(
    runner,
    test_data,
    temp_output_jsonld_path,
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
            temp_output_jsonld_path,
        ],
    )

    pheno = load_test_json(temp_output_jsonld_path)
    # Check the subject with only disease diagnoses
    sub_01_diagnoses = [
        diagnosis["identifier"]
        for diagnosis in pheno["hasSamples"][0]["hasSession"][0][
            "hasDiagnosis"
        ]
    ]
    assert sub_01_diagnoses == ["snomed:724761004", "snomed:370143000"]


def test_healthy_control_subject_with_diagnosis_is_handled(
    runner, test_data, temp_output_jsonld_path, load_test_json
):
    """
    Test that when a subject has both a diagnosis and a healthy control status,
    both are correctly parsed and stored as part of the subject's data.
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
            temp_output_jsonld_path,
        ],
    )

    pheno = load_test_json(temp_output_jsonld_path)

    healthy_control_sub_with_diagnosis = next(
        sub for sub in pheno["hasSamples"] if sub["hasLabel"] == "sub-03"
    )
    healthy_control_sub_with_diagnosis = healthy_control_sub_with_diagnosis[
        "hasSession"
    ][0]

    assert (
        healthy_control_sub_with_diagnosis["isSubjectGroup"]["identifier"]
        == "ncit:C94342"
    )
    assert len(healthy_control_sub_with_diagnosis["hasDiagnosis"]) == 1
    assert (
        healthy_control_sub_with_diagnosis["hasDiagnosis"][0]["identifier"]
        == "snomed:21897009"
    )


def test_pheno_command_succeeds_with_short_option_names(
    runner,
    test_data,
    temp_output_jsonld_path,
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
            temp_output_jsonld_path,
            "-n",
            "Test dataset",
        ],
    )
    assert result.exit_code == 0, f"Errored out. STDOUT: {result.output}"
    assert (
        temp_output_jsonld_path
    ).exists(), "The pheno.jsonld output was not created."


@pytest.mark.parametrize(
    "invalid_dataset_name",
    [
        "",
        "    ",
        "\n\t",
    ],
)
def test_empty_string_dataset_name_raises_error(
    runner,
    test_data_upload_path,
    temp_output_jsonld_path,
    invalid_dataset_name,
    disable_rich_markup,
):
    """Ensure that provided dataset names cannot be empty strings or only contain whitespace."""
    result = runner.invoke(
        bagel,
        [
            "pheno",
            "--pheno",
            test_data_upload_path / "example_synthetic.tsv",
            "--dictionary",
            test_data_upload_path / "example_synthetic.json",
            "--output",
            temp_output_jsonld_path,
            "--name",
            invalid_dataset_name,
        ],
        catch_exceptions=False,
    )

    assert result.exit_code != 0
    assert "cannot be an empty string" in result.output


def test_backup_used_with_warning_when_request_for_config_namespaces_fails(
    runner,
    test_data_upload_path,
    temp_output_jsonld_path,
    caplog,
    propagate_warnings,
    monkeypatch,
    disable_rich_markup,
):
    """
    Test that when config namespaces cannot be fetched from the remote source,
    the pheno command raises a warning and uses the backup configuration.
    """
    monkeypatch.setattr(
        mappings, "CONFIG_NAMESPACES_FETCHING_ERR", "Network unreachable"
    )

    result = runner.invoke(
        bagel,
        [
            "pheno",
            "--pheno",
            test_data_upload_path / "example_synthetic.tsv",
            "--dictionary",
            test_data_upload_path / "example_synthetic.json",
            "--config",
            "neuroBagel",
            "--name",
            "Config test",
            "--output",
            temp_output_jsonld_path,
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert temp_output_jsonld_path.exists()
    assert len(caplog.records) == 1
    assert "Using a packaged backup configuration" in caplog.text
