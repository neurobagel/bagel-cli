import json
from pathlib import Path


def load_json(input_p: Path) -> dict:
    """Load a user-specified json type file."""
    with open(input_p, "r") as f:
        return json.load(f)
