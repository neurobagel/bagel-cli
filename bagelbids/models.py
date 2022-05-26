from typing import List, Literal
from pydantic import BaseModel, Field


class Imaging(BaseModel):
    hasContrastType: str
    schemaKey: Literal["Imaging"] = Field("Imaging", readOnly=True)


class Session(BaseModel):
    id: str
    hasAcquisition: List[Imaging]
    schemaKey: Literal["Session"] = Field("Session", readOnly=True)


class Subject(BaseModel):
    id: str
    hasSession: List[Session] = []
    schemaKey: Literal["Subject"] = Field("Subject", readOnly=True)


class Dataset(BaseModel):
    id: str
    hasSamples: List[Subject]
    schemaKey: Literal["Dataset"] = Field("Dataset", readOnly=True)
