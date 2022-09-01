import json
from typing import List
import warnings

import click


def is_subset(sample: List, reference: List) -> bool:
    return set(sample).issubset(set(reference))


def get_id(data: dict, mode: str = "bids") -> dict:
    if mode == "bids":
        return {sub["identifier"]: sub for sub in data["hasSamples"]}
    elif mode == "demo":
        # TODO: replace this hack and instead change the annotator output model
        return {
            sub["id"]: dict(
                identifier=sub["id"], **{key: val for (key, val) in sub.items() if not "id" in key}
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
        raise NotImplementedError(
            "The BIDS file contains subjects that don't exist in the demographc file. "
            "This is not supported. Here are the IDs:\n"
            + "\n".join(
                [str(val) for val in set(bids_json.keys()).difference(set(demo_json.keys()))]
            )
        )
    elif not is_subset(demo_json.keys(), bids_json.keys()):
        warnings.warn(
            UserWarning(
                "There are subjects in the demographics file that do not exist in the BIDS dataset! "
                "Their IDs are:\n"
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

    with open(out_path, "w") as f:
        f.write(json.dumps(merge_json(bids_json, demo_json), indent=2))


if __name__ == "__main__":
    cli()
