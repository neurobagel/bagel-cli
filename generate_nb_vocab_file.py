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

    class_entries = []
    for name, obj in sorted(all_classes.items()):
        class_entry = f"{mappings.NB.pf}:{name} a rdfs:Class"

        is_subclass = False
        for other_name, other_obj in all_classes.items():
            if other_obj in obj.__bases__:
                class_entry += (
                    f";\n    rdfs:subClassOf {mappings.NB.pf}:{other_name}."
                )
                is_subclass = True
                break

        if not is_subclass:
            class_entry += "."

        class_entries.append(class_entry)

    nb_vocab = "\n\n".join([PREAMBLE] + class_entries) + "\n"

    with OUTPUT_PATH.open("w") as f:
        f.write(nb_vocab)


if __name__ == "__main__":
    generate_vocab_string_from_models()
