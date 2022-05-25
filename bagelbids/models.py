from typing import List
from pydantic import BaseModel


class Imaging(BaseModel):
    hasContrastType: str


class Session(BaseModel):
    id: str
    hasAcquisition: List[Imaging]


class Subject(BaseModel):
    id: str
    hasSession: List[Session] = []


class Dataset(BaseModel):
    id: str
    hasSamples: List[Subject]
