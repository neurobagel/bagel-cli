import pytest
from click.testing import CliRunner

from bagelbids.cli import bagel


@pytest.fixture
def runner():
    return CliRunner()


def test_processing_valid_bids_data_succeeds(runner, tmp_path, bids_synthetic):
    result = runner.invoke(bagel, ["--bids_dir", bids_synthetic, 
                                   "--output_dir", tmp_path])
    assert result.exit_code == 0


def test_processing_invalid_bids_data_fails(runner, tmp_path, bids_invalid_synthetic):
    result = runner.invoke(bagel, ["--bids_dir", bids_invalid_synthetic, 
                                   "--output_dir", tmp_path])
    assert result.exit_code == 1


def test_disabling_validation(runner, tmp_path, bids_invalid_synthetic):
    result = runner.invoke(bagel, ["--bids_dir", bids_invalid_synthetic, 
                                   "--output_dir", tmp_path, 
                                   "--skip-validate"])
    assert result.exit_code == 0


def test_processing_bids_synth_creates_json(runner, bids_synthetic, tmp_path):
    result = runner.invoke(bagel, ["--bids_dir", bids_synthetic, 
                                   "--output_dir", tmp_path])
    assert result.exit_code == 0
    assert (tmp_path / "synthetic.json").is_file()