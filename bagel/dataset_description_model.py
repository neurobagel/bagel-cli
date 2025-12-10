from enum import Enum
from typing import Annotated

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, EmailStr, Field


class AccessType(str, Enum):
    """Enum for dataset access type."""

    PUBLIC = "public"
    REGISTERED = "registered"
    RESTRICTED = "restricted"


class DatasetDescription(BaseModel):
    """Schema for a Neurobagel dataset description JSON file."""

    name: Annotated[str, Field(..., alias="Name")]
    authors: Annotated[list[str], Field(default_factory=list, alias="Authors")]
    references_and_links: Annotated[
        list[str], Field(default_factory=list, alias="ReferencesAndLinks")
    ]
    keywords: Annotated[
        list[str], Field(default_factory=list, alias="Keywords")
    ]
    datalad_url: Annotated[AnyHttpUrl, Field(default=None, alias="DataladURL")]
    access_instructions: Annotated[
        str, Field(default=None, alias="AccessInstructions")
    ]
    access_type: Annotated[AccessType, Field(default=None, alias="AccessType")]
    access_email: Annotated[EmailStr, Field(default=None, alias="AccessEmail")]
    # NOTE: AnyHttpUrl validation will fail for bare DOIs like 10.1038/s41586-020-03167-3
    access_link: Annotated[AnyHttpUrl, Field(default=None, alias="AccessLink")]

    model_config = ConfigDict(extra="ignore")
