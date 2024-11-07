import pytest

from bagel import mappings, models
from bagel.utilities import model_utils as mutil


@pytest.fixture
def get_test_context():
    """Generate an @context dictionary to test against."""
    return mutil.generate_context()


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
    bids_exclusive_subs = mutil.get_subs_missing_from_pheno_data(
        pheno_subjects=pheno_list, subjects=bids_list
    )

    # We sort the list for comparison since the order of the missing subjects is not guaranteed
    # due to using set operations
    assert sorted(bids_exclusive_subs) == expected_bids_exclusive_subs


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

    subjects = mutil.get_subject_instances(dataset)
    assert list(subjects.keys()) == ["sub-01", "sub-02"]


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
    imaging_sessions = mutil.get_imaging_session_instances(example_subject)

    assert list(imaging_sessions.keys()) == ["ses-im01"]


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


def test_add_context_to_graph_dataset():
    """Test that add_context_to_graph_dataset() correctly adds the @context to a graph dataset instance."""
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

    jsonld = mutil.add_context_to_graph_dataset(dataset=dataset)

    assert "@context" in jsonld.keys()
    assert len(jsonld["hasSamples"]) == 2
