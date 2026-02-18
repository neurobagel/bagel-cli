import pandas as pd
import pandera.extensions as extensions
import pandera.pandas as pa

NO_WHITESPACE_ERR = (
    "Must be a non-empty value that does not contain only whitespace."
)


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
            pa.Check.is_not_whitespace(error=NO_WHITESPACE_ERR),
            nullable=False,
        ),
        "ses": pa.Column(
            str,
            nullable=True,
        ),
        "suffix": pa.Column(
            str,
            pa.Check.is_not_whitespace(error=NO_WHITESPACE_ERR),
            nullable=False,
            # NOTE: We filter out unsupported BIDS suffixes and handle them separately
        ),
        "path": pa.Column(
            str,
            pa.Check.is_not_whitespace(error=NO_WHITESPACE_ERR),
            nullable=False,
        ),
    },
    strict="filter",
)
