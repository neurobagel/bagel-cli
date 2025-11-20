import uuid
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from bagel.mappings import NB

UUID_PATTERN = r"[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12}$"
BAGEL_UUID_PATTERN = rf"^{NB.pf}:{UUID_PATTERN}"


class Bagel(BaseModel):
    """identifier has to be a valid UUID prepended by the Neurobagel namespace
    by default, a random (uuid4) string UUID will be created"""

    identifier: Annotated[
        str,
        Field(
            pattern=BAGEL_UUID_PATTERN,
            default_factory=lambda: NB.pf + ":" + str(uuid.uuid4()),
        ),
    ]

    model_config = ConfigDict(extra="forbid")


class ControlledTerm(BaseModel):
    identifier: str | HttpUrl
    schemaKey: str


class Sex(ControlledTerm):
    schemaKey: Literal["Sex"] = "Sex"


class Diagnosis(ControlledTerm):
    schemaKey: Literal["Diagnosis"] = "Diagnosis"


class SubjectGroup(ControlledTerm):
    schemaKey: Literal["SubjectGroup"] = "SubjectGroup"


class Assessment(ControlledTerm):
    schemaKey: Literal["Assessment"] = "Assessment"


class Image(ControlledTerm):
    schemaKey: Literal["Image"] = "Image"


class Acquisition(Bagel):
    hasContrastType: Image
    schemaKey: Literal["Acquisition"] = "Acquisition"


class Pipeline(ControlledTerm):
    schemaKey: Literal["Pipeline"] = "Pipeline"


class CompletedPipeline(Bagel):
    hasPipelineVersion: str
    hasPipelineName: Pipeline
    schemaKey: Literal["CompletedPipeline"] = "CompletedPipeline"


class Session(Bagel):
    hasLabel: str


class PhenotypicSession(Session):
    hasAge: float | None = None
    hasSex: Sex | None = None
    isSubjectGroup: SubjectGroup | None = None
    hasDiagnosis: list[Diagnosis] | None = None
    hasAssessment: list[Assessment] | None = None
    schemaKey: Literal["PhenotypicSession"] = "PhenotypicSession"


class ImagingSession(Session):
    # NOTE: Do imaging session have to have at least one acquisition OR at least one completed pipeline to be valid?
    hasFilePath: str | None = None
    hasAcquisition: list[Acquisition] | None = None
    hasCompletedPipeline: list[CompletedPipeline] | None = None
    schemaKey: Literal["ImagingSession"] = "ImagingSession"


class Subject(Bagel):
    hasLabel: str
    hasSession: list[PhenotypicSession | ImagingSession]
    schemaKey: Literal["Subject"] = "Subject"


class Dataset(Bagel):
    hasLabel: str
    # NOTE: Since Pydantic v2, URL types no longer inherit from `str`
    # (see https://docs.pydantic.dev/latest/migration/#url-and-dsn-types-in-pydanticnetworks-no-longer-inherit-from-str)
    hasPortalURI: str | HttpUrl | None = None
    hasSamples: list[Subject]
    schemaKey: Literal["Dataset"] = "Dataset"
