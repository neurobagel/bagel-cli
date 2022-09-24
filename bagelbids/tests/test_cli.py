import json

import pytest
from click.testing import CliRunner

from bagelbids.cli import bagel, map_term_to_namespace
from bagelbids.mappings import NIDM


@pytest.fixture
def runner():
    return CliRunner()


def test_processing_valid_bids_data_succeeds(runner, tmp_path, bids_synthetic):
    result = runner.invoke(bagel, ["--bids_dir", bids_synthetic, "--output_dir", tmp_path])
    assert result.exit_code == 0


def test_processing_invalid_bids_data_fails(runner, tmp_path, bids_invalid_synthetic):
    result = runner.invoke(bagel, ["--bids_dir", bids_invalid_synthetic, "--output_dir", tmp_path])
    assert result.exit_code == 1


def test_disabling_validation(runner, tmp_path, bids_invalid_synthetic):
    result = runner.invoke(
        bagel, ["--bids_dir", bids_invalid_synthetic, "--output_dir", tmp_path, "--skip-validate"]
    )
    assert result.exit_code == 0


def test_processing_bids_synth_creates_json(runner, bids_synthetic, tmp_path):
    result = runner.invoke(bagel, ["--bids_dir", bids_synthetic, "--output_dir", tmp_path])
    assert result.exit_code == 0
    assert (tmp_path / "synthetic.json").is_file()


def test_that_subject_id_includes_the_full_sub_prefix(runner, bids_synthetic, tmp_path):
    runner.invoke(bagel, ["--bids_dir", bids_synthetic, "--output_dir", tmp_path])
    with open(tmp_path / "synthetic.json", "r") as f:
        bids_json = json.load(f)

    subs = [sub for sub in bids_json["hasSamples"] if "sub-04" in sub["label"]]
    assert len(subs) == 1, "We did not find a subject with the name of sub-04"
    assert set(["01", "02"]).issubset(
        [ses["label"] for ses in subs[0]["hasSession"]]
    ), "The expected sessions are not found for subject 04"


def test_BIDS_suffix_gets_mapped_to_NIDM():
    bids_term = "T1w"
    mapping_target = "nidm:T1Weighted"
    result = map_term_to_namespace(bids_term, NIDM)

    assert mapping_target == result


def test_that_bad_suffix_returns_False():
    not_a_bids_term = "superMRI"

    assert map_term_to_namespace(not_a_bids_term, NIDM) is False


def test_BIDS_suffix_mapped_in_output(runner, bids_synthetic, tmp_path):
    runner.invoke(bagel, ["--bids_dir", bids_synthetic, "--output_dir", tmp_path])
    with open(tmp_path / "synthetic.json", "r") as f:
        bids_json = json.load(f)

    # We know that the synthetic dataset has some T1w scans, so we expect at
    # least one of them to have the correct NIDM term
    assert "nidm:T1Weighted" in [
        acq["hasContrastType"].get("identifier")
        for sub in bids_json["hasSamples"]
        for ses in sub["hasSession"]
        for acq in ses["hasAcquisition"]
    ]
