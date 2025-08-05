import pytest

from bagel import mappings


@pytest.fixture(scope="session")
def mock_config_namespaces_mapping():
    return [
        {
            "config_name": "Neurobagel",
            "namespaces": {
                "variables": [
                    {
                        "namespace_prefix": "nb",
                        "namespace_url": "http://neurobagel.org/vocab/",
                    }
                ],
                "terms": [
                    {
                        "namespace_prefix": "ncit",
                        "namespace_url": "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#",
                    },
                    {
                        "namespace_prefix": "snomed",
                        "namespace_url": "http://purl.bioontology.org/ontology/SNOMEDCT/",
                    },
                ],
            },
        },
        {
            "config_name": "Ontario Brain Institute",
            "namespaces": {
                "variables": [
                    {
                        "namespace_prefix": "nb",
                        "namespace_url": "http://purl.bioontology.org/ontology/MEDDRA/",
                    }
                ],
                "terms": [
                    {
                        "namespace_prefix": "lnc",
                        "namespace_url": "http://purl.bioontology.org/ontology/LNC/",
                    },
                    {
                        "namespace_prefix": "medra",
                        "namespace_url": "http://purl.bioontology.org/ontology/MEDDRA/",
                    },
                ],
            },
        },
    ]


def test_get_available_configs(mock_config_namespaces_mapping):
    """Test the function returns a correct list of config names from a configuration namespaces mapping file."""
    assert mappings.get_available_configs(mock_config_namespaces_mapping) == [
        "Neurobagel",
        "Ontario Brain Institute",
    ]


def test_get_supported_namespaces_for_config(
    mock_config_namespaces_mapping, monkeypatch
):
    """Test the function correctly returns the supported namespaces for a given config name."""
    monkeypatch.setattr(
        mappings, "CONFIG_NAMESPACES_MAPPING", mock_config_namespaces_mapping
    )
    assert mappings.get_supported_namespaces_for_config("Neurobagel") == {
        "nb": "http://neurobagel.org/vocab/",
        "ncit": "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#",
        "snomed": "http://purl.bioontology.org/ontology/SNOMEDCT/",
    }


def test_parse_pipeline_catalog():
    """Test the function correctly parses a pipeline catalog file into two dictionaries for pipeline URIs and recognized versions."""
    mock_pipeline_catalog = [
        {
            "name": "fmriprep",
            "versions": [
                "20.2.0",
                "20.2.7",
                "23.1.3",
            ],
        },
        {"name": "freesurfer", "versions": ["6.0.1", "7.3.2"]},
    ]
    uri_dict, version_dict = mappings.parse_pipeline_catalog(
        mock_pipeline_catalog
    )
    assert uri_dict == {
        "fmriprep": "np:fmriprep",
        "freesurfer": "np:freesurfer",
    }
    assert version_dict == {
        "fmriprep": ["20.2.0", "20.2.7", "23.1.3"],
        "freesurfer": ["6.0.1", "7.3.2"],
    }
