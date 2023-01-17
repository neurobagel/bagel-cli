from typing import Dict, Optional, Union

from pydantic import BaseModel, conlist


class Identifier(BaseModel):
    TermURL: str
    Label: str


class Neurobagel(BaseModel):
    IsAbout: Identifier
    MissingValues: conlist(str, unique_items=True)
    IsPartOf: Optional[Identifier]


class CategoricalNeurobagel(Neurobagel):
    Levels: Dict[str, Identifier]


class ContinuousNeurobagel(Neurobagel):
    Transformation: Identifier


class Column(BaseModel):
    Description: str
    Annotations: Optional[Union[CategoricalNeurobagel, ContinuousNeurobagel]] = None


class CategoricalColumn(Column):
    Levels: Dict[str, str]


class ContinuousColumn(Column):
    Units: str


class DataDictionary(BaseModel):
    __root__: Dict[str, Union[ContinuousColumn, CategoricalColumn]]
