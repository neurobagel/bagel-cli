"""
Test the command line interface function to merge a BIDS and demographic json file.
"""
import json
import re
from pathlib import Path
import warnings

import pytest
from click.testing import CliRunner
from pydantic import ValidationError
import uuid

from bagelbids.merge import cli, get_id, merge_on_subject, merge_json
from bagelbids import models


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def bids_json():
    return {
        "hasSamples": [
            {"label": 1, "extra_key": "one"},
            {"label": 2, "extra_key": "two"},
        ],
        "schemaKey": "Dataset",
        "label": "BIDS dataset",
    }


@pytest.fixture
def bids_json_long(bids_json):
    return dict(
        bids_json, **{"hasSamples": bids_json["hasSamples"] + [{"label": 3, "extra_key": "three"}]}
    )


@pytest.fixture
def demo_json():
    return {"subjects": [{"id": 1, "special_key": "one"}, {"id": 2, "special_key": "two"}]}


@pytest.fixture
def demo_json_long(demo_json):
    return {"subjects": demo_json["subjects"] + [{"id": 99, "special_key": "three"}]}


@pytest.fixture
def bids_json_path(bids_json, tmp_path):
    """Creates a temporary example json file that looks like a json file that could be
    generated by bagelbids from a BIDS directory.
    """
    json_path = tmp_path / "bids_json.json"
    with open(json_path, "w") as f:
        f.write(json.dumps(bids_json))
    return json_path


@pytest.fixture
def demo_json_path(demo_json, tmp_path):
    """Creates a temporary example json file that looks like a file that could be generated
    by the neurobagel annotator from a participants.tsv file
    """
    json_path = tmp_path / "demo_json.json"
    with open(json_path, "w") as f:
        f.write(json.dumps(demo_json))
    return json_path


@pytest.fixture
def target_json():
    return {
        "hasSamples": [
            {"label": 1, "extra_key": "one", "special_key": "one"},
            {"label": 2, "extra_key": "two", "special_key": "two"},
        ],
        "schemaKey": "Dataset",
        "label": "BIDS dataset",
    }


def test_merge_creates_valid_data_model(runner, bids_json_path, demo_json_path, tmp_path):
    """When I load the output of the merge CLI and use it to instantiate the pydantic
    model, then the pydantic model will not raise a validation error / will be valid."""
    result = runner.invoke(
        cli,
        [
            "--bids_path",
            bids_json_path,
            "--demo_path",
            demo_json_path,
            "--out_path",
            tmp_path / "my_output.jsonld",
        ],
    )
    assert result.exit_code == 0
    with open(tmp_path / "my_output.jsonld", "r") as f:
        result = json.load(f)

    try:
        models.Dataset.parse_obj(result)
    except ValidationError as e:
        pytest.fail(f"The output of the merge CLI was not a valid dataset model: {e}")


def test_get_id_unsupported_mode_fails():
    with pytest.raises(NotImplementedError):
        get_id({}, "does_not_exist_mode")


def test_get_id(bids_json, demo_json):
    target_bids = {
        1: {"label": 1, "extra_key": "one"},
        2: {"label": 2, "extra_key": "two"},
    }
    target_demo = {
        1: {"label": 1, "special_key": "one"},
        2: {"label": 2, "special_key": "two"},
    }
    result_bids = get_id(bids_json, mode="bids")
    result_demo = get_id(demo_json, mode="demo")
    assert result_bids == target_bids
    assert result_demo == target_demo


def test_merge_subject_lists():
    # I give two label indexed dicts
    # and I expect to get a single, merged dict back that contains both
    bids_example = {1: {"label": 1, "extra_key": 1}, 2: {"label": 2, "extra_key": 2}}
    demo_example = {1: {"label": 1, "special_key": 1}, 2: {"label": 2, "special_key": 2}}
    target = [
        {"label": 1, "extra_key": 1, "special_key": 1},
        {"label": 2, "extra_key": 2, "special_key": 2},
    ]

    result = merge_on_subject(bids_example, demo_example)

    assert result == target


def test_merge_json(bids_json, demo_json, target_json):
    result = merge_json(bids_json, demo_json)
    assert result == target_json


def test_merge_if_demo_has_additional_subjects(bids_json, demo_json_long, target_json):
    # If there are more subjects in the demo file than the BIDS dataset
    # we expect a warning that includes the subject IDs that will be stripped
    with pytest.warns(Warning, match=r"99"):
        result = merge_json(bids_json, demo_json_long)
    assert result == target_json


def test_merge_if_bids_has_additional_subjects(bids_json_long, demo_json, target_json):
    # If there are more subjects in the BIDS dataset than in the demographic file
    # We will strip these subjects and we expect a warning that includes the
    # subject IDs that will be stripped.

    with pytest.warns(
        Warning,
        match=r"(?P<mismatch>There is a mismatch)(?:.+\n+.+)(?P<type>only present in the BIDS data)(?:.+\n+)(?P<sub>3)",
    ):
        result = merge_json(bids_json_long, demo_json)
    assert result == target_json


def test_merge_if_bids_and_demo_have_additional_subjects(
    bids_json_long, demo_json_long, target_json
):
    # If both the BIDS and the demographic file have additional subjects,
    # then we expect to get their intersection and remove any subject that is
    # unique to either file. Every time subjects are removed, a warning is expected
    with pytest.warns(Warning) as warning_record:
        result = merge_json(bids_json_long, demo_json_long)

    assert re.match(
        r"(?P<mismatch>There is a mismatch)(?:.+\n+.+)(?P<type>only present in the BIDS data)(?:.+\n+)(?P<sub>3)",
        warning_record[0].message.args[0],
    )
    assert re.match(r"(.+\n+)(99)", warning_record[1].message.args[0])
    assert result == target_json


def test_merged_subjects_have_uuid_identifiers(runner, bids_json_path, demo_json_path, tmp_path):
    """In the merged jsonld file every entity should have a UUID with a bagel namespace
    so that it does not get a blank node in the graph.
    """
    result = runner.invoke(
        cli,
        [
            "--bids_path",
            bids_json_path,
            "--demo_path",
            demo_json_path,
            "--out_path",
            tmp_path / "my_output.jsonld",
        ],
    )
    with open(tmp_path / "my_output.jsonld", "r") as f:
        result = json.load(f)

    # We just confirm that the identifier exists and contains the right name space
    try:
        for subject in result["hasSamples"]:
            # If the identifier string is a valid UUID then we can cast it to a UUID object
            uuid.UUID(subject.get("identifier").split(":")[1], version=4)
    except ValueError:
        pytest.fail("At least one subject does not have a valid UUID identifier")
