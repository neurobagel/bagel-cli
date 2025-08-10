import bidsschematools as bst
import pandera.pandas as pa
from pandera.typing.pandas import Series

# BIDS_SUPPORTED_SUFFIXES =
#     "FLAIR",
#     "PDT2",
#     "PDw",
#     "T1w",
#     "T2starw",
#     "T2w",
#     "UNIT1",
#     "angio",
#     "inplaneT1",
#     "inplaneT2",
#     "Chimap",
#     "M0map",
#     "MTRmap",
#     "MTVmap",
#     "MTsat",
#     "MWFmap",
#     "PDmap",
#     "R1map",
#     "R2map",
#     "R2starmap",
#     "RB1map",
#     "S0map",
#     "T1map",
#     "T1rho",
#     "T2map",
#     "T2starmap",
#     "TB1map",
#     "bold",
#     "cbv",
#     "dwi",
#     "sbref",
#     "asl",
#     "pet",
#     "svs",
#     "mrsi",
#     "unloc",
#     "mrsref",
# ]


def get_bids_supported_suffixes() -> list[str]:
    """
    Retrieve the list of supported BIDS suffixes from the BIDS schema.
    Note that the suffixes are not restricted to NIfTI data.
    """
    bids_schema = bst.schema.load_schema()
    suffixes = bids_schema["objects.suffixes"].to_dict().keys()
    return list(suffixes)


class BIDSTable(pa.DataFrameModel):
    """
    A DataFrame model for BIDS tables.
    """

    sub: str = pa.Field(
        str_startswith="sub-",
        ignore_na=False,
    )
    ses: str = pa.Field(
        str_startswith="ses-",
        ignore_na=True,
    )
    suffix: str = pa.Field(
        isin=get_bids_supported_suffixes(),
        ignore_na=False,
    )
    path: str = pa.Field(
        ignore_na=False,
    )

    @pa.check("path")
    def check_path_is_nifti(cls, path: Series[str]) -> Series[bool]:
        """
        Check if the path ends with a valid BIDS NIfTI file extension.
        """
        return path.str.endswith((".nii", ".nii.gz"))
