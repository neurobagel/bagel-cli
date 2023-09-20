from collections import Counter
from contextlib import nullcontext as does_not_raise
from pathlib import Path

import pandas as pd
import pytest
from bids import BIDSLayout

import bagel.bids_utils as butil
import bagel.pheno_utils as putil
from bagel import mappings


@pytest.fixture
def get_test_context():
    """Generate an @context dictionary to test against."""
    return putil.generate_context()


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


def test_schema_invalid_column_raises_error():
    partial_data_dict = (
        {
            "participant_id": {
                "Description": "A participant ID",
                "Annotations": {
                    "IsAbout": {
                        "TermURL": "nb:ParticipantID",
                        "Label": "Unique participant identifier",
                    }
                },
            },
            "sex": {
                "Description": "Participant sex",
                "Annotations": {"IsAbout": {"TermURL": "nb:Sex", "Label": ""}},
            },
        },
    )

    with pytest.raises(ValueError) as e:
        putil.validate_data_dict(partial_data_dict)

    assert "not a valid Neurobagel data dictionary" in str(e.value)


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


def test_get_transformed_categorical_value(test_data, load_test_json):
    """Test that the correct transformed value is returned for a categorical variable"""
    data_dict = load_test_json(test_data / "example2.json")
    pheno = pd.read_csv(test_data / "example2.tsv", sep="\t")

    assert "snomed:248153007" == putil.get_transformed_values(
        columns=["sex"],
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
        putil.are_not_missing(test_columns, pheno.iloc[subject_idx], data_dict)
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
        ("11.0", 11.0, "nb:float"),
        ("11", 11.0, "nb:int"),
        ("11,0", 11.0, "nb:euro"),
        ("90+", 90.0, "nb:bounded"),
        ("20Y6M", 20.5, "nb:iso8601"),
        ("P20Y6M", 20.5, "nb:iso8601"),
        ("20Y9M", 20.75, "nb:iso8601"),
    ],
)
def test_age_gets_converted(raw_age, expected_age, heuristic):
    assert expected_age == putil.transform_age(raw_age, heuristic)


@pytest.mark.parametrize(
    "raw_age, incorrect_heuristic",
    [
        ("11,0", "nb:float"),
        ("11.0", "nb:iso8601"),
        ("20-30", "nb:bounded"),
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


@pytest.mark.parametrize(
    "model, attributes",
    [
        ("Bagel", ["identifier"]),
        ("Sex", ["identifier", "schemaKey"]),
        ("Diagnosis", ["identifier", "schemaKey"]),
        ("SubjectGroup", ["identifier", "schemaKey"]),
        ("Assessment", ["identifier", "schemaKey"]),
        ("Image", ["identifier", "schemaKey"]),
        ("Acquisition", ["hasContrastType", "schemaKey"]),
        (
            "Session",
            ["hasLabel", "hasFilePath", "hasAcquisition", "schemaKey"],
        ),
        (
            "Subject",
            [
                "hasLabel",
                "hasSession",
                "hasAge",
                "hasSex",
                "isSubjectGroup",
                "hasDiagnosis",
                "hasAssessment",
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
    "bids_list, expectation",
    [
        (["sub-01", "sub-02", "sub-03"], does_not_raise()),
        (
            ["sub-01", "sub-02", "sub-03", "sub-04", "sub-05"],
            pytest.raises(LookupError),
        ),
        (
            ["sub-cbm001", "sub-cbm002", "sub-cbm003"],
            pytest.raises(LookupError),
        ),
    ],
)
def test_check_unique_bids_subjects_err(bids_list, expectation):
    """
    Given a list of BIDS subject IDs, raise an error or not depending on
    whether all IDs are found in the phenotypic subject list.
    """
    pheno_list = ["sub-01", "sub-02", "sub-03", "sub-PD123", "sub-PD234"]

    with expectation:
        butil.check_unique_bids_subjects(
            pheno_subjects=pheno_list, bids_subjects=bids_list
        )


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
