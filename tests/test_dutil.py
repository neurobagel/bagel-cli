import pandas as pd
import pytest

from bagel import mappings
from bagel.utilities import derivatives_utils as dutil


@pytest.mark.parametrize(
    "pipelines, unrecog_pipelines",
    [
        (["fmriprep", "pipeline1"], ["pipeline1"]),
        (["pipelineA", "pipelineB"], ["pipelineA", "pipelineB"]),
    ],
)
def test_unrecognized_pipeline_names_raise_error(pipelines, unrecog_pipelines):
    """Test that pipeline names not found in the pipeline catalog raise an informative error."""
    with pytest.raises(LookupError) as e:
        dutil.check_pipelines_are_recognized(pipelines)

    assert all(
        substr in str(e.value)
        for substr in ["unrecognized pipelines"] + unrecog_pipelines
    )


@pytest.mark.parametrize(
    "fmriprep_versions, unrecog_versions",
    [
        (["20.2.7", "vA.B"], ["vA.B"]),
        (["C.D.E", "F.G.H"], ["C.D.E", "F.G.H"]),
    ],
)
def test_unrecognized_pipeline_versions_raise_error(
    fmriprep_versions, unrecog_versions
):
    """Test that versions of a pipeline not found in the pipeline catalog raise an informative error."""
    with pytest.raises(LookupError) as e:
        dutil.check_pipeline_versions_are_recognized(
            "fmriprep", fmriprep_versions
        )

    assert all(
        substr in str(e.value)
        for substr in ["unrecognized fmriprep versions"] + unrecog_versions
    )


def test_create_completed_pipelines():
    """
    Test that completed pipelines for a subject-session are accurately identified,
    where a completed pipeline is one meeting the condition that *all* steps of that pipeline
    that were run for the session are marked with a status of "SUCCESS".
    """
    sub_ses_data = [
        [
            "01",
            "sub-01",
            "01",
            "ses-01",
            "fmriprep",
            "20.2.7",
            "step1",
            "SUCCESS",
        ],
        [
            "01",
            "sub-01",
            "01",
            "ses-01",
            "fmriprep",
            "20.2.7",
            "step2",
            "FAIL",
        ],
        [
            "01",
            "sub-01",
            "01",
            "ses-01",
            "fmriprep",
            "23.1.3",
            "default",
            "SUCCESS",
        ],
    ]
    example_ses_proc_df = pd.DataFrame.from_records(
        columns=[
            "participant_id",
            "bids_participant_id",
            "session_id",
            "bids_session_id",
            "pipeline_name",
            "pipeline_version",
            "pipeline_step",
            "status",
        ],
        data=sub_ses_data,
    )
    completed_pipelines = dutil.create_completed_pipelines(example_ses_proc_df)

    assert len(completed_pipelines) == 1
    assert (
        completed_pipelines[0].hasPipelineName.identifier
        == f"{mappings.NP.pf}:fmriprep"
    )
    assert completed_pipelines[0].hasPipelineVersion == "23.1.3"
