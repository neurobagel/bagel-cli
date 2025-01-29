# This is an example script for generating a JSON schema for the Neurobagel data dictionary model.
# Example usage: python generate_dictionary_jsonschema.py

import json

from bagel.dictionary_models import DataDictionary

FPATH = "neurobagel_datadictionary.schema.json"

with open(FPATH, "w") as f:
    f.write(json.dumps(DataDictionary.model_json_schema(), indent=2))
