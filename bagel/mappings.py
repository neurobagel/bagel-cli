from collections import namedtuple

Namespace = namedtuple("Namespace", ["pf", "url"])
COGATLAS = Namespace("cogatlas", "https://www.cognitiveatlas.org/task/id/")
NB = Namespace("nb", "http://neurobagel.org/vocab/")
NCIT = Namespace("ncit", "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#")
NIDM = Namespace("nidm", "http://purl.org/nidash/nidm#")
SNOMED = Namespace("snomed", "http://purl.bioontology.org/ontology/SNOMEDCT/")

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
