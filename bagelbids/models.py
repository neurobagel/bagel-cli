from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class Imaging(BaseModel):
    hasContrastType: str
    schemaKey: Literal["Imaging"] = Field("Imaging", readOnly=True)


class Session(BaseModel):
    identifier: str
    hasAcquisition: List[Imaging]
    schemaKey: Literal["Session"] = Field("Session", readOnly=True)


class Subject(BaseModel):
    identifier: str
    hasSession: List[Session] = []
    age: Optional[float] = None
    sex: Optional[str] = None
    diagnosis: Optional[str] = None
    schemaKey: Literal["Subject"] = Field("Subject", readOnly=True)


class Dataset(BaseModel):
    identifier: str
    hasSamples: List[Subject]
    schemaKey: Literal["Dataset"] = Field("Dataset", readOnly=True)
