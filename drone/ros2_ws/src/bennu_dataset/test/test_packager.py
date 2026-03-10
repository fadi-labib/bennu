"""Tests for bundle packager."""
import hashlib
import json
from pathlib import Path

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
