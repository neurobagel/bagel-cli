from collections import namedtuple
from pathlib import Path

from bagel.utility import load_json

Namespace = namedtuple("Namespace", ["pf", "url"])
COGATLAS = Namespace("cogatlas", "https://www.cognitiveatlas.org/task/id/")
NB = Namespace("nb", "http://neurobagel.org/vocab/")
NCIT = Namespace("ncit", "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#")
NIDM = Namespace("nidm", "http://purl.org/nidash/nidm#")
SNOMED = Namespace("snomed", "http://purl.bioontology.org/ontology/SNOMEDCT/")
NP = Namespace(
    "np", "https://github.com/nipoppy/pipeline-catalog/tree/main/processing"
)

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

PROCESSING_PIPELINE_PATH = (
    Path(__file__).parents[1] / "pipeline-catalog" / "processing"
)


def get_pipeline_uris() -> dict:
    output_dict = {}
    for pipe_file in PROCESSING_PIPELINE_PATH.glob("*.json"):
        pipe = load_json(pipe_file)
        output_dict[pipe["name"]] = f"{NP.pf}: {pipe['name']}"

    return output_dict


def get_pipeline_versions() -> dict:
    output_dict = {}
    for pipe_file in PROCESSING_PIPELINE_PATH.glob("*.json"):
        pipe = load_json(pipe_file)
        output_dict[pipe["name"]] = pipe["versions"]

    return output_dict
