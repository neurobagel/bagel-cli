from typing import Dict, Optional, Union

from pydantic import BaseModel, conlist, Field


class Identifier(BaseModel):
    TermURL: str = Field(..., description="An unambiguous identifier for the term, concept or entity that is referenced")
    Label: str = Field(..., description="A human readable label. If more than one label exists for the term, "
                                        "then the preferred label should be used.")


class Neurobagel(BaseModel):
    IsAbout: Identifier = Field(..., description="The concept or controlled term that describes this column")
    MissingValues: conlist(str, unique_items=True) = Field(..., description="A list of unique values that represent "
                                                                            "invalid responses, typos, or missing data")
    IsPartOf: Optional[Identifier] = Field(..., description="If the column is a subscale or item of an assessment tool"
                                                            "then the assessment tool should be specified here.")


class CategoricalNeurobagel(Neurobagel):
    Levels: Dict[str, Identifier] = Field(..., description="For categorical variables: "
                                                           "An object of values (keys) in the column and the semantic"
                                                           "term (URI and label) they are unambiguously mapped to.")


class ContinuousNeurobagel(Neurobagel):
    Transformation: Identifier = Field(..., description="For continuous columns this field can be used to describe"
                                                        "a transformation that can be applied to the values in this"
                                                        "column in order to match the desired format of a standardized"
                                                        "data element referenced in the IsAbout attribute.")


class Column(BaseModel):
    Description: str = Field(..., description="Free-form natural language description")
    Annotations: Optional[Union[CategoricalNeurobagel, ContinuousNeurobagel]] = Field(None,
                                                                                      description="Semantic annotations")


class CategoricalColumn(Column):
    Levels: Dict[str, str] = Field(..., description="For categorical variables: "
                                                    "An object of possible values (keys) "
                                                    "and their descriptions (values). ")


class ContinuousColumn(Column):
    Units: str = Field(..., description="Measurement units for the values in this column. "
                                        "SI units in CMIXF formatting are RECOMMENDED (see Units)")


class DataDictionary(BaseModel):
    __root__: Dict[str, Union[ContinuousColumn, CategoricalColumn]]
