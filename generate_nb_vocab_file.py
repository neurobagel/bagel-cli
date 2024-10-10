import inspect
from pathlib import Path

import pydantic

from bagel import mappings, models

EXCLUDE_CLASSES = ["Bagel", "BaseModel"]
PREAMBLE = "\n".join(
    [
        "@prefix nb: <http://neurobagel.org/vocab/>.",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>.",
    ]
)
OUTPUT_PATH = Path.cwd() / "nb_vocab.ttl"


def generate_vocab_string_from_models():
    all_classes = {
        name: obj
        for name, obj in inspect.getmembers(models)
        if inspect.isclass(obj)
        and issubclass(obj, pydantic.BaseModel)
        and name not in EXCLUDE_CLASSES
    }
    nb_vocab = ""

    for count, (name, obj) in enumerate(sorted(all_classes.items())):
        class_entry = f"{mappings.NB.pf}:{name}\n" "    a rdfs:Class"

        is_subclass = False
        for other_name, other_obj in all_classes.items():
            if name != other_name and issubclass(obj, other_obj):
                class_entry += (
                    f";\n    rdfs:subClassOf {mappings.NB.pf}:{other_name}."
                )
                is_subclass = True
                break

        if not is_subclass:
            class_entry += "."

        nb_vocab += class_entry + (
            "\n\n" if count != (len(all_classes) - 1) else ""
        )

    nb_vocab_full = PREAMBLE + "\n\n" + nb_vocab

    with OUTPUT_PATH.open("w") as f:
        f.write(nb_vocab_full)


if __name__ == "__main__":
    generate_vocab_string_from_models()
