from enum import Enum
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    HttpUrl,
    field_validator,
)


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
            description=(
                "Name of the dataset. This name will be displayed when users discover the dataset in a Neurobagel query."
                "Key reused from BIDS dataset_description.json."
            ),
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
        HttpUrl,
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
        HttpUrl,
        Field(
            default=None,
            description="Primary link for access requests or information.",
            alias="AccessLink",
        ),
    ]

    model_config = ConfigDict(extra="ignore")

    @field_validator("name")
    @classmethod
    def check_name_not_whitespace(cls, value: str) -> str:
        """
        Raise an error (will be caught as a ValidationError by Pydantic) if
        the required 'Name' field is an empty string or all whitespace.
        """
        if value.strip() == "":
            raise ValueError("'Name' field cannot be an empty string.")
        return value

    @field_validator("access_instructions")
    @classmethod
    def whitespace_string_to_default_none(
        cls, value: str | None
    ) -> str | None:
        """Convert an empty string or a string that contains only whitespace to None."""
        if value is not None and value.strip() == "":
            return None
        return value

    @field_validator("authors", "references_and_links", "keywords")
    @classmethod
    def whitespace_list_to_default_empty_list(
        cls, value: list[str]
    ) -> list[str]:
        """Convert a list containing only empty or whitespace strings to an empty list."""
        if all(item.strip() == "" for item in value):
            return []
        return value
