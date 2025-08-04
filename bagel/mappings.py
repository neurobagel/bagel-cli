from collections import namedtuple
from pathlib import Path

from .utilities import file_utils

DEFAULT_CONFIG = "Neurobagel"

Namespace = namedtuple("Namespace", ["pf", "url"])
COGATLAS = Namespace("cogatlas", "https://www.cognitiveatlas.org/task/id/")
NB = Namespace("nb", "http://neurobagel.org/vocab/")
NCIT = Namespace("ncit", "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#")
NIDM = Namespace("nidm", "http://purl.org/nidash/nidm#")
NP = Namespace(
    "np", "https://github.com/nipoppy/pipeline-catalog/tree/main/processing/"
)

# Keep deprecated namespaces for informative user messages
DEPRECATED_NAMESPACES = [COGATLAS]
DEPRECATED_NAMESPACE_PREFIXES = [ns.pf for ns in DEPRECATED_NAMESPACES]

BIDS = {
    "anat": NIDM.pf + ":Anatomical",
    "func": NIDM.pf + ":Functional",
    "dwi": NIDM.pf + ":DiffusionWeighted",
    "bval": NIDM.pf + ":b-value",
    "bvec": NIDM.pf + ":b-vector",
    "T1w": NIDM.pf + ":T1Weighted",
    "T2w": NIDM.pf + ":T2Weighted",
    "inplaneT2": NIDM.pf + ":T2Weighted",
    "bold": NIDM.pf + ":FlowWeighted",
    "dti": NIDM.pf + ":DiffusionTensor",
    "asl": NIDM.pf + ":ArterialSpinLabeling",
}
NEUROBAGEL = {
    "participant": NB.pf + ":ParticipantID",
    "session": NB.pf + ":SessionID",
    "sex": NB.pf + ":Sex",
    "age": NB.pf + ":Age",
    "diagnosis": NB.pf + ":Diagnosis",
    "healthy_control": NCIT.pf + ":C94342",
    "assessment_tool": NB.pf + ":Assessment",
}

# TODO: Use importlib.resources.files(bagel) to get the path to the pipeline-catalog instead?
PROCESSING_PIPELINE_PATH = (
    Path(__file__).parent / "pipeline-catalog/processing/processing.json"
)
PROCESSING_PIPELINE_URL = "https://raw.githubusercontent.com/nipoppy/pipeline-catalog/refs/heads/main/processing/processing.json"
CONFIG_NAMESPACES_PATH = (
    Path(__file__).parent
    / "communities/config_metadata/config_namespace_map.json"
)
CONFIG_NAMESPACES_URL = "https://raw.githubusercontent.com/neurobagel/communities/refs/heads/main/config_metadata/config_namespace_map.json"


def get_available_configs(config_namespaces_mapping: list) -> list:
    return [config["config_name"] for config in config_namespaces_mapping]


def get_supported_namespaces_for_config(config_name: str) -> dict:
    config_namespaces = next(
        config["namespaces"]
        for config in CONFIG_NAMESPACES_MAPPING
        if config["config_name"] == config_name
    )

    config_namespaces_dict = {}
    for namespace_group in config_namespaces.values():
        for namespace in namespace_group:
            config_namespaces_dict[namespace["namespace_prefix"]] = namespace[
                "namespace_url"
            ]

    return config_namespaces_dict


def parse_pipeline_catalog(pipeline_catalog: list) -> tuple[dict, dict]:
    """
    Load the pipeline catalog and return a dictionary of pipeline names and their URIs in the Nipoppy namespace,
    and a dictionary of pipeline names and their supported versions in Nipoppy.
    """
    version_dict = {}
    uri_dict = {}
    for pipeline in pipeline_catalog:
        version_dict[pipeline["name"]] = pipeline["versions"]
        uri_dict[pipeline["name"]] = f"{NP.pf}:{pipeline['name']}"

    return uri_dict, version_dict


# TODO: consider refactoring this into a Mappings class that also
# handles lazy loading of the remote content, i.e. only when accessed
PIPELINE_CATALOG, PIPELINES_FETCHING_ERR = file_utils.request_file(
    url=PROCESSING_PIPELINE_URL, backup_path=PROCESSING_PIPELINE_PATH
)
CONFIG_NAMESPACES_MAPPING, CONFIG_FETCHING_ERR = file_utils.request_file(
    url=CONFIG_NAMESPACES_URL, backup_path=CONFIG_NAMESPACES_PATH
)
