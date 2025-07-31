import json
from collections import namedtuple
from pathlib import Path

import httpx

from .logger import log_error, logger
from .utilities import file_utils

DEFAULT_CONFIG = "Neurobagel"

Namespace = namedtuple("Namespace", ["pf", "url"])
COGATLAS = Namespace("cogatlas", "https://www.cognitiveatlas.org/task/id/")
NB = Namespace("nb", "http://neurobagel.org/vocab/")
NCIT = Namespace("ncit", "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#")
NIDM = Namespace("nidm", "http://purl.org/nidash/nidm#")
# SNOMED = Namespace("snomed", "http://purl.bioontology.org/ontology/SNOMEDCT/")
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
COMMUNITY_NAMESPACES_URL = "https://raw.githubusercontent.com/neurobagel/communities/refs/heads/main/config_metadata/config_namespace_map.json"


def request_file(url: str) -> list[dict]:
    response = httpx.get(url)
    response.raise_for_status()
    return response.json()


def get_all_community_namespaces() -> list[dict]:
    try:
        return request_file(COMMUNITY_NAMESPACES_URL)
    except (httpx.HTTPError, json.JSONDecodeError) as e:
        log_error(
            logger,
            f"Error fetching configuration namespaces from {COMMUNITY_NAMESPACES_URL}: {e}. "
            "Please ensure that you have an internet connection, or open an issue in https://github.com/neurobagel/bagel-cli/issues if the problem persists.",
        )


def get_supported_namespaces_for_config(config: str) -> dict:
    config_namespaces = next(
        config["namespaces"]
        for config in ALL_COMMUNITY_NAMESPACES
        if config["config_name"] == config
    )

    config_namespaces_dict = {}
    for namespace_group in config_namespaces.values():
        for namespace in namespace_group:
            config_namespaces_dict[namespace["namespace_prefix"]] = namespace[
                "namespace_url"
            ]

    return config_namespaces_dict


def get_pipeline_catalog(url: str, path: Path) -> list[dict]:
    """
    Load the pipeline catalog from the remote location or, if that fails,
    from the local backup.
    """
    try:
        return request_file(url)
    # The JSONDecodeError should catch the case where the file is empty
    except (httpx.HTTPError, json.JSONDecodeError) as e:
        logger.warning(
            f"Unable to download pipeline catalog from {url}: {e}. Do you have an internet connection? "
            f"Attempting to load backup from {path} instead - "
            "note that the backup pipeline catalog bundled with your version of the CLI may not be the most up-to-date."
        )
        try:
            # load_json() will catch JSONDecodeError which should catch when the file is empty
            return file_utils.load_json(path)
        except FileNotFoundError as e:
            log_error(
                logger,
                f"Unable to find a local pipeline-catalog backup. Have you correctly initialized the submodules? {e}",
            )


def parse_pipeline_catalog() -> tuple[dict, dict]:
    """
    Load the pipeline catalog and return a dictionary of pipeline names and their URIs in the Nipoppy namespace,
    and a dictionary of pipeline names and their supported versions in Nipoppy.
    """
    pipeline_catalog_arr = get_pipeline_catalog(
        url=PROCESSING_PIPELINE_URL,
        path=PROCESSING_PIPELINE_PATH,
    )

    version_dict = {}
    uri_dict = {}
    for pipeline in pipeline_catalog_arr:
        version_dict[pipeline["name"]] = pipeline["versions"]
        uri_dict[pipeline["name"]] = f"{NP.pf}:{pipeline['name']}"

    return uri_dict, version_dict


# TODO: consider refactoring this into a Mappings class that also
# handles lazy loading of the remote content, i.e. only when accessed
KNOWN_PIPELINE_URIS, KNOWN_PIPELINE_VERSIONS = parse_pipeline_catalog()
ALL_COMMUNITY_NAMESPACES = get_all_community_namespaces()
AVAILABLE_COMMUNITY_CONFIGS = [
    config["config_name"] for config in ALL_COMMUNITY_NAMESPACES
]
