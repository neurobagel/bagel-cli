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


class Session(Bagel):
    hasLabel: str
    hasFilePath: Optional[str] = None
    hasAcquisition: List[Acquisition]
    schemaKey: Literal["Session"] = "Session"


class Subject(Bagel):
    hasLabel: str
    hasSession: Optional[List[Session]] = None
    hasAge: Optional[float] = None
    hasSex: Optional[Sex] = None
    isSubjectGroup: Optional[SubjectGroup] = None
    hasDiagnosis: Optional[List[Diagnosis]] = None
    hasAssessment: Optional[List[Assessment]] = None
    schemaKey: Literal["Subject"] = "Subject"


class Dataset(Bagel):
    hasLabel: str
    hasFilePath: str
    hasPortalURI: Optional[HttpUrl] = None
    hasSamples: List[Subject]
    schemaKey: Literal["Dataset"] = "Dataset"
