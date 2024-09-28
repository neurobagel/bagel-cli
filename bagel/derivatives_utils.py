from typing import Iterable

from bagel import mappings, models

# Shorthands for expected column names in a Nipoppy processing status file
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
        set(pipelines).difference(mappings.get_pipeline_uris())
    )
    if len(unrecognized_pipelines) > 0:
        raise LookupError(
            f"The processing status file contains unrecognized pipelines in the column '{PROC_STATUS_COLS['pipeline_name']}': "
            f"{unrecognized_pipelines}. "
            f"Allowed pipeline names are the following pipelines supported natively in Nipoppy (https://github.com/nipoppy/pipeline-catalog): \n"
            f"{mappings.get_pipeline_uris()}"
        )


def check_pipeline_versions_are_recognized(
    pipeline: str, versions: Iterable[str]
):
    """
    Check that all pipeline versions in the processing status file are supported by Nipoppy.
    Assumes that the input pipeline name is recognized.
    """
    unrecognized_versions = list(
        set(versions).difference(mappings.get_pipeline_versions()[pipeline])
    )
    if len(unrecognized_versions) > 0:
        raise LookupError(
            f"The processing status file contains unrecognized {pipeline} versions in the column '{PROC_STATUS_COLS['pipeline_version']}': {unrecognized_versions}. "
            f"Allowed {pipeline} versions are the following versions supported natively in Nipoppy (https://github.com/nipoppy/pipeline-catalog): \n"
            f"{mappings.get_pipeline_versions()[pipeline]}"
        )


def get_subject_imaging_sessions(
    jsonld_subject: models.Subject,
) -> dict:
    """
    Return a dictionary of imaging sessions for a given subject from JSONLD data,
    where the keys are the session labels and values are the session objects.
    """
    jsonld_sub_sessions_dict = {}
    for jsonld_sub_ses in getattr(jsonld_subject, "hasSession"):
        if jsonld_sub_ses.schemaKey == "ImagingSession":
            jsonld_sub_sessions_dict[jsonld_sub_ses.hasLabel] = jsonld_sub_ses

    return jsonld_sub_sessions_dict
