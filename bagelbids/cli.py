from pathlib import Path
import json

import click
from bids import BIDSLayout

from bagelbids import models


def generate_context():
    # Direct copy of the dandi-schema context generation function
    # https://github.com/dandi/dandi-schema/blob/c616d87eaae8869770df0cb5405c24afdb9db096/dandischema/metadata.py
    import pydantic
    
    field_preamble = {
        "bagel": "http://neurobagel.org/vocab"
    }
    fields = {}
    for val in dir(models):
        klass = getattr(models, val)
        if not isinstance(klass, pydantic.main.ModelMetaclass):
            continue
        fields[klass.__name__] = "bagel:" + klass.__name__
        for name, field in klass.__fields__.items():
            if name == "schemaKey":
                fields[name] = "@type"
            elif name not in fields:
                fields[name] = {"@id": "bagel:" + name}
                
    field_preamble.update(**fields)
                
    return {"@context": field_preamble}
    


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
                image_list.append(models.Imaging(hasContrastType=bids_file.get_entities().get("suffix")))
            session_list.append(models.Session(identifier=session, hasAcquisition=image_list))
        subject_list.append(models.Subject(identifier=subject, hasSession=session_list))
    dataset = models.Dataset(identifier=str(bids_dataset_name), hasSamples=subject_list)

    context = generate_context()
    
    with open(Path(output_dir) / f"{bids_dataset_name}.json", "w") as f:
        f.write(dataset.json(indent=2))
        
    with open(Path(output_dir) / f"bagelbids_context.json", "w") as f:
        f.write(json.dumps(context, indent=2))
        
    context.update(**dataset.dict())
    
    with open(Path(output_dir) / f"{bids_dataset_name}.jsonld", "w") as f:
        f.write(json.dumps(context, indent=2))