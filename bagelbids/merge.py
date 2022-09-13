import json
from typing import List
import warnings

import click

from bagelbids import models


def generate_context():
    # Direct copy of the dandi-schema context generation function
    # https://github.com/dandi/dandi-schema/blob/c616d87eaae8869770df0cb5405c24afdb9db096/dandischema/metadata.py
    import pydantic

    field_preamble = {"bagel": "http://neurobagel.org/vocab/"}
    fields = {}
    for val in dir(models):
        klass = getattr(models, val)
        if not isinstance(klass, pydantic.main.ModelMetaclass):
            continue
        fields[klass.__name__] = "bagel:" + klass.__name__
        for name, field in klass.__fields__.items():
            if name == "schemaKey":
                fields[name] = "@type"
            elif name == "identifier":
                fields[name] = "@id"
            elif name not in fields:
                fields[name] = {"@id": "bagel:" + name}

    field_preamble.update(**fields)

    return {"@context": field_preamble}


def is_subset(sample: List, reference: List) -> bool:
    return set(sample).issubset(set(reference))


def get_id(data: dict, mode: str = "bids") -> dict:
    if mode == "bids":
        return {sub["label"]: sub for sub in data["hasSamples"]}
    elif mode == "demo":
        # TODO: replace this hack and instead change the annotator output model
        return {
            sub["id"]: dict(
                label=sub["id"], **{key: val for (key, val) in sub.items() if "id" not in key}
            )
            for sub in data["subjects"]
        }
    else:
        raise NotImplementedError(f"Mode {mode} is not supported.")


def merge_on_subject(bids_json: dict, demo_json: dict) -> list:
    """_summary_

    Args:
        bids_json (dict): _description_
        demo_json (dict): _description_

    Returns:
        dict: _description_
    """
    if not is_subset(bids_json.keys(), demo_json.keys()):
        warnings.warn(
            Warning(
                "There is a mismatch between the BIDS and the demographic data.\n"
                "The following subjects are only present in the BIDS data, "
                "but not in the demographic data. They will be removed:\n"
                + "\n".join(
                    [str(val) for val in set(bids_json.keys()).difference(set(demo_json.keys()))]
                )
            )
        )
        for diff_sub in set(bids_json.keys()).difference(demo_json.keys()):
            bids_json.pop(diff_sub)

    if not is_subset(demo_json.keys(), bids_json.keys()):
        warnings.warn(
            Warning(
                "There are subjects in the demographics file "
                "that do not exist in the BIDS dataset! Their IDs are:\n"
                + "\n".join(
                    [str(val) for val in set(demo_json.keys()).difference(set(bids_json.keys()))]
                )
            )
        )

    return [dict(sub_obj, **demo_json[sub_id]) for (sub_id, sub_obj) in bids_json.items()]


def merge_json(bids_json: dict, demo_json: dict) -> dict:
    bids_index = get_id(bids_json, mode="bids")
    demo_index = get_id(demo_json, mode="demo")
    bids_json["hasSamples"] = merge_on_subject(bids_index, demo_index)

    return bids_json


@click.command(
    help="Tool to merge two neurobagel .json files\n\n"
    "Will take  a json file for a BIDS directory and merge it with a json file"
    "for a demographic file. Generates a jsonld file to upload to the graph."
)
@click.option(
    "--bids_path",
    type=click.Path(file_okay=True, dir_okay=False, exists=True),
    help="The path to a json file that represents a parsed BIDS directory",
    required=True,
)
@click.option(
    "--demo_path",
    type=click.Path(file_okay=True, dir_okay=False, exists=True),
    help="The path to a json file that represents a parsed participants file",
    required=True,
)
@click.option(
    "--out_path",
    type=click.Path(file_okay=True),
    help="The output path",
    required=False,
)
def cli(bids_path, demo_path, out_path):
    bids_json = json.load(open(bids_path))
    demo_json = json.load(open(demo_path))

    context = generate_context()

    # TODO: revisit this implementation. It is concerningly implicit
    # we instantiate the datamodel here for two purposes: validation,
    # and to add uuids if they don't exist yet
    model = models.Dataset.parse_obj(merge_json(bids_json, demo_json))
    context.update(**model.dict())

    with open(out_path, "w") as f:
        f.write(json.dumps(context, indent=2))


if __name__ == "__main__":
    cli()
