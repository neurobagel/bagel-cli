import pytest
from pydantic import ValidationError

from bagel import dataset_description_model


@pytest.mark.parametrize(
    "valid_dataset_description",
    [
        {
            "Name": "Test Dataset",
            "Authors": ["First Author", "Second Author"],
            "ReferencesAndLinks": [
                "https://mydataset.org",
                "https://doi.org/10.1234/example-doi",
            ],
            "Keywords": ["Parkinson's Disease", "fMRI"],
            "DataladURL": "https://datasets.datalad.org/mydataset",
            "AccessInstructions": "Submit a data access request at https://mydataset.org/access",
            "AccessType": "restricted",
            "AccessEmail": "first.author@gmail.com",
            "AccessLink": "https://mydataset.org/access",
        },
        {"Name": "Test Dataset"},
        {
            "Name": "Test Dataset",
            "Authors": [],
            "ReferencesAndLinks": [],
            "Keywords": [],
            "AccessInstructions": "",
        },
        {
            "Name": "Test Dataset",
            "BIDSVersion": "1.6.0",  # from BIDS dataset_description.json
            "DatasetType": "raw",  # from BIDS dataset_description.json
        },
    ],
)
def test_valid_dataset_description_passes_validation(
    valid_dataset_description,
):
    """
    Test that valid dataset descriptions do not raise a validation error,
    even if optional fields are omitted or BIDS-only fields are included.
    """
    dataset_description_model.DatasetDescription(**valid_dataset_description)


def test_invalid_dataset_description_fails_validation():
    """
    Test that an invalid dataset description raises a validation error.
    """
    invalid_dataset_description = {
        "Name": "Test Dataset",
        "Authors": None,  # must be omitted or a list
        "AccessInstructions": None,  # must be omitted or a string
        "AccessType": "unknown",  # unrecognized access type
        "AccessEmail": "",  # not a valid email
    }

    with pytest.raises(ValidationError) as err:
        dataset_description_model.DatasetDescription(
            **invalid_dataset_description
        )

    errors = err.value.errors()
    invalid_fields = {error["loc"][0] for error in errors}

    assert len(errors) == 4
    assert invalid_fields == {
        "Authors",
        "AccessInstructions",
        "AccessType",
        "AccessEmail",
    }
