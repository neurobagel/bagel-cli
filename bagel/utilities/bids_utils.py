from pathlib import Path
from typing import Iterable

import bidsschematools.schema as bst
import pandas as pd
import pandera.pandas as pa
from typer import BadParameter

from bagel import bids_table_model, models
from bagel.logger import log_error, logger
from bagel.utilities import file_utils

# NOTE: A copy of the imaging modality vocab will likely end up in all community config directories,
# but since the contents will be the same, we always pull it from the Neurobagel config for now for simplicity.
IMAGING_MODALITIES_URL = "https://raw.githubusercontent.com/neurobagel/communities/refs/heads/main/configs/Neurobagel/imaging_modalities.json"
IMAGING_MODALITIES_PATH = (
    Path(__file__).parents[1]
    / "communities/configs/Neurobagel/imaging_modalities.json"
)

bids_schema = bst.load_schema()


def get_bids_suffix_to_std_term_mapping() -> dict[str, str]:
    """
    Fetch the standardized imaging modality vocabulary from the neurobagel/communities repository
    and return a mapping of BIDS suffixes to prefixed standardized terms.

    Returns:
        dict[str, str]: A mapping where keys are BIDS suffixes (e.g., "T1w", "bold")
                        and values are namespaced standardized terms (e.g., "nidm:T1Weighted").

    Raises:
        typer.Exit: If the vocabulary cannot be fetched from either the remote URL or local backup.
    """
    # TODO: Revisit once we cache community config files locally as part of https://github.com/neurobagel/bagel-cli/issues/493.
    # For now we revert to a local submodule backup if the request fails, but this means we might not have the latest vocab.
    bids_terms_vocab, err = file_utils.request_file(
        url=IMAGING_MODALITIES_URL, backup_path=IMAGING_MODALITIES_PATH
    )
    if bids_terms_vocab == []:
        log_error(
            logger,
            f"Failed to fetch the standardized imaging modality vocabulary required to validate your BIDS metadata. Error: {err} "
            "Please check that you have an internet connection and try again, or open an issue in https://github.com/neurobagel/bagel-cli/issues if the problem persists.",
        )
    # We only expect one term namespace in the bids_term_vocab list
    bids_terms_vocab = bids_terms_vocab[0]
    namespace_prefix = bids_terms_vocab["namespace_prefix"]
    bids_suffix_to_std_term_mapping = {}
    for term in bids_terms_vocab["terms"]:
        bids_suffix_to_std_term_mapping[term["abbreviation"]] = (
            f"{namespace_prefix}:{term['id']}"
        )

    return bids_suffix_to_std_term_mapping


def find_unrecognized_bids_file_suffixes(suffixes: pd.Series) -> list[str]:
    """Return any file suffixes that are not recognized by BIDS."""
    all_bids_suffixes = {
        bids_suffix["value"]
        for bids_suffix in bids_schema.objects.suffixes.values()
    }
    return [
        suffix
        for suffix in suffixes.unique()
        if suffix not in all_bids_suffixes
    ]


def find_unsupported_image_suffixes(
    data: pd.DataFrame, supported_suffixes: Iterable[str]
) -> list[str]:
    """Return any image file suffixes unsupported by Neurobagel that are found in the provided BIDS table."""
    return (
        data.loc[
            ~data["suffix"].isin(supported_suffixes),
            "suffix",
        ]
        .unique()
        .tolist()
    )


def check_absolute_path(dir_path: Path | None) -> Path | None:
    """
    Raise an error if the input path does not look like an absolute path.
    This is a workaround for --dataset-source-path not requiring the path to exist on the host machine
    (and thus not being able to resolve the path automatically).
    """
    # Allow POSIX-style absolute paths (e.g., "/data/...") across OSes - useful for referencing paths on remote Unix servers.
    if dir_path is not None and not (
        dir_path.is_absolute() or dir_path.as_posix().startswith("/")
    ):
        raise BadParameter(
            "Dataset source directory must be an absolute path."
        )
    return dir_path


def validate_bids_table(bids_table: pd.DataFrame):
    """Error and exit if the provided BIDS table is empty or fails schema validation."""
    try:
        bids_table_model.model.validate(bids_table)
    except pa.errors.SchemaError as err:
        rows_with_errs_msg = ""
        # When validation fails due to a column value check (e.g., as opposed to a missing column),
        # printing the row indices helps with debugging, especially for invalid empty values.
        if isinstance(err.failure_cases, pd.DataFrame):
            rows_with_errs_msg = f"Rows with error (0 = first non-header row): {err.failure_cases['index'].tolist()}. "
        log_error(
            logger,
            f"Invalid BIDS table. Error: {err}. {rows_with_errs_msg}",
        )
    if bids_table.empty:
        log_error(
            logger,
            "BIDS table is empty (only a header row was found). No imaging metadata to add.",
        )


def map_term_to_namespace(term: str, namespace: dict) -> str | bool:
    """Returns the mapped namespace term if it exists, or False otherwise."""
    return namespace.get(term, False)


def create_acquisitions(
    session_df: pd.DataFrame,
    bids_term_mapping: dict,
) -> list:
    """Parses BIDS image file suffixes for a specified session to create a list of Acquisition objects."""
    image_list = []

    for bids_file_suffix in session_df["suffix"]:
        mapped_term = map_term_to_namespace(
            term=bids_file_suffix,
            namespace=bids_term_mapping,
        )
        if mapped_term:
            image_list.append(
                models.Acquisition(
                    hasContrastType=models.Image(identifier=mapped_term)
                )
            )

    return image_list


def get_session_path(
    dataset_root: Path | None,
    bids_sub_id: str,
    session_id: str,
) -> str:
    """
    Construct the session directory or subject directory path (when there is no session ID) from the source BIDS directory path, subject ID, and session ID.
    If no source BIDS directory is available, return a relative path.
    """
    subject_path = (
        Path(dataset_root / bids_sub_id) if dataset_root else Path(bids_sub_id)
    )
    session_path = (
        subject_path / session_id if session_id.strip() != "" else subject_path
    )
    return session_path.as_posix()
