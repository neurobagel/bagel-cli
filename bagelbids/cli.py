from pathlib import Path
from typing import Dict
import warnings

import click
from bids import BIDSLayout

from bagelbids import models, mappings


def map_term_to_namespace(term: str, namespace: Dict):
    """
    Returns the mapped namespace term if it exists, or False otherwise"""
    return namespace.get(term, False)


@click.command(
    help="The bagelbids parser\n\n"
    ""
    "Helps you to parse a BIDS dataset into a jsonld summary file that is ready for the "
    "neurobagel graph store."
)
@click.option(
    "--bids_dir",
    type=click.Path(file_okay=False, dir_okay=True, exists=True),
    help="The path to a valid BIDS directory on your system that you want to parse",
    required=True,
)
@click.option(
    "--output_dir",
    type=click.Path(file_okay=False, dir_okay=True),
    help="The path to an output directory where you want the parsed summary file to be stored.",
    required=True,
)
@click.option("--analysis_level", "level", type=click.Choice(["group"]))
@click.option("--validate/--skip-validate", default=True)
def bagel(bids_dir, output_dir, level, validate):
    # TODO setup logger
    file_name = Path(bids_dir).name
    layout = BIDSLayout(bids_dir, validate=validate)
    if layout.get_file("dataset_description.tsv") is None and not validate:
        warnings.warn(
            "The BIDS dataset_description.json file is missing."
            "We can therefore not read the BIDS dataset name."
            f"We will use the name of the BIDS directory as the dataset name: {file_name}."
        )
        bids_dataset_name = file_name
    else:
        bids_dataset_name = layout.get_dataset_description().get("Name", "Unnamed Dataset")

    subject_list = []
    for subject in layout.get_subjects():
        session_list = []
        for session in layout.get_sessions(subject=subject):
            image_list = []
            for bids_file in layout.get(
                subject=subject, session=session, extension=[".nii", ".nii.gz"]
            ):
                # If the suffix of a BIDS file is not recognized, then ignore
                mapped_term = map_term_to_namespace(
                    bids_file.get_entities().get("suffix"), namespace=mappings.NIDM
                )
                if mapped_term:
                    image_list.append(
                        models.Acquisition(
                            hasContrastType=models.Image(identifier=mapped_term),
                        )
                    )
            session_list.append(models.Session(label=session, hasAcquisition=image_list))
        # pyBIDS strips the "sub-" prefix, but we want to add it back
        subject_list.append(models.Subject(label=f"sub-{subject}", hasSession=session_list))
    dataset = models.Dataset(label=str(bids_dataset_name), hasSamples=subject_list)

    with open(Path(output_dir) / f"{file_name}.json", "w") as f:
        f.write(dataset.json(indent=2))
