import bidsschematools as bst
import pandas as pd
import pandera.extensions as extensions
import pandera.pandas as pa

NO_WHITESPACE_ERR = (
    "Must be a non-empty value that does not contain only whitespace."
)


def get_bids_supported_suffixes() -> list[str]:
    """
    Retrieve the list of supported BIDS suffixes from the BIDS schema.
    Note that the suffixes are not restricted to NIfTI data.
    """
    bids_schema = bst.schema.load_schema()
    suffixes = bids_schema["objects.suffixes"].to_dict().keys()
    return list(suffixes)


BIDS_SUPPORTED_SUFFIXES = get_bids_supported_suffixes()


@extensions.register_check_method()
def is_not_whitespace(pd_series: pd.Series) -> pd.Series:
    """
    Custom Pandera validation method that checks that column values are not empty strings or whitespace.

    TODO: Should non-empty strings with leading/trailing whitespace also fail validation?
    """
    return pd_series.str.strip() != ""


model = pa.DataFrameSchema(
    # NOTE: Most of the columns will implicitly fail on an empty cell via other checks,
    # but we explicitly check for whitespace-only values to provide a more informative error message.
    {
        "sub": pa.Column(
            str,
            checks=[
                pa.Check.is_not_whitespace(error=NO_WHITESPACE_ERR),
                pa.Check.str_startswith("sub-"),
            ],
            nullable=False,
        ),
        "ses": pa.Column(
            str,
            pa.Check(
                lambda ses: (ses.str.strip() == "")
                | ses.str.startswith("ses-"),
                ignore_na=True,
                error='Session ID must be left empty or start with the "ses-" prefix.',
            ),
            nullable=True,
        ),
        "suffix": pa.Column(
            str,
            checks=[
                pa.Check.is_not_whitespace(error=NO_WHITESPACE_ERR),
                pa.Check.isin(
                    BIDS_SUPPORTED_SUFFIXES
                ),  # NOTE: suffixes are case-sensitive
            ],
            nullable=False,
        ),
        "path": pa.Column(
            str,
            checks=[
                pa.Check.is_not_whitespace(error=NO_WHITESPACE_ERR),
                pa.Check(
                    lambda path: path.str.endswith((".nii", ".nii.gz")),
                    error="Path must end with a valid BIDS NIfTI file extension (.nii, .nii.gz).",
                ),
            ],
            nullable=False,
        ),
    },
    strict="filter",
)
