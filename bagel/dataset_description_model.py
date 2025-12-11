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
    # TODO: In the BIDS dataset_description.json, values for this field can be string references instead of URLs.
    # To store a 'homepage' for the dataset, we should find and use the first valid URL from this list.
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
    repository_url: Annotated[
        AnyHttpUrl,
        Field(
            default=None,
            description="URL to a repository where the dataset can be downloaded or retrieved from (e.g., DataLad, Zenodo, GitHub).",
            alias="RepositoryURL",
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
    access_link: Annotated[
        AnyHttpUrl,
        Field(
            default=None,
            description="Primary link for access requests or information.",
            alias="AccessLink",
        ),
    ]

    model_config = ConfigDict(extra="ignore")
