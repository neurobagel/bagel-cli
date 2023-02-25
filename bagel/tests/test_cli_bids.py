from collections import Counter
from contextlib import nullcontext as does_not_raise

import pytest
from bids import BIDSLayout

from bagel.cli import bagel, check_unique_bids_subjects, create_acquisitions


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
            ses["label"] for ses in sub["hasSession"]
        ]


@pytest.mark.parametrize(
    "bids_list, expectation",
    [
        (["sub-01", "sub-02", "sub-03"], does_not_raise()),
        (
            ["sub-01", "sub-02", "sub-03", "sub-04", "sub-05"],
            pytest.raises(LookupError),
        ),
        (
            ["sub-cbm001", "sub-cbm002", "sub-cbm003"],
            pytest.raises(LookupError),
        ),
    ],
)
def test_check_unique_bids_subjects_err(bids_list, expectation):
    """
    Given a list of BIDS subject IDs, raise an error or not depending on
    whether all IDs are found in the phenotypic subject list.
    """
    pheno_list = ["sub-01", "sub-02", "sub-03", "sub-PD123", "sub-PD234"]

    with expectation:
        check_unique_bids_subjects(
            pheno_subjects=pheno_list, bids_subjects=bids_list
        )


@pytest.mark.parametrize(
    "bids_dir, acquisitions, bids_session",
    [
        (
            "synthetic",
            {"nidm:T1Weighted": 1, "nidm:FlowWeighted": 3},
            "01",
        ),
        (
            "ds001",
            {
                "nidm:T2Weighted": 1,
                "nidm:T1Weighted": 1,
                "nidm:FlowWeighted": 3,
            },
            None,
        ),
        ("eeg_ds000117", {"nidm:T1Weighted": 1}, None),
    ],
)
def test_create_acquisitions(bids_path, bids_dir, acquisitions, bids_session):
    """Given a BIDS dataset, creates a list of acquisitions matching the image files found on disk."""
    image_list = create_acquisitions(
        layout=BIDSLayout(bids_path / bids_dir, validate=True),
        bids_sub_id="01",
        session=bids_session,
    )

    image_counts = Counter(
        [image.hasContrastType.identifier for image in image_list]
    )

    for contrast, count in acquisitions.items():
        assert image_counts[contrast] == count
