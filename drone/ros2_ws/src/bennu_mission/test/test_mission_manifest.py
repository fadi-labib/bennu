"""Tests for mission manifest generator."""

import csv
import io
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from bennu_mission.mission_manifest import ManifestGenerator


def _make_image(seq, score=0.9, flags="ok", rtk="RTK_FIXED", ts="2026-03-15T10:32:00Z"):
    """Create a fake image metadata object."""
    return SimpleNamespace(
        sequence=seq,
        filename=f"{seq:04d}_rgb.jpg",
        sensor="rgb",
        timestamp_utc=ts,
        lat=55.6761,
        lon=12.5683,
        alt_msl=80.0,
        alt_agl=75.0,
        heading_deg=90.0,
        pitch_deg=-90.0,
        roll_deg=0.0,
        rtk_fix_type=rtk,
        position_accuracy_m=0.05,
        gsd_cm=2.1,
        quality_score=score,
        quality_flags=flags,
        ambient_light_lux=None,
        capture_offset_ms=None,
        to_csv_dict=lambda s=seq, sc=score, f=flags, r=rtk, t=ts: {
            "sequence": s,
            "filename": f"{s:04d}_rgb.jpg",
            "sensor": "rgb",
            "timestamp_utc": t,
            "lat": 55.6761,
            "lon": 12.5683,
            "alt_msl": 80.0,
            "alt_agl": 75.0,
            "heading_deg": 90.0,
            "pitch_deg": -90.0,
            "roll_deg": 0.0,
            "rtk_fix_type": r,
            "position_accuracy_m": 0.05,
            "gsd_cm": 2.1,
            "quality_score": sc,
            "quality_flags": f,
            "ambient_light_lux": None,
            "capture_offset_ms": None,
        },
    )


def test_manifest_matches_schema():
    """Generated manifest validates against contract schema."""
    # test/ -> bennu_mission/ -> src/ -> ros2_ws/ -> drone/ -> repo
    repo_root = Path(__file__).resolve().parents[5]
    schema_path = repo_root / "contract" / "v1" / "manifest.schema.json"
    assert schema_path.exists(), f"Schema not found at {schema_path}"

    gen = ManifestGenerator(
        drone_id="bennu-001",
        hardware_manifest={
            "flight_controller": "Pixhawk6C",
            "px4_version": "1.16.1",
            "gps_model": "F9P",
            "sensors": ["rgb:IMX477"],
        },
        mission_id="2026-03-15-test-001",
    )

    images = [_make_image(i, ts=f"2026-03-15T10:3{i}:00Z") for i in range(1, 4)]
    manifest = gen.generate_manifest(
        images=images,
        sensor_config="mapping",
        checksums_digest="abc123",
        signature="base64sig",
    )

    import jsonschema

    schema = json.loads(schema_path.read_text())
    jsonschema.validate(manifest, schema)

    assert manifest["contract_version"] == "v1"
    assert manifest["mission_id"] == "2026-03-15-test-001"
    assert manifest["drone_id"] == "bennu-001"
    assert manifest["capture"]["image_count"] == 3
    assert "survey" not in manifest


def test_generate_images_csv():
    """CSV has correct header (18 cols) and row count."""
    gen = ManifestGenerator(
        drone_id="bennu-001",
        hardware_manifest={},
        mission_id="test",
    )
    images = [_make_image(1), _make_image(2)]
    csv_str = gen.generate_images_csv(images)

    reader = csv.DictReader(io.StringIO(csv_str))
    rows = list(reader)
    assert len(rows) == 2
    assert len(reader.fieldnames) == 18

    from bennu_camera.geotag import IMAGE_METADATA_COLUMNS

    assert tuple(reader.fieldnames) == IMAGE_METADATA_COLUMNS


def test_quality_summary_counts():
    """3 images (1 pass, 2 fail) -> correct counts and failure reasons."""
    gen = ManifestGenerator(
        drone_id="bennu-001",
        hardware_manifest={},
        mission_id="test",
    )
    images = [
        _make_image(1, score=0.9, flags="ok"),
        _make_image(2, score=0.3, flags="blur"),
        _make_image(3, score=0.2, flags="blur,underexposed"),
    ]
    manifest = gen.generate_manifest(
        images=images, sensor_config="mapping", checksums_digest="x", signature="y"
    )
    qs = manifest["quality_summary"]
    assert qs["images_total"] == 3
    assert qs["images_passed"] == 1
    assert qs["images_failed"] == 2
    assert qs["failure_reasons"]["blur"] == 2
    assert qs["failure_reasons"]["underexposed"] == 1


def test_empty_images_raises():
    """generate_manifest rejects empty image list."""
    gen = ManifestGenerator(
        drone_id="bennu-001",
        hardware_manifest={},
        mission_id="test",
    )
    with pytest.raises(ValueError, match="empty image list"):
        gen.generate_manifest(images=[], sensor_config="mapping")


def test_empty_images_csv_raises():
    """generate_images_csv rejects empty image list."""
    gen = ManifestGenerator(
        drone_id="bennu-001",
        hardware_manifest={},
        mission_id="test",
    )
    with pytest.raises(ValueError, match="empty image list"):
        gen.generate_images_csv(images=[])


def test_empty_drone_id_rejected():
    with pytest.raises(ValueError, match="drone_id"):
        ManifestGenerator(drone_id="", hardware_manifest={}, mission_id="test")


def test_empty_mission_id_rejected():
    with pytest.raises(ValueError, match="mission_id"):
        ManifestGenerator(drone_id="bennu-001", hardware_manifest={}, mission_id="")
