import uuid
from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Extra, Field, HttpUrl

UUID_PATTERN = r"[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12}$"
BAGEL_UUID_PATTERN = r"^bg:" + UUID_PATTERN


class Bagel(BaseModel, extra=Extra.forbid):
    """identifier has to be a valid UUID prepended by the bg: namespace
    by default, a random (uuid4) string UUID will be created"""

    identifier: str = Field(
        regex=BAGEL_UUID_PATTERN,
        default_factory=lambda: "bg:" + str(uuid.uuid4()),
    )


class Image(BaseModel, extra=Extra.forbid):
    identifier: str
    schemaKey: Literal["Image"] = "Image"


class Acquisition(Bagel):
    hasContrastType: Image
    schemaKey: Literal["Acquisition"] = "Acquisition"


class Diagnosis(BaseModel, extra=Extra.forbid):
    identifier: Union[str, HttpUrl]
    schemaKey: Literal["Diagnosis"] = "Diagnosis"


class Assessment(BaseModel, extra=Extra.forbid):
    identifier: Union[str, HttpUrl]
    schemaKey: Literal["Assessment"] = "Assessment"


class Session(Bagel):
    label: str
    filePath: Optional[str] = None
    hasAcquisition: List[Acquisition]
    schemaKey: Literal["Session"] = "Session"


class Subject(Bagel):
    label: str
    hasSession: Optional[List[Session]] = None
    age: Optional[float] = None
    sex: Optional[str] = None
    isSubjectGroup: Optional[str] = None
    diagnosis: Optional[List[Diagnosis]] = None
    assessment: Optional[List[Assessment]] = None
    schemaKey: Literal["Subject"] = "Subject"


class Dataset(Bagel):
    label: str
    hasSamples: List[Subject]
    schemaKey: Literal["Dataset"] = "Dataset"