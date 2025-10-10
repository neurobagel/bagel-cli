import pandas as pd
import pandera.extensions as extensions
import pandera.pandas as pa

from .mappings import BIDS

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
                    list(BIDS.keys()),
                ),  # NOTE: suffixes are case-sensitive
            ],
            nullable=False,
        ),
        "path": pa.Column(
            str,
            pa.Check.is_not_whitespace(error=NO_WHITESPACE_ERR),
            nullable=False,
        ),
    },
    strict="filter",
)
