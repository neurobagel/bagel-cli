from collections import namedtuple

Namespace = namedtuple("Namespace", ["pf", "url"])
NB = Namespace("nb", "http://neurobagel.org/vocab/")
SNOMED = Namespace("snomed", "http://purl.bioontology.org/ontology/SNOMEDCT/")
NIDM = Namespace("nidm", "http://purl.org/nidash/nidm#")
COGATLAS = Namespace("cogatlas", "https://www.cognitiveatlas.org/task/id/")

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
    "healthy_control": "purl:NCIT_C94342",
    "assessment_tool": NB.pf + ":Assessment",
}
