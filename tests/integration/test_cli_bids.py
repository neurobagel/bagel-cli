import pandas as pd
import pytest

from bagel.cli import bagel
from tests import utils


@pytest.fixture(scope="function")
def synthetic_dataset_tsv_path(test_data):
    """Return the path to the BIDS TSV file for the bids-examples synthetic dataset."""
    return test_data / "bids_metadata_synthetic.tsv"


def test_bids_valid_inputs_run_successfully(
    runner,
    test_data_upload_path,
    synthetic_dataset_tsv_path,
    temp_output_jsonld_path,
    load_test_json,
):
    """
    Basic smoke test for the "bids" command.

    Also performs a sanity check that an @context is present in the output JSONLD
    (which should have been inherited from the input JSONLD).
    """
    result = runner.invoke(
        bagel,
        [
            "bids",
            "--jsonld-path",
            test_data_upload_path / "example_synthetic.jsonld",
            "--bids-table",
            synthetic_dataset_tsv_path,
            "--output",
            temp_output_jsonld_path,
        ],
    )
    assert result.exit_code == 0, f"Errored out. STDOUT: {result.output}"
    assert (
        temp_output_jsonld_path
    ).exists(), "The pheno_bids.jsonld output was not created."

    output = load_test_json(temp_output_jsonld_path)
    assert (
        output.get("@context") is not None
    ), "The output JSONLD is missing an @context."


def test_imaging_sessions_have_expected_labels(
    runner,
    test_data_upload_path,
    synthetic_dataset_tsv_path,
    temp_output_jsonld_path,
    load_test_json,
):
    """Check that the imaging sessions in the JSONLD output have the expected session labels."""
    runner.invoke(
        bagel,
        [
            "bids",
            "--jsonld-path",
            test_data_upload_path / "example_synthetic.jsonld",
            "--bids-table",
            synthetic_dataset_tsv_path,
            "--output",
            temp_output_jsonld_path,
        ],
    )

    output = load_test_json(temp_output_jsonld_path)

    for sub in output["hasSamples"]:
        # all subjects in the BIDS synthetic dataset are expected to have 4 sessions total
        assert 4 == len(sub["hasSession"])

        imaging_ses_labels = [
            ses["hasLabel"]
            for ses in sub["hasSession"]
            if ses["schemaKey"] == "ImagingSession"
        ]

        assert sorted(imaging_ses_labels) == ["ses-01", "ses-02"]


@pytest.mark.parametrize(
    "jsonld_path,expected_sessions_with_acq_and_pipe_metadata",
    [
        ("example_synthetic.jsonld", 0),
        (
            "pheno-derivatives-output/example_synthetic_pheno-derivatives.jsonld",
            3,
        ),
    ],
)
def test_imaging_sessions_have_expected_metadata(
    runner,
    test_data_upload_path,
    synthetic_dataset_tsv_path,
    temp_output_jsonld_path,
    load_test_json,
    jsonld_path,
    expected_sessions_with_acq_and_pipe_metadata,
):
    """
    Check that the JSONLD output contains the expected total number of imaging sessions with
    acquisition and completed pipeline metadata, based on whether a phenotypic-only JSONLD or
    JSONLD with both phenotypic and processing pipeline metadata is provided as input.
    """
    runner.invoke(
        bagel,
        [
            "bids",
            "--jsonld-path",
            test_data_upload_path / jsonld_path,
            "--bids-table",
            synthetic_dataset_tsv_path,
            "--output",
            temp_output_jsonld_path,
        ],
    )

    output = load_test_json(temp_output_jsonld_path)

    sessions_with_acq_metadata = []
    sessions_with_acq_and_pipe_metadata = []
    for sub in output["hasSamples"]:
        for ses in sub["hasSession"]:
            if (
                ses["schemaKey"] == "ImagingSession"
                and ses.get("hasAcquisition") is not None
            ):
                sessions_with_acq_metadata.append(ses)
                if ses.get("hasCompletedPipeline") is not None:
                    sessions_with_acq_and_pipe_metadata.append(ses)

    assert len(sessions_with_acq_metadata) == 10
    assert (
        len(sessions_with_acq_and_pipe_metadata)
        == expected_sessions_with_acq_and_pipe_metadata
    )


def test_imaging_sessions_have_correct_paths(
    runner,
    test_data_upload_path,
    synthetic_dataset_tsv_path,
    temp_output_jsonld_path,
    load_test_json,
):
    """
    Check that an imaging session path in the JSONLD is correctly constructed from the
    subject and session IDs from the BIDS table and the dataset root directory when provided.
    """
    runner.invoke(
        bagel,
        [
            "bids",
            "--jsonld-path",
            test_data_upload_path / "example_synthetic.jsonld",
            "--bids-table",
            synthetic_dataset_tsv_path,
            "--dataset-source-dir",
            "/public_datasets/dataset01",
            "--output",
            temp_output_jsonld_path,
        ],
    )

    pheno_bids = load_test_json(temp_output_jsonld_path)
    subject = next(
        sub for sub in pheno_bids["hasSamples"] if sub["hasLabel"] == "sub-01"
    )
    session = next(
        ses
        for ses in subject["hasSession"]
        if ses["hasLabel"] == "ses-01" and ses["schemaKey"] == "ImagingSession"
    )
    assert session["hasFilePath"] == "/public_datasets/dataset01/sub-01/ses-01"


def test_relative_source_dir_path_raises_error(
    runner,
    test_data_upload_path,
    temp_output_jsonld_path,
    disable_rich_markup,
):
    """Check that a relative source directory path raises an error."""
    result = runner.invoke(
        bagel,
        [
            "bids",
            "--jsonld-path",
            test_data_upload_path / "example_synthetic.jsonld",
            "--dataset-source-dir",
            "data/bids",
            "--output",
            temp_output_jsonld_path,
        ],
        catch_exceptions=False,
    )
    assert result.exit_code != 0
    assert "must be an absolute path" in result.output


def test_some_unsupported_suffixes_in_bids_table_raises_warning(
    runner,
    tmp_path,
    test_data_upload_path,
    temp_output_jsonld_path,
    load_test_json,
    disable_rich_markup,
    propagate_info,
    caplog,
):
    """
    Check that when the input BIDS table contains some unsupported suffixes:
    - an informative warning is logged
    - info is logged about the suffixes that WILL be added to the graph data
    - the unsupported suffixes are dropped in the graph data output
    """
    row_data = [
        [
            "sub-01",
            "ses-01",
            "unsupported1",  # unsupported_suffix
            "/data/synthetic/sub-01/anat/sub-01_ses-01_unsupported1.nii.gz",
        ],
        [
            "sub-01",
            "ses-01",
            "bold",
            "/data/synthetic/sub-01/func/sub-01_ses-01_task-rest_bold.nii.gz",
        ],
        [
            "sub-02",
            "ses-01",
            "unsupported1",  # unsupported_suffix
            "/data/synthetic/sub-02/anat/sub-02_ses-01_unsupported1.nii.gz",
        ],
        [
            "sub-02",
            "ses-01",
            "bold",
            "/data/synthetic/sub-02/func/sub-02_ses-01_task-rest_bold.nii.gz",
        ],
    ]
    bids_table = pd.DataFrame(
        row_data, columns=["sub", "ses", "suffix", "path"]
    )
    bids_table.to_csv(tmp_path / "bids.tsv", sep="\t", index=False)

    runner.invoke(
        bagel,
        [
            "bids",
            "--jsonld-path",
            test_data_upload_path / "example_synthetic.jsonld",
            "--bids-table",
            tmp_path / "bids.tsv",
            "--output",
            temp_output_jsonld_path,
        ],
        catch_exceptions=False,
    )

    output = load_test_json(temp_output_jsonld_path)
    contrasts = utils.get_values_by_key(output, "hasContrastType")
    warnings = [
        record.msg
        for record in caplog.records
        if record.levelname == "WARNING"
    ]

    assert len(warnings) == 1
    for warning_substr in [
        "suffixes unsupported by Neurobagel",
        "unsupported1",
    ]:
        assert warning_substr in warnings[0]
    for info_substr in [
        "the following Neurobagel-supported imaging modalities will be added",
        "bold",
    ]:
        assert info_substr in caplog.text
    assert all(
        contrast["identifier"] == "nidm:FlowWeighted" for contrast in contrasts
    )


def test_all_unsupported_suffixes_in_bids_table_raises_error(
    runner,
    tmp_path,
    test_data_upload_path,
    temp_output_jsonld_path,
    disable_rich_markup,
    propagate_warnings,
    caplog,
):
    """
    Check that a BIDS table containing only unsupported suffixes raises an error
    and no output JSONLD file is created.
    """
    row_data = [
        [
            "sub-01",
            "ses-01",
            "unsupported1",
            "/data/synthetic/sub-01/anat/sub-01_ses-01_unsupported1.nii.gz",
        ],
        [
            "sub-01",
            "ses-01",
            "unsupported2",
            "/data/synthetic/sub-01/func/sub-01_ses-01_unsupported2.nii.gz",
        ],
        [
            "sub-02",
            "ses-01",
            "unsupported1",
            "/data/synthetic/sub-02/anat/sub-02_ses-01_unsupported1.nii.gz",
        ],
        [
            "sub-02",
            "ses-01",
            "unsupported2",
            "/data/synthetic/sub-02/func/sub-02_ses-01_unsupported2.nii.gz",
        ],
    ]
    bids_table = pd.DataFrame(
        row_data, columns=["sub", "ses", "suffix", "path"]
    )
    bids_table.to_csv(tmp_path / "bids.tsv", sep="\t", index=False)

    result = runner.invoke(
        bagel,
        [
            "bids",
            "--jsonld-path",
            test_data_upload_path / "example_synthetic.jsonld",
            "--bids-table",
            tmp_path / "bids.tsv",
            "--output",
            temp_output_jsonld_path,
        ],
        catch_exceptions=False,
    )

    assert result.exit_code != 0
    assert not temp_output_jsonld_path.exists()
    assert len(caplog.records) == 1
    assert "No Neurobagel-supported BIDS suffixes found" in caplog.text


def test_bids_table_missing_required_columns_exits_gracefully(
    runner,
    tmp_path,
    test_data_upload_path,
    temp_output_jsonld_path,
    disable_rich_markup,
    propagate_errors,
    caplog,
):
    """Test that the bids command exits gracefully when provided a BIDS table missing a required column."""
    bids_table = pd.DataFrame(
        [
            [
                "sub-01",
                "ses-01",
                "/data/synthetic/sub-01/anat/sub-01_ses-01_T1w.nii",
            ],
            [
                "sub-01",
                "ses-01",
                "/data/synthetic/sub-01/func/sub-01_ses-01_task-rest_bold.nii",
            ],
            [
                "sub-02",
                "ses-01",
                "/data/synthetic/sub-02/ses-01/anat/sub-02_ses-01_T1w.nii",
            ],
            [
                "sub-02",
                "ses-01",
                "/data/synthetic/sub-02/ses-01/func/sub-02_ses-01_task-rest_bold.nii",
            ],
        ],
        columns=["sub", "ses", "path"],  # missing 'suffix' column
    )
    bids_table.to_csv(tmp_path / "bids.tsv", sep="\t", index=False)

    result = runner.invoke(
        bagel,
        [
            "bids",
            "--jsonld-path",
            test_data_upload_path / "example_synthetic.jsonld",
            "--bids-table",
            tmp_path / "bids.tsv",
            "--output",
            temp_output_jsonld_path,
        ],
        catch_exceptions=False,
    )

    assert result.exit_code != 0
    assert not temp_output_jsonld_path.exists()
    assert len(caplog.records) == 1
    assert "Invalid BIDS table" in caplog.text
    assert "suffix" in caplog.text


def test_no_error_when_bids_table_id_columns_have_no_prefixes(
    runner, tmp_path, test_data, temp_output_jsonld_path, load_test_json
):
    """
    Test that when BIDS table 'sub' and 'ses' columns do not include "sub-" and "ses-" prefixes, respectively,
    the bids command runs successfully and IDs in the output JSONLD also do not include these prefixes.
    """
    bids_table = pd.DataFrame(
        [
            [
                "01",
                "01",
                "T1w",
                "/data/synthetic/sub-01/ses-01/anat/sub-01_ses-01_T1w.nii.gz",
            ],
            [
                "01",
                "01",
                "bold",
                "/data/synthetic/sub-01/ses-01/func/sub-01_ses-01_task-nback_run-01_bold.nii.gz",
            ],
            [
                "02",
                "01",
                "T1w",
                "/data/synthetic/sub-02/ses-01/anat/sub-02_ses-01_T1w.nii.gz",
            ],
            [
                "02",
                "01",
                "bold",
                "/data/synthetic/sub-02/ses-01/func/sub-02_ses-01_task-nback_run-01_bold.nii.gz",
            ],
        ],
        columns=["sub", "ses", "suffix", "path"],
    )
    bids_table.to_csv(tmp_path / "bids.tsv", sep="\t", index=False)

    result = runner.invoke(
        bagel,
        [
            "bids",
            "--jsonld-path",
            test_data / "example_synthetic_no_id_prefixes.jsonld",
            "--bids-table",
            tmp_path / "bids.tsv",
            "--output",
            temp_output_jsonld_path,
        ],
        catch_exceptions=False,
    )

    output = load_test_json(temp_output_jsonld_path)

    output_sub_ids = set()
    output_ses_ids = set()
    for sub in output["hasSamples"]:
        output_sub_ids.add(sub["hasLabel"])
        for ses in sub["hasSession"]:
            output_ses_ids.add(ses["hasLabel"])

    assert result.exit_code == 0
    assert temp_output_jsonld_path.exists()
    assert all(not item.startswith("sub-") for item in output_sub_ids)
    assert all(not item.startswith("ses-") for item in output_ses_ids)
