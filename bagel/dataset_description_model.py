from enum import Enum
from typing import Annotated, Any

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    EmailStr,
    Field,
    HttpUrl,
    field_validator,
)


def whitespace_string_to_default_none(value: Any) -> Any:
    """Convert an empty string or a string that contains only whitespace to None."""
    if isinstance(value, str) and value.strip() == "":
        return None
    return value


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
                "Name of the dataset. This name will be displayed when users discover the dataset in a Neurobagel query. "
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
    # NOTE: In the BIDS dataset_description.json, values for this field can be string references as well as URLs.
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
        HttpUrl | None,
        Field(
            default=None,
            description="URL to a repository where the dataset can be downloaded or retrieved from (e.g., DataLad, Zenodo, GitHub).",
            alias="RepositoryURL",
        ),
        BeforeValidator(whitespace_string_to_default_none),
    ]
    access_instructions: Annotated[
        str | None,
        Field(
            default=None,
            description="Description of how to access the data.",
            alias="AccessInstructions",
        ),
        AfterValidator(whitespace_string_to_default_none),
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
        EmailStr | None,
        Field(
            default=None,
            description="Primary email for access requests.",
            alias="AccessEmail",
        ),
        BeforeValidator(whitespace_string_to_default_none),
    ]
    access_link: Annotated[
        HttpUrl | None,
        Field(
            default=None,
            description="Primary link for access requests or information.",
            alias="AccessLink",
        ),
        BeforeValidator(whitespace_string_to_default_none),
    ]

    # NOTE: url_preserve_empty_path (>=2.12) is needed to prevent HttpUrl from auto-appending trailing slashes to URLs
    # when the path portion of the URL is empty
    # (https://docs.pydantic.dev/latest/migration/#url-and-dsn-types-in-pydanticnetworks-no-longer-inherit-from-str)
    model_config = ConfigDict(extra="ignore", url_preserve_empty_path=True)

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

    @field_validator("authors", "references_and_links", "keywords")
    @classmethod
    def whitespace_list_to_default_empty_list(
        cls, value: list[str]
    ) -> list[str]:
        """Convert a list containing only empty or whitespace strings to an empty list."""
        if all(item.strip() == "" for item in value):
            return []
        return value
