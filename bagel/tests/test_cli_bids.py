from pathlib import Path

import pytest

from bagel.cli import bagel


@pytest.fixture(scope="function")
def default_pheno_bids_output_path(tmp_path):
    "Return temporary bids command output filepath that uses the default filename."
    return tmp_path / "pheno_bids.jsonld"


def test_bids_valid_inputs_run_successfully(
    runner,
    test_data_upload_path,
    bids_synthetic,
    default_pheno_bids_output_path,
):
    """Basic smoke test for the "add-bids" subcommand"""
    result = runner.invoke(
        bagel,
        [
            "bids",
            "--jsonld-path",
            test_data_upload_path / "example_synthetic.jsonld",
            "--bids-dir",
            bids_synthetic,
            "--output",
            default_pheno_bids_output_path,
        ],
    )
    assert result.exit_code == 0, f"Errored out. STDOUT: {result.output}"
    assert (
        default_pheno_bids_output_path
    ).exists(), "The pheno_bids.jsonld output was not created."


def test_bids_sessions_have_correct_labels(
    runner,
    test_data_upload_path,
    bids_synthetic,
    default_pheno_bids_output_path,
    load_test_json,
):
    """Check that sessions added to pheno_bids.jsonld have the expected labels."""
    runner.invoke(
        bagel,
        [
            "bids",
            "--jsonld-path",
            test_data_upload_path / "example_synthetic.jsonld",
            "--bids-dir",
            bids_synthetic,
            "--output",
            default_pheno_bids_output_path,
        ],
    )

    pheno_bids = load_test_json(default_pheno_bids_output_path)
    for sub in pheno_bids["hasSamples"]:
        assert ["ses-01", "ses-02"] == [
            ses["hasLabel"] for ses in sub["hasSession"]
        ]


def test_bids_data_with_sessions_have_correct_paths(
    runner,
    test_data_upload_path,
    default_pheno_bids_output_path,
    load_test_json,
):
    """
    Check that BIDS session paths added to pheno_bids.jsonld match the parent
    session/subject labels and are absolute file paths.
    """
    runner.invoke(
        bagel,
        [
            "bids",
            "--jsonld-path",
            test_data_upload_path / "example_synthetic.jsonld",
            "--bids-dir",
            Path(__file__).parent / "../../bids-examples/synthetic",
            "--output",
            default_pheno_bids_output_path,
        ],
    )

    pheno_bids = load_test_json(default_pheno_bids_output_path)
    for sub in pheno_bids["hasSamples"]:
        for ses in sub["hasSession"]:
            assert sub["hasLabel"] in ses["hasFilePath"]
            assert ses["hasLabel"] in ses["hasFilePath"]
            assert Path(ses["hasFilePath"]).is_absolute()
            assert Path(ses["hasFilePath"]).is_dir()
