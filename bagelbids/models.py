import uuid

from typing import List, Literal, Optional
from pydantic import BaseModel, Field, constr


class Bagel(BaseModel):
    """identifier has to be a valid UUID prepended by the bagel: namespace
    by default, a random (uuid4) string UUID will be created"""

    identifier: constr(
        regex=r"^bagel:[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12}$"
    ) = "bagel:" + str(uuid.uuid4())


class Imaging(Bagel):
    hasContrastType: str
    schemaKey: Literal["Imaging"] = Field("Imaging", readOnly=True)


class Session(Bagel):
    label: str
    hasAcquisition: List[Imaging]
    schemaKey: Literal["Session"] = Field("Session", readOnly=True)


class Subject(Bagel):
    label: str
    hasSession: Optional[List[Session]] = None
    age: Optional[float] = None
    sex: Optional[str] = None
    diagnosis: Optional[str] = None
    schemaKey: Literal["Subject"] = Field("Subject", readOnly=True)


class Dataset(Bagel):
    label: str
    hasSamples: List[Subject]
    schemaKey: Literal["Dataset"] = Field("Dataset", readOnly=True)
