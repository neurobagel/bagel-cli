from typing import Iterable

import pandas as pd

from bagel import mappings, models
from bagel.logger import log_error, logger

# Shorthands for expected column names in a Nipoppy processing status file
# TODO: While there are multiple session ID columns in a Nipoppy processing status file,
# we only only look at `bids_session_id` right now. We should revisit this after the schema is finalized,
# to see if any other logic is needed to avoid issues with session ID discrepancies across columns.
PROC_STATUS_COLS = {
    "participant": "bids_participant_id",
    "session": "bids_session_id",
    "pipeline_name": "pipeline_name",
    "pipeline_version": "pipeline_version",
    "status": "status",
}


def get_recognized_pipelines(pipelines: Iterable[str]) -> list:
    """
    Check that all pipelines in the processing status file are supported by Nipoppy.
    Log an error if all pipelines are unrecognized, otherwise warn about unrecognized pipelines.
    """
    recognized_pipelines = list(
        set(pipelines).intersection(mappings.KNOWN_PIPELINE_URIS)
    )
    unrecognized_pipelines = list(
        set(pipelines).difference(mappings.KNOWN_PIPELINE_URIS)
    )

    unrecognized_pipelines_details = (
        f"Unrecognized processing pipelines: {unrecognized_pipelines}. "
        f"Supported pipelines are found in the Nipoppy pipeline vocabulary (https://github.com/nipoppy/pipeline-vocabulary): "
        f"{list(mappings.KNOWN_PIPELINE_URIS.keys())}"
    )
    if not recognized_pipelines:
        log_error(
            logger,
            f"The processing status file contains no recognized pipelines in the column: '{PROC_STATUS_COLS['pipeline_name']}'.\n"
            f"{unrecognized_pipelines_details}",
        )
    if unrecognized_pipelines:
        logger.warning(
            f"The processing status file contains unrecognized pipelines in the column: '{PROC_STATUS_COLS['pipeline_name']}' - "
            "these will be ignored. "
            f"{unrecognized_pipelines_details}"
        )
    return recognized_pipelines


def validate_pipeline_versions(
    pipeline: str, versions: Iterable[str]
) -> tuple[list, list]:
    """
    For a given pipeline, return the recognized and unrecognized pipeline versions in the processing status file
    based on the Nipoppy pipeline vocabulary, and return both as lists.
    """
    recognized_versions = list(
        set(versions).intersection(mappings.KNOWN_PIPELINE_VERSIONS[pipeline])
    )
    unrecognized_versions = list(
        set(versions).difference(mappings.KNOWN_PIPELINE_VERSIONS[pipeline])
    )

    return recognized_versions, unrecognized_versions


def check_at_least_one_pipeline_version_is_recognized(status_df: pd.DataFrame):
    """
    Check that at least one pipeline name and version combination found in the processing status file is supported by Nipoppy.
    """
    recognized_pipelines = get_recognized_pipelines(
        status_df[PROC_STATUS_COLS["pipeline_name"]].unique()
    )

    any_recognized_versions = False
    unrecognized_pipeline_versions = {}
    for pipeline in recognized_pipelines:
        versions = status_df[
            status_df[PROC_STATUS_COLS["pipeline_name"]] == pipeline
        ][PROC_STATUS_COLS["pipeline_version"]].unique()

        recognized_versions, unrecognized_versions = (
            validate_pipeline_versions(pipeline, versions)
        )
        if recognized_versions:
            any_recognized_versions = True
        if unrecognized_versions:
            unrecognized_pipeline_versions[pipeline] = unrecognized_versions

    unrecognized_versions_details = (
        f"Unrecognized processing pipeline versions: {unrecognized_pipeline_versions}. "
        "Supported pipeline versions are found in the Nipoppy pipeline vocabulary (https://github.com/nipoppy/pipeline-vocabulary)."
    )
    if not any_recognized_versions:
        log_error(
            logger,
            f"The processing status file contains no recognized versions of any pipelines in the column '{PROC_STATUS_COLS['pipeline_version']}'.\n"
            f"{unrecognized_versions_details}",
        )
    if unrecognized_pipeline_versions:
        logger.warning(
            f"The processing status file contains unrecognized versions of pipelines in the column '{PROC_STATUS_COLS['pipeline_version']}' - "
            "these will be ignored. "
            f"{unrecognized_versions_details}"
        )


def create_completed_pipelines(session_proc_df: pd.DataFrame) -> list:
    """
    Create a list of CompletedPipeline objects for a single subject-session based on the completion status
    info of pipelines for that session from the processing status dataframe.
    """
    completed_pipelines = []
    for (pipeline, version), session_pipe_df in session_proc_df.groupby(
        [
            PROC_STATUS_COLS["pipeline_name"],
            PROC_STATUS_COLS["pipeline_version"],
        ]
    ):
        if (
            pipeline in mappings.KNOWN_PIPELINE_URIS
            and version in mappings.KNOWN_PIPELINE_VERSIONS[pipeline]
        ) and (
            session_pipe_df[PROC_STATUS_COLS["status"]].str.lower()
            == "success"
        ).all():
            completed_pipeline = models.CompletedPipeline(
                hasPipelineName=models.Pipeline(
                    identifier=mappings.KNOWN_PIPELINE_URIS[pipeline]
                ),
                hasPipelineVersion=version,
            )
            completed_pipelines.append(completed_pipeline)

    return completed_pipelines
