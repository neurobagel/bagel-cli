import json

import click



def get_id(data: dict, mode: str = 'bids') -> dict:
    if mode == 'bids':
        return {sub['identifier']: sub for sub in data['hasSamples']}
    elif mode == 'demo':
        # TODO: replace this hack and instead change the annotator output model
        return {sub['id']: dict(identifier=sub['id'], 
                                **{key: val for (key, val) in sub.items() if not 'id' in key})
                for sub in data['subjects']}
    else:
        raise NotImplementedError(f'Mode {mode} is not supported.')


def merge_on_subject(bids_json: dict, demo_json: dict) -> list:
    """_summary_

    Args:
        bids_json (dict): _description_
        demo_json (dict): _description_

    Returns:
        dict: _description_
    """
    # TODO: ensure mismatched IDs can error out nicely
    return [dict(sub_obj, **demo_json[sub_id])
            for (sub_id, sub_obj) in bids_json.items()]
    
    
def merge_json(bids_json: dict, demo_json: dict) -> dict:
    bids_index = get_id(bids_json, mode='bids')
    demo_index = get_id(demo_json, mode='demo')
    bids_json['hasSamples'] = merge_on_subject(bids_index, demo_index)
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
    
    with open(out_path, 'w') as f:
        f.write(json.dumps(merge_json(bids_json, demo_json), indent=2))
        
        
        
if __name__ == "__main__":
    cli()
