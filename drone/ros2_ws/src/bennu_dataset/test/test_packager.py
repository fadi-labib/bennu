"""Tests for bundle packager."""
import hashlib
import json
from pathlib import Path

import pytest

from bennu_dataset.packager import BundlePackager


def _create_test_image(path: Path) -> None:
    """Create a minimal test JPEG (just bytes, not a real image)."""
    path.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 100)


def test_package_creates_bundle_structure(tmp_path):
    output_dir = tmp_path / "output"
    packager = BundlePackager(output_dir)

    # Create fake image files
    img_dir = tmp_path / "src_images"
    img_dir.mkdir()
    img1 = img_dir / "0001_rgb.jpg"
    img2 = img_dir / "0002_rgb.jpg"
    _create_test_image(img1)
    _create_test_image(img2)

    manifest = {"contract_version": "v1", "mission_id": "test-001"}
    images_csv = "sequence,filename\n1,0001_rgb.jpg\n2,0002_rgb.jpg\n"
    quality_report = {"images_total": 2, "images_passed": 2}

    bundle = packager.package(
        mission_id="test-001",
        manifest=manifest,
        images_csv=images_csv,
        image_files=[img1, img2],
        quality_report=quality_report,
    )

    assert (bundle / "contract_version").read_text().strip() == "v1"
    assert (bundle / "manifest.json").exists()
    assert (bundle / "images" / "0001_rgb.jpg").exists()
    assert (bundle / "images" / "0002_rgb.jpg").exists()
    assert (bundle / "metadata" / "images.csv").exists()
    assert (bundle / "telemetry").is_dir()
    assert (bundle / "quality" / "report.json").exists()
    assert (bundle / "checksums.sha256").exists()

    report = json.loads((bundle / "quality" / "report.json").read_text())
    assert report["images_total"] == 2


def test_checksums_are_valid(tmp_path):
    output_dir = tmp_path / "output"
    packager = BundlePackager(output_dir)

    img_dir = tmp_path / "src_images"
    img_dir.mkdir()
    img1 = img_dir / "0001_rgb.jpg"
    _create_test_image(img1)

    bundle = packager.package(
        mission_id="test-002",
        manifest={"contract_version": "v1"},
        images_csv="sequence,filename\n1,0001_rgb.jpg\n",
        image_files=[img1],
    )

    checksums_text = (bundle / "checksums.sha256").read_text()
    for line in checksums_text.strip().split("\n"):
        if not line:
            continue
        expected_hash, rel_path = line.split("  ", 1)
        file_path = bundle / rel_path
        actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        assert actual_hash == expected_hash, f"Checksum mismatch for {rel_path}"


def test_quality_report_none_writes_sentinel(tmp_path):
    """When quality_report is None, report.json has status='not_available'."""
    output_dir = tmp_path / "output"
    packager = BundlePackager(output_dir)
    img_dir = tmp_path / "src_images"
    img_dir.mkdir()
    img1 = img_dir / "0001_rgb.jpg"
    _create_test_image(img1)

    bundle = packager.package(
        mission_id="test-sentinel",
        manifest={"contract_version": "v1"},
        images_csv="sequence,filename\n1,0001_rgb.jpg\n",
        image_files=[img1],
        quality_report=None,
    )

    report = json.loads((bundle / "quality" / "report.json").read_text())
    assert report == {"status": "not_available"}


def test_flight_log_copied(tmp_path):
    """Flight log is copied to telemetry/flight.ulg."""
    output_dir = tmp_path / "output"
    packager = BundlePackager(output_dir)
    img_dir = tmp_path / "src_images"
    img_dir.mkdir()
    img1 = img_dir / "0001_rgb.jpg"
    _create_test_image(img1)

    log_file = tmp_path / "test.ulg"
    log_file.write_bytes(b"ULog\x00" + b"\x00" * 50)

    bundle = packager.package(
        mission_id="test-log",
        manifest={"contract_version": "v1"},
        images_csv="sequence,filename\n1,0001_rgb.jpg\n",
        image_files=[img1],
        flight_log=log_file,
    )

    assert (bundle / "telemetry" / "flight.ulg").exists()
    assert (bundle / "telemetry" / "flight.ulg").read_bytes() == log_file.read_bytes()


def test_missing_flight_log_raises(tmp_path):
    """Specifying a nonexistent flight log raises FileNotFoundError."""
    packager = BundlePackager(tmp_path / "output")
    with pytest.raises(FileNotFoundError, match="Flight log not found"):
        packager.package(
            mission_id="test-missing",
            manifest={},
            images_csv="",
            image_files=[],
            flight_log=tmp_path / "nonexistent.ulg",
        )


def test_unsafe_mission_id_rejected(tmp_path):
    """Mission IDs with path traversal characters are rejected."""
    packager = BundlePackager(tmp_path / "output")
    with pytest.raises(ValueError, match="Unsafe mission_id"):
        packager.package(
            mission_id="../escape",
            manifest={},
            images_csv="",
            image_files=[],
        )


def test_duplicate_image_filenames_rejected(tmp_path):
    """Two images with the same filename are rejected."""
    output_dir = tmp_path / "output"
    packager = BundlePackager(output_dir)
    img_dir = tmp_path / "src_images"
    img_dir.mkdir()
    img1 = img_dir / "0001_rgb.jpg"
    _create_test_image(img1)

    # Create another dir with same filename
    img_dir2 = tmp_path / "other"
    img_dir2.mkdir()
    img2 = img_dir2 / "0001_rgb.jpg"
    _create_test_image(img2)

    with pytest.raises(ValueError, match="Duplicate image filename"):
        packager.package(
            mission_id="test-dupe",
            manifest={"contract_version": "v1"},
            images_csv="",
            image_files=[img1, img2],
        )


def test_cleanup_on_failure(tmp_path):
    """Partial bundle is cleaned up if packaging fails."""
    output_dir = tmp_path / "output"
    packager = BundlePackager(output_dir)
    img_dir = tmp_path / "src_images"
    img_dir.mkdir()
    img1 = img_dir / "0001_rgb.jpg"
    _create_test_image(img1)

    # Duplicate filenames will cause failure mid-packaging
    img_dir2 = tmp_path / "other"
    img_dir2.mkdir()
    img2 = img_dir2 / "0001_rgb.jpg"
    _create_test_image(img2)

    with pytest.raises(ValueError):
        packager.package(
            mission_id="test-cleanup",
            manifest={"contract_version": "v1"},
            images_csv="",
            image_files=[img1, img2],
        )

    # Bundle directory should be cleaned up
    assert not (output_dir / "test-cleanup").exists()
