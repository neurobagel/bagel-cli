from uuid import UUID

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class Imaging(BaseModel):
    identifier: Optional[UUID] = None
    hasContrastType: str
    schemaKey: Literal["Imaging"] = Field("Imaging", readOnly=True)


class Session(BaseModel):
    identifier: Optional[UUID] = None
    label: str
    hasAcquisition: List[Imaging]
    schemaKey: Literal["Session"] = Field("Session", readOnly=True)


class Subject(BaseModel):
    identifier: Optional[UUID] = None
    label: str
    hasSession: Optional[List[Session]] = None
    age: Optional[float] = None
    sex: Optional[str] = None
    diagnosis: Optional[str] = None
    schemaKey: Literal["Subject"] = Field("Subject", readOnly=True)


class Dataset(BaseModel):
    identifier: Optional[UUID] = None
    label: str
    hasSamples: List[Subject]
    schemaKey: Literal["Dataset"] = Field("Dataset", readOnly=True)
