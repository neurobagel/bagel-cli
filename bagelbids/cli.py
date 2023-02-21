import json
from pathlib import Path

import pandas as pd
import typer
from bids import BIDSLayout
from pydantic import ValidationError

from bagelbids import mappings, models
from bagelbids.pheno_utils import (
    are_not_missing,
    generate_context,
    get_transformed_values,
    map_categories_to_columns,
    map_tools_to_columns,
    validate_inputs,
)
from bagelbids.utility import load_json

bagel = typer.Typer()


@bagel.command()
def pheno(
    pheno: Path = typer.Option(
        ...,
        help="The path to a phenotypic .tsv file.",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    dictionary: Path = typer.Option(
        ...,
        help="The path to the .json data dictionary "
        "corresponding to the phenotypic .tsv file.",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    output: Path = typer.Option(
        ...,
        help="The directory where outputs should be created.",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    name: str = typer.Option(
        ...,
        help="A descriptive name for the dataset the input belongs to. "
        "This name is expected to match the name field in the BIDS "
        "dataset_description.json file.",
    ),
):
    """
    Process a tabular phenotypic file (.tsv) that has been successfully annotated
    with the Neurobagel annotation tool. The annotations are expected to be stored
    in a data dictionary (.json).

    This tool will create a valid, subject-level instance of the Neurobagel
    graph datamodel for the provided phenotypic file in the .jsonld format.
    You can upload this .jsonld file to the Neurobagel graph.
    """
    data_dictionary = load_json(dictionary)
    pheno_df = pd.read_csv(pheno, sep="\t")
    validate_inputs(data_dictionary, pheno_df)

    subject_list = []

    column_mapping = map_categories_to_columns(data_dictionary)
    tool_mapping = map_tools_to_columns(data_dictionary)

    # TODO: needs refactoring once we handle multiple participant IDs
    participants = column_mapping.get("participant")[0]

    for participant in pheno_df[participants].unique():
        # TODO: needs refactoring once we handle phenotypic information at the session level
        # for the moment we are not creating any session instances in the phenotypic graph
        # we treat the phenotypic information in the first row of the _sub_pheno dataframe
        # as reflecting the subject level phenotypic information
        _sub_pheno = pheno_df.query(
            f"{participants} == '{str(participant)}'"
        ).iloc[0]

        subject = models.Subject(label=str(participant))
        if "sex" in column_mapping.keys():
            subject.sex = get_transformed_values(
                column_mapping["sex"], _sub_pheno, data_dictionary
            )

        if "diagnosis" in column_mapping.keys():
            _dx_val = get_transformed_values(
                column_mapping["diagnosis"], _sub_pheno, data_dictionary
            )
            if _dx_val is None:
                pass
            elif _dx_val == mappings.NEUROBAGEL["healthy_control"]:
                subject.isSubjectGroup = mappings.NEUROBAGEL["healthy_control"]
            else:
                subject.diagnosis = [models.Diagnosis(identifier=_dx_val)]

        if "age" in column_mapping.keys():
            subject.age = get_transformed_values(
                column_mapping["age"], _sub_pheno, data_dictionary
            )

        if tool_mapping:
            _assessments = [
                models.Assessment(identifier=tool)
                for tool, columns in tool_mapping.items()
                if are_not_missing(columns, _sub_pheno, data_dictionary)
            ]
            if _assessments:
                # Only set assignments for the subject if at least one is not missing
                subject.assessment = _assessments

        subject_list.append(subject)

    dataset = models.Dataset(label=name, hasSamples=subject_list)
    context = generate_context()
    # We can't just exclude_unset here because the identifier and schemaKey
    # for each instance are created as default values and so technically are never set
    # TODO: we should revisit this because there may be reasons to have None be meaningful in the future
    context.update(**dataset.dict(exclude_none=True))

    with open(output / "pheno.jsonld", "w") as f:
        f.write(json.dumps(context, indent=2))


@bagel.command()
def add_bids(
    jsonld_path: Path = typer.Option(
        ...,
        help="The path to a pheno.jsonld file.",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    bids_dir: Path = typer.Option(
        ...,
        help="The path to the corresponding BIDS dataset directory.",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    output: Path = typer.Option(
        ...,
        help="The directory where outputs should be created",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
):
    jsonld = load_json(jsonld_path)
    layout = BIDSLayout(bids_dir, validate=True)

    context = jsonld.pop("@context")

    # NOTE: The following validation can also be performed using jsonschema.validate()
    # But Pydantic's error message is much cleaner - plus this saves a line of code!
    try:
        pheno_dataset = models.Dataset.parse_obj(jsonld)
    except ValidationError as err:
        print(err)
