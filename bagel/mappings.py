import json
import warnings
from collections import namedtuple
from pathlib import Path

import httpx

from .utilities import file_utils

Namespace = namedtuple("Namespace", ["pf", "url"])
COGATLAS = Namespace("cogatlas", "https://www.cognitiveatlas.org/task/id/")
NB = Namespace("nb", "http://neurobagel.org/vocab/")
NCIT = Namespace("ncit", "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#")
NIDM = Namespace("nidm", "http://purl.org/nidash/nidm#")
SNOMED = Namespace("snomed", "http://purl.bioontology.org/ontology/SNOMEDCT/")
NP = Namespace(
    "np", "https://github.com/nipoppy/pipeline-catalog/tree/main/processing/"
)
# Store all supported amespaces in a list for easy iteration & testing
ALL_NAMESPACES = [COGATLAS, NB, NCIT, NIDM, SNOMED, NP]

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
PROCESSING_PIPELINE_PATH = Path(__file__).parent / "local_vocab_backup"
PROCESSING_PIPELINE_URL = "https://raw.githubusercontent.com/nipoppy/pipeline-catalog/refs/heads/main/processing/processing.json"


def get_pipeline_catalog(get_url: str, get_path: Path) -> dict:
    """
    Load the pipeline catalog from the remote location or, if that fails,
    from the local backup.
    """
    try:
        response = httpx.get(get_url)
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPStatusError, httpx.ConnectError, json.JSONDecodeError):
        warnings.warn(
            f"Unable to load pipeline catalog from {get_url}.\n"
            f"Will revert to loading backup from {get_path}."
        )
        return file_utils.load_json(get_path)


def get_pipeline_uris(in_arr: list) -> dict:
    """
    Load files from the pipeline-catalog and return a dictionary of pipeline names
    and their URIs in the Nipoppy namespace.
    """
    output_dict = {}
    for pipeline in in_arr:
        output_dict[pipeline["name"]] = f"{NP.pf}:{pipeline['name']}"

    return output_dict


def get_pipeline_versions(in_arr: list) -> dict:
    """
    Load files from the pipeline-catalog and return a dictionary of pipeline names
    and corresponding supported versions in the Nipoppy namespace.
    """
    output_dict = {}
    for pipeline in in_arr:
        output_dict[pipeline["name"]] = pipeline["versions"]

    return output_dict


def parse_pipeline_catalog():
    """
    Load the pipeline catalog and return a dictionary of pipeline names and their URIs
    and a dictionary of pipeline names and their versions.
    """
    in_arr = get_pipeline_catalog(
        get_url=PROCESSING_PIPELINE_URL,
        get_path=PROCESSING_PIPELINE_PATH / "processing_pipelines.json",
    )
    # version_dict = {}
    # uri_dict = {}
    # for pipeline in in_arr:
    #     version_dict[pipeline["name"]] = pipeline["versions"]
    #     uri_dict[pipeline["name"]] = f"{NP.pf}:{pipeline['name']}"

    return get_pipeline_uris(in_arr), get_pipeline_versions(in_arr)


# TODO: consider refactoring this into a Mappings class that also
# handles lazy loading of the remote content, i.e. only when accessed
KNOWN_PIPELINE_URIS, KNOWN_PIPELINE_VERSIONS = parse_pipeline_catalog()
