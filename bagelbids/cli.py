from pathlib import Path

import click
from bids import BIDSLayout

from bagelbids.models import Dataset, Imaging, Session, Subject


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
@click.option('--validate/--skip-validate', default=True)
def bagel(bids_dir, output_dir, level, validate):
    # TODO setup logger
    bids_dataset_name = Path(bids_dir).name
    layout = BIDSLayout(bids_dir, validate=validate)
    subjects = layout.get_subjects()

    subject_list = []
    for subject in subjects:
        session_list = []
        for session in layout.get_sessions(subject=subject):
            image_list = []
            for bids_file in layout.get(
                subject=subject, session=session, extension=[".nii", ".nii.gz"]
            ):
                image_list.append(Imaging(hasContrastType=bids_file.get_entities().get("suffix")))
            session_list.append(Session(id=session, hasAcquisition=image_list))
        subject_list.append(Subject(id=subject, hasSession=session_list))
    dataset = Dataset(id=str(bids_dataset_name), hasSamples=subject_list)

    with open(Path(output_dir) / f"{bids_dataset_name}.json", "w") as f:
        f.write(dataset.json(indent=2))
