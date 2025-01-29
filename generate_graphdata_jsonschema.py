# This is an example script for generating a JSON schema for the Neurobagel graph data model (i.e., the model for a Neurobagel "Dataset").
# Example usage: python generate_graphdata_jsonschema.py

import json

from bagel.models import Dataset

FPATH = "neurobagel_graphdata.schema.json"

with open(FPATH, "w") as f:
    f.write(
        json.dumps(
            Dataset.model_json_schema(),
            indent=2,
        )
    )
