from pathlib import Path

from bagel.cli import bagel


def test_bids_valid_inputs_run_successfully(
    runner, test_data, bids_synthetic, tmp_path
):
    """Basic smoke test for the "add-bids" subcommand"""
    result = runner.invoke(
        bagel,
        [
            "bids",
            "--jsonld-path",
            test_data / "example_synthetic.jsonld",
            "--bids-dir",
            bids_synthetic,
            "--output",
            tmp_path,
        ],
    )
    assert result.exit_code == 0, f"Errored out. STDOUT: {result.output}"
    assert (
        tmp_path / "pheno_bids.jsonld"
    ).exists(), "The pheno_bids.jsonld output was not created."


def test_bids_sessions_have_correct_labels(
    runner,
    test_data,
    bids_synthetic,
    tmp_path,
    load_test_json,
):
    """Check that sessions added to pheno_bids.jsonld have the expected labels."""
    runner.invoke(
        bagel,
        [
            "bids",
            "--jsonld-path",
            test_data / "example_synthetic.jsonld",
            "--bids-dir",
            bids_synthetic,
            "--output",
            tmp_path,
        ],
    )

    pheno_bids = load_test_json(tmp_path / "pheno_bids.jsonld")
    for sub in pheno_bids["hasSamples"]:
        assert ["ses-01", "ses-02"] == [
            ses["hasLabel"] for ses in sub["hasSession"]
        ]


def test_bids_data_with_sessions_have_correct_paths(
    runner,
    test_data,
    tmp_path,
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
            test_data / "example_synthetic.jsonld",
            "--bids-dir",
            Path(__file__).parent / "../../bids-examples/synthetic",
            "--output",
            tmp_path,
        ],
    )

    pheno_bids = load_test_json(tmp_path / "pheno_bids.jsonld")
    for sub in pheno_bids["hasSamples"]:
        for ses in sub["hasSession"]:
            assert sub["hasLabel"] in ses["hasFilePath"]
            assert ses["hasLabel"] in ses["hasFilePath"]
            assert Path(ses["hasFilePath"]).is_absolute()
            assert Path(ses["hasFilePath"]).is_dir()
