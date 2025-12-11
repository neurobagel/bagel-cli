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

    name: Annotated[
        str,
        Field(
            ...,
            description="Name of the dataset. Key reused from BIDS dataset_description.json.",
            alias="Name",
        ),
    ]
    authors: Annotated[
        list[str],
        Field(
            default_factory=list,
            description="List of individuals who contributed to the creation/curation of the dataset. Key reused from BIDS dataset_description.json.",
            alias="Authors",
        ),
    ]
    references_and_links: Annotated[
        list[str],
        Field(
            default_factory=list,
            description="List of links or references that contain information on the dataset. Key reused from BIDS dataset_description.json.",
            alias="ReferencesAndLinks",
        ),
    ]
    keywords: Annotated[
        list[str],
        Field(
            default_factory=list,
            description="List of keywords describing the content or subject matter of the dataset. Key reused from BIDS dataset_description.json.",
            alias="Keywords",
        ),
    ]
    datalad_url: Annotated[
        AnyHttpUrl,
        Field(
            default=None,
            description="URL to a DataLad repository for the dataset.",
            alias="DataladURL",
        ),
    ]
    access_instructions: Annotated[
        str,
        Field(
            default=None,
            description="Description of how to access the data.",
            alias="AccessInstructions",
        ),
    ]
    access_type: Annotated[
        AccessType,
        Field(
            default=None,
            description="Level of requirements for dataset access.",
            alias="AccessType",
        ),
    ]
    access_email: Annotated[
        EmailStr,
        Field(
            default=None,
            description="Primary email for access requests.",
            alias="AccessEmail",
        ),
    ]
    # NOTE: AnyHttpUrl validation will fail for bare DOIs like 10.1038/s41586-020-03167-3
    access_link: Annotated[
        AnyHttpUrl,
        Field(
            default=None,
            description="Primary link for access requests or information.",
            alias="AccessLink",
        ),
    ]

    model_config = ConfigDict(extra="ignore")
