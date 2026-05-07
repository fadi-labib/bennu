"""End-to-end bundle generation test.

Exercises the full pipeline:
1. Create DroneIdentity
2. Generate fake images + score them with ImageQualityScorer
3. Create ImageMetadata for each (18 columns)
4. Generate manifest.json + images.csv via ManifestGenerator
5. Sign manifest with ManifestSigner
6. Package everything with BundlePackager
7. Validate: schema, signature, checksums, file counts
"""

import hashlib
import json
from pathlib import Path

import numpy as np

from bennu_camera.geotag import ImageMetadata, compute_gsd
from bennu_camera.quality import ImageQualityScorer
from bennu_core.drone_identity import DroneIdentity
from bennu_dataset.packager import BundlePackager
from bennu_dataset.signer import ManifestSigner
from bennu_mission.mission_manifest import ManifestGenerator

REPO_ROOT = Path(__file__).resolve().parents[2]


def _create_test_image(path: Path, sharp: bool = True) -> np.ndarray:
    """Create a test image and save it as JPEG-like bytes.

    Returns the image array for quality scoring.
    A non-sharp image is dark+uniform: triggers both blur and underexposed
    flags, giving a score well below the 0.5 quality threshold.
    """
    if sharp:
        img = np.random.randint(50, 200, (480, 640, 3), dtype=np.uint8)
    else:
        img = np.full((480, 640, 3), 5, dtype=np.uint8)
    # Write raw bytes as a fake image file
    path.write_bytes(b"\xff\xd8\xff\xe0" + img.tobytes()[:1000])
    return img


def test_full_bundle_pipeline(tmp_path):
    """Full pipeline: identity -> capture -> score -> manifest -> package -> sign -> validate."""

    # 1. Create DroneIdentity
    identity = DroneIdentity(
        drone_id="bennu-001",
        flight_controller="Pixhawk6C",
        px4_version="1.16.1",
        gps_model="F9P",
        sensors=("rgb:IMX477",),
    )

    # 2. Generate fake images + score them
    scorer = ImageQualityScorer(blur_threshold=100.0)
    img_dir = tmp_path / "raw_images"
    img_dir.mkdir()

    image_files = []
    metadata_list = []

    for i in range(1, 4):
        filename = f"{i:04d}_rgb.jpg"
        img_path = img_dir / filename
        sharp = i != 2  # Image 2 is blurry
        img_array = _create_test_image(img_path, sharp=sharp)
        image_files.append(img_path)

        # Score
        result = scorer.score(img_array)

        # 3. Create ImageMetadata (18 columns)
        gsd = compute_gsd(80.0, 6.0, 4.712, 3040)
        meta = ImageMetadata(
            sequence=i,
            filename=filename,
            sensor="rgb",
            timestamp_utc=f"2026-03-15T10:3{i}:00Z",
            lat=55.6761 + i * 0.0001,
            lon=12.5683 + i * 0.0001,
            alt_msl=80.0,
            alt_agl=75.0,
            heading_deg=90.0,
            pitch_deg=-90.0,
            roll_deg=0.0,
            rtk_fix_type="RTK_FIXED",
            position_accuracy_m=0.05,
            gsd_cm=gsd,
            quality_score=result.score,
            quality_flags=",".join(result.flags),
        )
        metadata_list.append(meta)

    # 4. Generate manifest + images.csv
    gen = ManifestGenerator(
        drone_id=identity.drone_id,
        hardware_manifest=identity.hardware_manifest(),
        mission_id="2026-03-15-e2e-test",
    )
    manifest = gen.generate_manifest(
        images=metadata_list,
        sensor_config="mapping",
    )
    images_csv = gen.generate_images_csv(metadata_list)

    # 5. Package everything
    output_dir = tmp_path / "bundles"
    packager = BundlePackager(output_dir)

    quality_report = {
        "images_total": len(metadata_list),
        "images_passed": sum(1 for m in metadata_list if m.quality_score >= 0.5),
        "images_failed": sum(1 for m in metadata_list if m.quality_score < 0.5),
    }

    bundle = packager.package(
        mission_id="2026-03-15-e2e-test",
        manifest=manifest,
        images_csv=images_csv,
        image_files=image_files,
        quality_report=quality_report,
    )

    # Update checksums_digest in manifest
    checksums_digest = BundlePackager.compute_checksums_digest(bundle)
    manifest["checksums_digest"] = checksums_digest

    # 6. Sign manifest
    signer = ManifestSigner.generate()
    manifest_without_sig = {k: v for k, v in manifest.items() if k != "signature"}
    canonical = signer.canonicalize(manifest_without_sig)
    signature = signer.sign(canonical)
    manifest["signature"] = signature

    # Re-write manifest with checksums_digest and signature
    (bundle / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    # 7. Validate everything

    # 7a. Bundle structure
    assert (bundle / "contract_version").exists()
    assert (bundle / "manifest.json").exists()
    assert (bundle / "images").is_dir()
    assert (bundle / "metadata" / "images.csv").exists()
    assert (bundle / "quality" / "report.json").exists()
    assert (bundle / "checksums.sha256").exists()

    # 7b. Image count
    image_count = len(list((bundle / "images").glob("*.jpg")))
    assert image_count == 3

    # 7c. Schema validation (mandatory)
    schema_path = REPO_ROOT / "contract" / "v1" / "manifest.schema.json"
    assert schema_path.exists(), f"Schema not found at {schema_path}"
    import jsonschema

    schema = json.loads(schema_path.read_text())
    jsonschema.validate(manifest, schema)

    # 7d. Signature verification
    manifest_for_verify = {k: v for k, v in manifest.items() if k != "signature"}
    canonical_verify = signer.canonicalize(manifest_for_verify)
    assert signer.verify(canonical_verify, manifest["signature"])

    # 7e. Checksums validation
    checksums_text = (bundle / "checksums.sha256").read_text()
    for line in checksums_text.strip().split("\n"):
        if not line:
            continue
        expected_hash, rel_path = line.split("  ", 1)
        file_path = bundle / rel_path
        actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        assert actual_hash == expected_hash, f"Checksum mismatch: {rel_path}"

    # 7f. CSV has 18 columns
    import csv
    import io

    csv_content = (bundle / "metadata" / "images.csv").read_text()
    reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(reader)
    assert len(reader.fieldnames) == 18
    assert len(rows) == 3

    # 7g. Manifest fields
    assert manifest["contract_version"] == "v1"
    assert manifest["mission_id"] == "2026-03-15-e2e-test"
    assert manifest["drone_id"] == "bennu-001"
    assert manifest["capture"]["image_count"] == 3
    assert manifest["quality_summary"]["images_total"] == 3
    assert manifest["quality_summary"]["images_passed"] == 2
    assert manifest["quality_summary"]["images_failed"] == 1
    assert "blur" in manifest["quality_summary"]["failure_reasons"]

    # 7h. CSV column order matches contract schema
    from bennu_camera.geotag import IMAGE_METADATA_COLUMNS

    assert tuple(reader.fieldnames) == IMAGE_METADATA_COLUMNS
