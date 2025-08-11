import bidsschematools as bst
import pandas as pd
import pandera.extensions as extensions
import pandera.pandas as pa

NO_WHITESPACE_ERR = (
    "Value must not be an empty string or contain only whitespace."
)


def get_bids_supported_suffixes() -> list[str]:
    """
    Retrieve the list of supported BIDS suffixes from the BIDS schema.
    Note that the suffixes are not restricted to NIfTI data.
    """
    bids_schema = bst.schema.load_schema()
    suffixes = bids_schema["objects.suffixes"].to_dict().keys()
    return list(suffixes)


@extensions.register_check_method()
def is_not_whitespace(pd_series: pd.Series) -> pd.Series:
    """
    Check that column values are not empty strings or whitespace.
    TODO: Should non-empty strings with leading/trailing whitespace also fail validation?
    """
    return pd_series.str.strip() != ""


bids_table_model = pa.DataFrameSchema(
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
                pa.Check.isin(get_bids_supported_suffixes()),
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
    }
)
