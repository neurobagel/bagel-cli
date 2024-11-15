from typing import Dict, List, Union

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, RootModel
from pydantic_core import PydanticCustomError
from typing_extensions import Annotated


def validate_unique_list(values: List[str]) -> List[str]:
    """
    Check that provided list only has unique elements.

    This custom validator is needed because constrained dtypes and their `unique_items` parameter
    were deprecated in Pydantic v2. This function was adapted from https://github.com/pydantic/pydantic-core/pull/820#issuecomment-1656228704
    and https://docs.pydantic.dev/latest/concepts/validators/#annotated-validators.

    See also:
    - https://docs.pydantic.dev/latest/migration/#changes-to-pydanticfield
    - https://docs.pydantic.dev/latest/api/types/#pydantic.types.conlist)
    """
    if len(values) != len(set(values)):
        raise PydanticCustomError(
            "unique_list", f"{values} is not a unique list"
        )
    return values


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
    missingValues: Annotated[
        List[str],
        AfterValidator(validate_unique_list),
        Field(
            [],
            description="A list of unique values that represent "
            "invalid responses, typos, or missing data",
            alias="MissingValues",
            json_schema_extra={"uniqueItems": True},
        ),
    ]

    model_config = ConfigDict(extra="forbid")


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
        ...,
        description="For continuous columns this field can be used to describe"
        "a transformation that can be applied to the values in this"
        "column in order to match the desired format of a standardized"
        "data element referenced in the IsAbout attribute.",
        alias="Transformation",
    )


class IdentifierNeurobagel(Neurobagel):
    """A Neurobagel annotation for an identifier column"""

    identifies: str = Field(
        ...,
        description="For identifier columns, the type of observation uniquely identified by this column.",
        alias="Identifies",
    )


class ToolNeurobagel(Neurobagel):
    """A Neurobagel annotation for an assessment tool column"""

    # NOTE: Optional[Identifier] was removed as part of https://github.com/neurobagel/bagel-cli/pull/389
    # because we couldn't tell what the Optional was doing
    isPartOf: Identifier = Field(
        ...,
        description="If the column is a subscale or item of an assessment tool "
        "then the assessment tool should be specified here.",
        alias="IsPartOf",
    )


class Column(BaseModel):
    """The base model for a BIDS column description"""

    description: str = Field(
        ...,
        description="Free-form natural language description",
        alias="Description",
    )
    annotations: Union[
        CategoricalNeurobagel,
        ContinuousNeurobagel,
        IdentifierNeurobagel,
        ToolNeurobagel,
    ] = Field(None, description="Semantic annotations", alias="Annotations")


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


class DataDictionary(
    RootModel[Dict[str, Union[ContinuousColumn, CategoricalColumn]]]
):
    """A data dictionary with human and machine readable information for a tabular data file"""

    pass
