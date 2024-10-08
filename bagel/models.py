import uuid
from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Extra, Field, HttpUrl

from bagel.mappings import NB

UUID_PATTERN = r"[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12}$"
BAGEL_UUID_PATTERN = rf"^{NB.pf}:{UUID_PATTERN}"


class Bagel(BaseModel, extra=Extra.forbid):
    """identifier has to be a valid UUID prepended by the Neurobagel namespace
    by default, a random (uuid4) string UUID will be created"""

    identifier: str = Field(
        regex=BAGEL_UUID_PATTERN,
        default_factory=lambda: NB.pf + ":" + str(uuid.uuid4()),
    )


class ControlledTerm(BaseModel):
    identifier: Union[str, HttpUrl]
    schemaKey: str


class Sex(ControlledTerm):
    schemaKey = "Sex"


class Diagnosis(ControlledTerm):
    schemaKey = "Diagnosis"


class SubjectGroup(ControlledTerm):
    schemaKey = "SubjectGroup"


class Assessment(ControlledTerm):
    schemaKey = "Assessment"


class Image(ControlledTerm):
    schemaKey = "Image"


class Acquisition(Bagel):
    hasContrastType: Image
    schemaKey: Literal["Acquisition"] = "Acquisition"


class Pipeline(ControlledTerm):
    schemaKey = "Pipeline"


class CompletedPipeline(Bagel):
    hasPipelineVersion: str
    hasPipelineName: Pipeline
    schemaKey: Literal["CompletedPipeline"] = "CompletedPipeline"


class Session(Bagel):
    hasLabel: str


class PhenotypicSession(Session):
    hasAge: Optional[float] = None
    hasSex: Optional[Sex] = None
    isSubjectGroup: Optional[SubjectGroup] = None
    hasDiagnosis: Optional[List[Diagnosis]] = None
    hasAssessment: Optional[List[Assessment]] = None
    schemaKey = "PhenotypicSession"


class ImagingSession(Session):
    # NOTE: Do imaging session have to have at least one acquisition OR at least one completed pipeline to be valid?
    hasFilePath: Optional[str] = None
    hasAcquisition: Optional[List[Acquisition]] = None
    hasCompletedPipeline: Optional[List[CompletedPipeline]] = None
    schemaKey = "ImagingSession"


class Subject(Bagel):
    hasLabel: str
    hasSession: List[Union[PhenotypicSession, ImagingSession]]
    schemaKey: Literal["Subject"] = "Subject"


class Dataset(Bagel):
    hasLabel: str
    hasPortalURI: Optional[HttpUrl] = None
    hasSamples: List[Subject]
    schemaKey: Literal["Dataset"] = "Dataset"
