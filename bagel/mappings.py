BIDS = {
    "anat": "nidm:Anatomical",
    "func": "nidm:Functional",
    "dwi": "nidm:DiffusionWeighted",
    "bval": "nidm:b-value",
    "bvec": "nidm:b-vector",
    "T1w": "nidm:T1Weighted",
    "T2w": "nidm:T2Weighted",
    "inplaneT2": "nidm:T2Weighted",
    "bold": "nidm:FlowWeighted",
    "dti": "nidm:DiffusionTensor",
    "asl": "nidm:ArterialSpinLabeling",
}
NEUROBAGEL = {
    "participant": "nb:ParticipantID",  # TODO: Add to graph?
    "session": "nb:SessionID",  # TODO: Add to graph?
    "sex": "nb:Sex",
    "age": "nb:Age",
    "diagnosis": "nb:Diagnosis",
    "healthy_control": "purl:NCIT_C94342",
    "assessment_tool": "nb:Assessment",
}
