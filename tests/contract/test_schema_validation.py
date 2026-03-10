"""Contract schema validation tests.

Ensures the v1 mission bundle contract schemas are correct and that
example artifacts conform to them.
"""

import csv
import json
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = REPO_ROOT / "contract" / "v1"
EXAMPLE_DIR = SCHEMA_DIR / "example"


@pytest.fixture
def manifest_schema():
    with open(SCHEMA_DIR / "manifest.schema.json") as f:
        return json.load(f)


@pytest.fixture
def example_manifest():
    with open(EXAMPLE_DIR / "manifest.json") as f:
        return json.load(f)


@pytest.fixture
def images_schema():
    with open(SCHEMA_DIR / "images.schema.json") as f:
        return json.load(f)


# ---- Tests ----


def test_example_manifest_validates(manifest_schema, example_manifest):
    """Example manifest.json must pass schema validation."""
    jsonschema.validate(instance=example_manifest, schema=manifest_schema)


def test_manifest_rejects_missing_required(manifest_schema, example_manifest):
    """Removing a required field must cause a validation error."""
    incomplete = {k: v for k, v in example_manifest.items() if k != "mission_id"}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=incomplete, schema=manifest_schema)


def test_contract_version_is_v1(manifest_schema, example_manifest):
    """Contract version must be pinned to 'v1'."""
    assert example_manifest["contract_version"] == "v1"

    bad = {**example_manifest, "contract_version": "v2"}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=bad, schema=manifest_schema)


def test_manifest_without_survey_validates(manifest_schema, example_manifest):
    """Manifest without the optional survey section must still validate."""
    no_survey = {k: v for k, v in example_manifest.items() if k != "survey"}
    jsonschema.validate(instance=no_survey, schema=manifest_schema)


def test_checksums_digest_required(manifest_schema, example_manifest):
    """checksums_digest is required — enforces the integrity chain."""
    no_digest = {k: v for k, v in example_manifest.items() if k != "checksums_digest"}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=no_digest, schema=manifest_schema)


def test_images_csv_columns_match_schema(images_schema):
    """CSV header row must match the column names defined in the images schema."""
    column_defs = images_schema["default"]["columns"]
    expected_headers = [col["name"] for col in column_defs]

    with open(EXAMPLE_DIR / "images.csv", newline="") as f:
        reader = csv.reader(f)
        actual_headers = next(reader)

    assert actual_headers == expected_headers, (
        f"CSV headers do not match schema.\n"
        f"  Expected: {expected_headers}\n"
        f"  Actual:   {actual_headers}"
    )
