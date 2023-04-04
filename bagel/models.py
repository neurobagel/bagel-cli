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


class ControlledTerm(BaseModel):
    identifier: Union[str, HttpUrl]
    schemaKey: str


class Acquisition(Bagel):
    hasContrastType: ControlledTerm
    schemaKey: Literal["Acquisition"] = "Acquisition"


class Session(Bagel):
    label: str
    filePath: Optional[str] = None
    hasAcquisition: List[Acquisition]
    schemaKey: Literal["Session"] = "Session"


class Subject(Bagel):
    label: str
    hasSession: Optional[List[Session]] = None
    age: Optional[float] = None
    sex: Optional[ControlledTerm] = None
    isSubjectGroup: Optional[ControlledTerm] = None
    diagnosis: Optional[List[ControlledTerm]] = None
    assessment: Optional[List[ControlledTerm]] = None
    schemaKey: Literal["Subject"] = "Subject"


class Dataset(Bagel):
    label: str
    hasSamples: List[Subject]
    schemaKey: Literal["Dataset"] = "Dataset"
