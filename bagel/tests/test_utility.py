from collections import Counter
from pathlib import Path

import pandas as pd
import pytest
import typer
from bids import BIDSLayout

import bagel.bids_utils as butil
import bagel.derivatives_utils as dutil
import bagel.file_utils as futil
import bagel.pheno_utils as putil
from bagel import mappings, models
from bagel.utility import (
    generate_context,
    get_subject_instances,
    get_subs_missing_from_pheno_data,
)


@pytest.fixture
def get_test_context():
    """Generate an @context dictionary to test against."""
    return generate_context()


@pytest.fixture
def get_values_by_key():
    """
    Get values of all instances of a specified key in a dictionary. Will also look inside lists of dictionaries and nested dictionaries.
    """

    def _find_by_key(data, target):
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    yield from _find_by_key(value, target)
                elif key == target:
                    yield value
        elif isinstance(data, list):
            for item in data:
                yield from _find_by_key(item, target)

    return _find_by_key


def test_all_used_namespaces_have_urls(
    get_test_context, get_values_by_key, load_test_json, test_data_upload_path
):
    """Test that all namespace prefixes used in a comprehensive data dictionary have a corresponding URL in the @context."""
    data_dict = load_test_json(
        test_data_upload_path / "example_synthetic.json"
    )

    prefixes = list(
        map(
            lambda term: term.split(":")[0],
            get_values_by_key(data_dict, "TermURL"),
        )
    )

    # add nidm to the list of tested prefixes manually since it is the only one not present in the data dictionary
    # but is used automatically during the bids step
    for prefix in set(prefixes + ["nidm"]):
        assert (
            prefix in get_test_context["@context"]
        ), f"The namespace '{prefix}' was used in the data dictionary, but was not defined in the @context."


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
        putil.validate_data_dict(partial_data_dict)

    for substring in [
        "not a valid Neurobagel data dictionary",
        invalid_column_name,
    ]:
        assert substring in str(e.value)


def test_get_columns_that_are_about_concept(test_data, load_test_json):
    """Test that matching annotated columns are returned as a list,
    and that empty list is returned if nothing matches"""
    data_dict = load_test_json(test_data / "example14.json")

    assert ["participant_id"] == putil.get_columns_about(
        data_dict, concept=mappings.NEUROBAGEL["participant"]
    )
    assert [] == putil.get_columns_about(
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
    result = putil.get_annotated_columns(example)[0]
    assert result[0] == "participant_id"
    assert result[1] == example["participant_id"]


def test_map_categories_to_columns(test_data, load_test_json):
    """Test that inverse mapping of concepts to columns is correctly created"""
    data_dict = load_test_json(test_data / "example2.json")

    result = putil.map_categories_to_columns(data_dict)

    assert {"participant", "session", "sex"}.issubset(result.keys())
    assert ["participant_id"] == result["participant"]
    assert ["session_id"] == result["session"]
    assert ["sex"] == result["sex"]


@pytest.mark.parametrize(
    "tool, columns",
    [
        ("cogatlas:1234", ["tool_item1", "tool_item2"]),
        ("cogatlas:4321", ["other_tool_item1"]),
    ],
)
def test_map_tools_to_columns(test_data, load_test_json, tool, columns):
    data_dict = load_test_json(test_data / "example6.json")

    result = putil.map_tools_to_columns(data_dict)

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

    assert expected_values == putil.get_transformed_values(
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
    result = putil.is_column_categorical(column="column", data_dict=example)

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

    assert putil.is_missing_value(value, column, test_data_dict) is expected


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
        putil.are_any_available(
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
    assert expected_indices == putil.get_rows_with_empty_strings(
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
    ],
)
def test_age_gets_converted(raw_age, expected_age, heuristic):
    assert expected_age == putil.transform_age(raw_age, heuristic)


@pytest.mark.parametrize(
    "raw_age, incorrect_heuristic",
    [
        ("11,0", "nb:FromFloat"),
        ("11.0", "nb:FromISO8601"),
        ("20-30", "nb:FromBounded"),
    ],
)
def test_incorrect_age_heuristic(raw_age, incorrect_heuristic):
    """Given an age transformation that does not match the type of age value provided, returns an informative error."""
    with pytest.raises(ValueError) as e:
        putil.transform_age(raw_age, incorrect_heuristic)

    assert (
        f"problem with applying the age transformation: {incorrect_heuristic}."
        in str(e.value)
    )


def test_invalid_age_heuristic():
    """Given an age transformation that is not recognized, returns an informative ValueError."""
    with pytest.raises(ValueError) as e:
        putil.transform_age("11,0", "nb:birthyear")

    assert "unrecognized age transformation: nb:birthyear" in str(e.value)


# TODO: See if we can remove this test: it's a little hard to maintain and
# essentially replicates the logic of the function being tested
# Instead, see test_all_used_namespaces_have_urls and test_used_namespaces_in_context
@pytest.mark.parametrize(
    "model, attributes",
    [
        ("Bagel", ["identifier"]),
        ("ControlledTerm", ["identifier", "schemaKey"]),
        ("Sex", ["schemaKey"]),
        ("Diagnosis", ["schemaKey"]),
        ("SubjectGroup", ["schemaKey"]),
        ("Assessment", ["schemaKey"]),
        ("Image", ["schemaKey"]),
        ("Acquisition", ["hasContrastType", "schemaKey"]),
        ("Pipeline", ["schemaKey"]),
        (
            "CompletedPipeline",
            ["hasPipelineVersion", "hasPipelineName", "schemaKey"],
        ),
        ("Session", ["hasLabel"]),
        (
            "PhenotypicSession",
            [
                "hasAge",
                "hasSex",
                "isSubjectGroup",
                "hasDiagnosis",
                "hasAssessment",
                "schemaKey",
            ],
        ),
        (
            "ImagingSession",
            [
                "hasFilePath",
                "hasAcquisition",
                "hasCompletedPipeline",
                "schemaKey",
            ],
        ),
        (
            "Subject",
            [
                "hasLabel",
                "hasSession",
                "schemaKey",
            ],
        ),
        (
            "Dataset",
            [
                "hasLabel",
                "hasPortalURI",
                "hasSamples",
                "schemaKey",
            ],
        ),
    ],
)
def test_generate_context(get_test_context, model, attributes):
    """Test that each model and its set of attributes have corresponding entries in @context."""
    assert model in get_test_context["@context"]
    for attribute in attributes:
        assert attribute in get_test_context["@context"]


@pytest.mark.parametrize(
    "bids_dir",
    ["synthetic", "ds000248"],
)
def test_get_bids_subjects_simple(bids_path, bids_dir):
    """Test that get_bids_subjects_simple() correctly extracts subject IDs from a BIDS directory."""
    bids_subject_list = butil.get_bids_subjects_simple(bids_path / bids_dir)
    expected_subjects = [
        f"sub-{sub_id}"
        for sub_id in BIDSLayout(
            bids_path / bids_dir, validate=True
        ).get_subjects()
    ]
    assert sorted(bids_subject_list) == sorted(expected_subjects)


@pytest.mark.parametrize(
    "bids_list, expected_bids_exclusive_subs",
    [
        (["sub-01", "sub-02", "sub-03"], []),
        (
            ["sub-01", "sub-02", "sub-03", "sub-04", "sub-05"],
            ["sub-04", "sub-05"],
        ),
        (
            ["sub-cbm001", "sub-cbm002", "sub-cbm003"],
            ["sub-cbm001", "sub-cbm002", "sub-cbm003"],
        ),
        (
            ["sub-pd123", "sub-pd234"],
            ["sub-pd123", "sub-pd234"],
        ),
    ],
)
def test_get_subjects_missing_from_pheno_data(
    bids_list, expected_bids_exclusive_subs
):
    """
    Given a list of BIDS subject IDs, test that IDs not found in the phenotypic subject list are returned.
    """
    pheno_list = ["sub-01", "sub-02", "sub-03", "sub-PD123", "sub-PD234"]
    bids_exclusive_subs = get_subs_missing_from_pheno_data(
        pheno_subjects=pheno_list, subjects=bids_list
    )

    # We sort the list for comparison since the order of the missing subjects is not guaranteed
    # due to using set operations
    assert sorted(bids_exclusive_subs) == expected_bids_exclusive_subs


@pytest.mark.parametrize(
    "bids_dir, acquisitions, bids_session",
    [
        (
            "synthetic",
            {"nidm:T1Weighted": 1, "nidm:FlowWeighted": 3},
            "01",
        ),
        (
            "ds001",
            {
                "nidm:T2Weighted": 1,
                "nidm:T1Weighted": 1,
                "nidm:FlowWeighted": 3,
            },
            None,
        ),
        ("eeg_ds000117", {"nidm:T1Weighted": 1}, None),
    ],
)
def test_create_acquisitions(bids_path, bids_dir, acquisitions, bids_session):
    """Given a BIDS dataset, creates a list of acquisitions matching the image files found on disk."""
    image_list = butil.create_acquisitions(
        layout=BIDSLayout(bids_path / bids_dir, validate=True),
        bids_sub_id="01",
        session=bids_session,
    )

    image_counts = Counter(
        [image.hasContrastType.identifier for image in image_list]
    )

    for contrast, count in acquisitions.items():
        assert image_counts[contrast] == count


@pytest.mark.parametrize(
    "bids_sub_id, session",
    [("01", "01"), ("02", "02"), ("03", "01")],
)
def test_get_session_path_when_session_exists(bids_sub_id, session):
    """
    Test that given a subject and session ID (i.e. when BIDS session layer exists for dataset),
    get_session_path() returns a path to the subject's session directory.
    """
    bids_dir = Path(__file__).parent / "../../bids-examples/synthetic"
    session_path = butil.get_session_path(
        layout=BIDSLayout(bids_dir, validate=True),
        bids_dir=bids_dir,
        bids_sub_id=bids_sub_id,
        session=session,
    )

    assert f"sub-{bids_sub_id}" in session_path
    assert f"ses-{session}" in session_path
    assert Path(session_path).is_absolute()
    assert Path(session_path).is_dir()


@pytest.mark.parametrize("bids_sub_id", ["01", "03", "05"])
def test_get_session_path_when_session_missing(bids_sub_id):
    """
    Test that given only a subject ID (i.e., when BIDS session layer is missing for dataset),
    get_session_path() returns the path to the subject directory.
    """
    bids_dir = Path(__file__).parent / "../../bids-examples/ds001"
    session_path = butil.get_session_path(
        layout=BIDSLayout(bids_dir, validate=True),
        bids_dir=bids_dir,
        bids_sub_id=bids_sub_id,
        session=None,
    )

    assert session_path.endswith(f"sub-{bids_sub_id}")
    assert Path(session_path).is_absolute()
    assert Path(session_path).is_dir()


@pytest.mark.parametrize(
    "unreadable_json,expected_message",
    [
        ("example_iso88591.json", "Failed to decode the input file"),
        ("example_invalid_json.json", "not valid JSON"),
    ],
)
def test_failed_json_reading_raises_informative_error(
    test_data, unreadable_json, expected_message, capsys
):
    """Test that when there is an issue reading an input JSON file, the CLI exits with an informative error message."""
    with pytest.raises(typer.Exit):
        futil.load_json(test_data / unreadable_json)
    captured = capsys.readouterr()

    assert expected_message in captured.err


def test_unsupported_tsv_encoding_raises_informative_error(test_data, capsys):
    """Test that given an input phenotypic TSV with an unsupported encoding, the CLI exits with an informative error message."""
    with pytest.raises(typer.Exit):
        futil.load_tabular(test_data / "example_iso88591.tsv")
    captured = capsys.readouterr()

    assert "Failed to decode the input file" in captured.err


def test_get_subject_instances():
    """Test that subjects are correctly extracted from a Neurobagel dataset instance."""
    dataset = models.Dataset(
        hasLabel="test_dataset",
        hasSamples=[
            models.Subject(
                hasLabel="sub-01",
                hasSession=[
                    models.PhenotypicSession(
                        hasLabel="ses-01",
                        hasAge=26,
                    ),
                ],
            ),
            models.Subject(
                hasLabel="sub-02",
                hasSession=[
                    models.PhenotypicSession(
                        hasLabel="ses-01",
                        hasAge=30,
                    ),
                ],
            ),
        ],
    )

    subjects = get_subject_instances(dataset)
    assert list(subjects.keys()) == ["sub-01", "sub-02"]


def test_pipeline_uris_are_loaded():
    """Test that pipeline URIs are loaded from the pipeline-catalog submodule."""

    pipeline_dict = mappings.get_pipeline_uris()
    assert all(
        ((mappings.NP.pf in pipe_uri) and (" " not in pipe_uri))
        for pipe_uri in pipeline_dict.values()
    )


def test_pipeline_versions_are_loaded():
    """Test that pipeline versions are loaded from the pipeline-catalog submodule."""

    pipeline_dict = mappings.get_pipeline_versions()
    assert all(
        isinstance(pipe_versions, list) and len(pipe_versions) > 0
        for pipe_versions in pipeline_dict.values()
    )


@pytest.mark.parametrize(
    "pipelines, unrecog_pipelines",
    [
        (["fmriprep", "pipeline1"], ["pipeline1"]),
        (["pipelineA", "pipelineB"], ["pipelineA", "pipelineB"]),
    ],
)
def test_unrecognized_pipeline_names_raise_error(pipelines, unrecog_pipelines):
    """Test that pipeline names not found in the pipeline catalog raise an informative error."""
    with pytest.raises(LookupError) as e:
        dutil.check_pipelines_are_recognized(pipelines)

    assert all(
        substr in str(e.value)
        for substr in ["unrecognized pipelines"] + unrecog_pipelines
    )


@pytest.mark.parametrize(
    "fmriprep_versions, unrecog_versions",
    [
        (["20.2.7", "vA.B"], ["vA.B"]),
        (["C.D.E", "F.G.H"], ["C.D.E", "F.G.H"]),
    ],
)
def test_unrecognized_pipeline_versions_raise_error(
    fmriprep_versions, unrecog_versions
):
    """Test that versions of a pipeline not found in the pipeline catalog raise an informative error."""
    with pytest.raises(LookupError) as e:
        dutil.check_pipeline_versions_are_recognized(
            "fmriprep", fmriprep_versions
        )

    assert all(
        substr in str(e.value)
        for substr in ["unrecognized fmriprep versions"] + unrecog_versions
    )


def test_get_imaging_session_instances():
    """Test that get_imaging_session_instances() correctly returns existing imaging sessions for a given subject."""
    example_subject_jsonld = {
        "identifier": "nb:34ec1e2d-9a81-4a50-bcd0-eb22c88d11e1",
        "hasLabel": "sub-01",
        "hasSession": [
            {
                "identifier": "nb:85c7473c-6122-4999-ad3b-5cd57a883c87",
                "hasLabel": "ses-01",
                "hasAge": 34.1,
                "hasSex": {
                    "identifier": "snomed:248152002",
                    "schemaKey": "Sex",
                },
                "schemaKey": "PhenotypicSession",
            },
            {
                "identifier": "nb:eb57d0c1-fb96-4c04-8c16-1f29f7f40db4",
                "hasLabel": "ses-02",
                "hasAge": 35.3,
                "hasSex": {
                    "identifier": "snomed:248152002",
                    "schemaKey": "Sex",
                },
                "schemaKey": "PhenotypicSession",
            },
            {
                "identifier": "nb:e67fd08b-9bf9-4ed8-b4cc-d0142cd27789",
                "hasLabel": "ses-im01",
                "hasFilePath": "/data/neurobagel/bagel-cli/bids-examples/synthetic/sub-01/ses-01",
                "hasAcquisition": [
                    {
                        "identifier": "nb:5dc2e11e-4f7a-4b0e-9488-843f0a607f4b",
                        "hasContrastType": {
                            "identifier": "nidm:T1Weighted",
                            "schemaKey": "Image",
                        },
                        "schemaKey": "Acquisition",
                    },
                ],
                "schemaKey": "ImagingSession",
            },
        ],
        "schemaKey": "Subject",
    }
    example_subject = models.Subject(**example_subject_jsonld)
    imaging_sessions = dutil.get_imaging_session_instances(example_subject)

    assert list(imaging_sessions.keys()) == ["ses-im01"]


def test_create_completed_pipelines():
    """
    Test that completed pipelines for a subject-session are accurately identified
    based on completion status of all pipeline steps.
    """
    sub_ses_data = [
        [
            "01",
            "sub-01",
            "01",
            "ses-01",
            "fmriprep",
            "20.2.7",
            "step1",
            "SUCCESS",
        ],
        [
            "01",
            "sub-01",
            "01",
            "ses-01",
            "fmriprep",
            "20.2.7",
            "step2",
            "FAIL",
        ],
        [
            "01",
            "sub-01",
            "01",
            "ses-01",
            "fmriprep",
            "23.1.3",
            "default",
            "SUCCESS",
        ],
    ]
    example_ses_proc_df = pd.DataFrame.from_records(
        columns=[
            "participant_id",
            "bids_participant",
            "session_id",
            "bids_session",
            "pipeline_name",
            "pipeline_version",
            "pipeline_step",
            "status",
        ],
        data=sub_ses_data,
    )
    completed_pipelines = dutil.create_completed_pipelines(example_ses_proc_df)

    assert len(completed_pipelines) == 1
    assert (
        completed_pipelines[0].hasPipelineName.identifier
        == f"{mappings.NP.pf}:fmriprep"
    )
    assert completed_pipelines[0].hasPipelineVersion == "23.1.3"


def test_used_namespaces_in_context(test_data_upload_path, load_test_json):
    """
    Test that all namespaces used internally by the CLI for JSONLD dataset creation are defined
    in the @context of reference example .jsonld files.
    """
    # Fetch all .jsonld files to avoid having to add a test parameter whenever we add a new JSONLD
    example_jsonld_files = list(test_data_upload_path.rglob("*.jsonld"))
    for jsonld in example_jsonld_files:
        jsonld_context = load_test_json(test_data_upload_path / jsonld)[
            "@context"
        ]

        for ns in mappings.ALL_NAMESPACES:
            assert (
                ns.pf in jsonld_context.keys()
            ), f"The namespace '{ns.pf}' was not found in the @context of {jsonld}."
