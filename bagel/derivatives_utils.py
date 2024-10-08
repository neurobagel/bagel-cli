from typing import Iterable

import pandas as pd

from bagel import mappings, models

# Shorthands for expected column names in a Nipoppy processing status file
# TODO: While there are multiple session ID columns in a Nipoppy processing status file,
# we only only look at `bids_session` right now. We should revisit this after the schema is finalized,
# to see if any other logic is needed to avoid issues with session ID discrepancies across columns.
PROC_STATUS_COLS = {
    "participant": "bids_participant",
    "session": "bids_session",
    "pipeline_name": "pipeline_name",
    "pipeline_version": "pipeline_version",
    "status": "status",
}


def check_pipelines_are_recognized(pipelines: Iterable[str]):
    """Check that all pipelines in the processing status file are supported by Nipoppy."""
    unrecognized_pipelines = list(
        set(pipelines).difference(mappings.KNOWN_PIPELINE_URIS)
    )
    if len(unrecognized_pipelines) > 0:
        raise LookupError(
            f"The processing status file contains unrecognized pipelines in the column '{PROC_STATUS_COLS['pipeline_name']}': "
            f"{unrecognized_pipelines}. "
            f"Allowed pipeline names are the following pipelines supported natively in Nipoppy (https://github.com/nipoppy/pipeline-catalog): \n"
            f"{mappings.KNOWN_PIPELINE_URIS}"
        )


def check_pipeline_versions_are_recognized(
    pipeline: str, versions: Iterable[str]
):
    """
    Check that all pipeline versions in the processing status file are supported by Nipoppy.
    Assumes that the input pipeline name is recognized.
    """
    unrecognized_versions = list(
        set(versions).difference(mappings.KNOWN_PIPELINE_VERSIONS[pipeline])
    )
    if len(unrecognized_versions) > 0:
        raise LookupError(
            f"The processing status file contains unrecognized {pipeline} versions in the column '{PROC_STATUS_COLS['pipeline_version']}': {unrecognized_versions}. "
            f"Allowed {pipeline} versions are the following versions supported natively in Nipoppy (https://github.com/nipoppy/pipeline-catalog): \n"
            f"{mappings.KNOWN_PIPELINE_VERSIONS[pipeline]}"
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
        # Check that all pipeline steps have succeeded
        if (
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
