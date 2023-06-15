from typing import Dict, Optional, Union

from pydantic import BaseModel, Field, conlist


class Identifier(BaseModel):
    """An identifier of a controlled term with an IRI"""

    termURL: str = Field(
        ...,
        description="An unambiguous identifier for the term, concept or entity that is referenced",
        alias="TermURL",
    )
    label: str = Field(
        ...,
        description="A human readable label. If more than one label exists for the term, "
        "then the preferred label should be used.",
        alias="Label",
    )


class Neurobagel(BaseModel):
    """The base model for a Neurobagel column annotation"""

    isAbout: Identifier = Field(
        ...,
        description="The concept or controlled term that describes this column",
        alias="IsAbout",
    )
    missingValues: conlist(str, unique_items=True) = Field(
        [],
        description="A list of unique values that represent "
        "invalid responses, typos, or missing data",
        alias="MissingValues",
    )
    isPartOf: Optional[Identifier] = Field(
        None,
        description="If the column is a subscale or item of an assessment tool "
        "then the assessment tool should be specified here.",
        alias="IsPartOf",
    )


class CategoricalNeurobagel(Neurobagel):
    """A Neurobagel annotation for a categorical column"""

    levels: Dict[str, Identifier] = Field(
        ...,
        description="For categorical variables: "
        "An object of values (keys) in the column and the semantic"
        "term (URI and label) they are unambiguously mapped to.",
        alias="Levels",
    )


class ContinuousNeurobagel(Neurobagel):
    """A Neurobagel annotation for a continuous column"""

    transformation: Identifier = Field(
        None,
        description="For continuous columns this field can be used to describe"
        "a transformation that can be applied to the values in this"
        "column in order to match the desired format of a standardized"
        "data element referenced in the IsAbout attribute.",
        alias="Transformation",
    )


class Column(BaseModel):
    """The base model for a BIDS column description"""

    description: str = Field(
        ...,
        description="Free-form natural language description",
        alias="Description",
    )
    annotations: Union[CategoricalNeurobagel, ContinuousNeurobagel] = Field(
        None, description="Semantic annotations", alias="Annotations"
    )


class CategoricalColumn(Column):
    """A BIDS column annotation for a categorical column"""

    levels: Dict[str, str] = Field(
        ...,
        description="For categorical variables: "
        "An object of possible values (keys) "
        "and their descriptions (values). ",
        alias="Levels",
    )


class ContinuousColumn(Column):
    """A BIDS column annotation for a continuous column"""

    units: str = Field(
        None,
        description="Measurement units for the values in this column. "
        "SI units in CMIXF formatting are RECOMMENDED (see Units)",
        alias="Units",
    )


class DataDictionary(BaseModel):
    """A data dictionary with human and machine readable information for a tabular data file"""

    __root__: Dict[str, Union[ContinuousColumn, CategoricalColumn]]
