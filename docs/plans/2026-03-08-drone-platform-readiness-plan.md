# Drone Platform-Readiness Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Evolve Bennu from a photogrammetry prototype into a production-grade data acquisition system that produces versioned, signed mission bundles consumable by an independent geospatial analysis platform.

**Architecture:** Contract-first development. Define the mission bundle schema, then build the drone-side pipeline that produces conformant bundles. Each phase adds capabilities (quality gates, sensor configuration, survey intelligence) while maintaining schema conformance. All new code lives in ROS2 Python packages under `drone/ros2_ws/src/`. Tests use `colcon test` for package-level tests and `pip install -e` for cross-package integration tests — never raw PYTHONPATH hacks.

**Tech Stack:** Python 3.12, ROS2 Jazzy, PX4 v1.16+, uXRCE-DDS, pytest, jsonschema, Ed25519 (PyNaCl), Gazebo Harmonic (SITL)

**Design Doc:** `docs/plans/2026-03-08-drone-platform-readiness-design.md`

---

## Phase 0: Foundation & Governance

### Task 1: Mission Bundle JSON Schema

**Files:**
- Create: `contract/v1/manifest.schema.json`
- Create: `contract/v1/images.schema.json` (CSV column definitions as JSON Schema)
- Create: `contract/v1/README.md`
- Create: `contract/v1/example/manifest.json`
- Create: `contract/v1/example/images.csv`
- Test: `tests/contract/test_schema_validation.py`

**Context:** The mission bundle contract is the ONLY coupling point between the drone and the platform. This schema defines what the drone must produce. Schema authority will eventually live in the platform repo; for now we bootstrap it here.

**Important schema decisions:**
- `survey` object is **optional** (omitted for manual flights, test flights, non-grid missions)
- `quality_summary.coverage_pct` is **nullable** (null when no survey grid defined)
- `checksums_digest` is **required** (SHA-256 of checksums.sha256 file — integrity chain)
- `images.schema.json` defines CSV column names, types, and constraints for machine validation

**Step 1: Write the failing test**

```python
# tests/contract/test_schema_validation.py
import json
import jsonschema
import pytest
from pathlib import Path

CONTRACT_DIR = Path(__file__).parent.parent.parent / "contract" / "v1"

def test_example_manifest_validates():
    schema = json.loads((CONTRACT_DIR / "manifest.schema.json").read_text())
    example = json.loads((CONTRACT_DIR / "example" / "manifest.json").read_text())
    jsonschema.validate(example, schema)

def test_manifest_rejects_missing_required_fields():
    schema = json.loads((CONTRACT_DIR / "manifest.schema.json").read_text())
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"contract_version": "v1"}, schema)

def test_contract_version_is_v1():
    schema = json.loads((CONTRACT_DIR / "manifest.schema.json").read_text())
    example = json.loads((CONTRACT_DIR / "example" / "manifest.json").read_text())
    assert example["contract_version"] == "v1"
    assert schema["properties"]["contract_version"]["const"] == "v1"

def test_manifest_without_survey_validates():
    """survey is optional — manual/test flights omit it."""
    schema = json.loads((CONTRACT_DIR / "manifest.schema.json").read_text())
    example = json.loads((CONTRACT_DIR / "example" / "manifest.json").read_text())
    example.pop("survey", None)
    example["quality_summary"]["coverage_pct"] = None
    jsonschema.validate(example, schema)

def test_checksums_digest_required():
    schema = json.loads((CONTRACT_DIR / "manifest.schema.json").read_text())
    example = json.loads((CONTRACT_DIR / "example" / "manifest.json").read_text())
    del example["checksums_digest"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(example, schema)

def test_images_csv_columns_match_schema():
    """Validate images.csv column names against images.schema.json."""
    csv_schema = json.loads((CONTRACT_DIR / "images.schema.json").read_text())
    example_csv = (CONTRACT_DIR / "example" / "images.csv").read_text()
    header = example_csv.strip().split("\n")[0].split(",")
    expected_columns = csv_schema["columns"]
    assert header == [col["name"] for col in expected_columns]
```

**Step 2: Run test to verify it fails**

Run: `cd /home/fadi/projects/bennu && python -m pytest tests/contract/test_schema_validation.py -v`
Expected: FAIL (files do not exist yet)

**Step 3: Create the JSON schema**

Create `contract/v1/manifest.schema.json` implementing the manifest.json structure from the design doc. The schema must include:
- `contract_version` (const "v1") — required
- `mission_id`, `drone_id` (required strings)
- `drone_hardware` object (flight_controller, px4_version, gps_model, sensors array) — required
- `capture` object (start_time, end_time, image_count, sensor_config, trigger_mode, trigger_distance_m) — required
- `survey` object (site_id, aoi_geojson, planned_altitude_m, planned_overlap_front, planned_overlap_side, planned_gsd_cm) — **optional** (omitted for manual/test flights)
- `quality_summary` object (images_total, images_passed, images_failed, failure_reasons, rtk_fixed_pct, coverage_pct) — required, but `coverage_pct` is **nullable**
- `checksums_digest` (required string) — SHA-256 of the checksums.sha256 file
- `signature` (required string)

Create `contract/v1/example/manifest.json` with a valid example matching the design doc (include `checksums_digest` field).

Create `contract/v1/images.schema.json` — a JSON Schema defining the CSV columns as a machine-validatable schema. Each column entry has `name`, `type` (string/int/float/ISO8601), and `nullable` (boolean). Columns: sequence, filename, sensor, timestamp_utc, lat, lon, alt_msl, alt_agl, heading_deg, pitch_deg, roll_deg, rtk_fix_type, position_accuracy_m, gsd_cm, quality_score, quality_flags, ambient_light_lux, capture_offset_ms.

Create `contract/v1/example/images.csv` with 3 example rows matching the schema.

Create `contract/v1/README.md` with contract rules (semver, backward compat, migration policy, canonical JSON serialization for signing).

**Step 4: Run tests to verify they pass**

Run: `cd /home/fadi/projects/bennu && python -m pytest tests/contract/test_schema_validation.py -v`
Expected: 3 PASS

**Step 5: Commit**

```bash
git add contract/ tests/contract/
git commit -m "feat: add mission bundle contract v1 schema and examples"
```

---

### Task 2: Compatibility Matrix

**Files:**
- Create: `docs/reference/compatibility-matrix.md`

**Context:** Pin the exact versions of PX4, ROS2, px4_msgs, and XRCE-DDS agent that are tested together. This prevents version drift from silently breaking the build.

**Step 1: Create the compatibility matrix**

```markdown
# Compatibility Matrix

| Component | Version | Notes |
|---|---|---|
| PX4 Autopilot | v1.16.1 | Pinned tag |
| ROS2 | Jazzy Jalisco | Ubuntu 24.04 |
| px4_msgs | Match PX4 v1.16.1 tag | Must match PX4 version exactly |
| Micro-XRCE-DDS Agent | v2.4.x | From ROS2 Jazzy repos |
| Gazebo | Harmonic | SITL only |
| Python | 3.12 | Ubuntu 24.04 default |
| Ubuntu (Pi 5) | 24.04 LTS | Companion computer |
| Ubuntu (Sim) | 24.04 LTS | Docker base image |
```

**Step 2: Commit**

```bash
git add docs/reference/compatibility-matrix.md
git commit -m "docs: add compatibility matrix for pinned dependency versions"
```

---

### Task 3: CI Pipeline Baseline

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `requirements-dev.txt`

**Context:** CI must run lint + tests on every PR. Contract schema validation runs as part of the test suite.

**Step 1: Create dev requirements**

```
# requirements-dev.txt
pytest>=8.0
jsonschema>=4.20
ruff>=0.4
```

**Step 2: Create GitHub Actions CI workflow**

```yaml
# .github/workflows/ci.yml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint-and-test:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements-dev.txt
      - run: |
          for pkg in drone/ros2_ws/src/bennu_*/; do
            pip install -e "$pkg"
          done
      - run: ruff check .
      - run: python -m pytest drone/ros2_ws/src/*/test/ tests/ -v
```

**Step 3: Verify locally**

Run: `pip install -r requirements-dev.txt && for pkg in drone/ros2_ws/src/bennu_*/; do pip install -e "$pkg"; done && ruff check . && python -m pytest drone/ros2_ws/src/*/test/ tests/ -v`
Expected: lint passes, tests pass

**Step 4: Commit**

```bash
git add .github/workflows/ci.yml requirements-dev.txt
git commit -m "ci: add lint and test pipeline with ruff and pytest"
```

---

### Task 4: Project Governance Files

**Files:**
- Create: `LICENSE`
- Create: `CONTRIBUTING.md`
- Create: `SECURITY.md`

**Context:** Required for any OSS project. Apache-2.0 license per the proposal.

**Step 1: Create governance files**

- `LICENSE`: Apache License 2.0 (full text)
- `CONTRIBUTING.md`: Brief contributor guide (fork, branch, PR, tests must pass, code review required)
- `SECURITY.md`: Responsible disclosure policy (email, response time commitment)

**Step 2: Update existing package.xml license fields**

Existing ROS2 packages declare `MIT` in their `package.xml` and `setup.py`. Update all
to `Apache-2.0` for consistency with the repo-level LICENSE:
- `drone/ros2_ws/src/bennu_camera/package.xml` — change `<license>MIT</license>` to `<license>Apache-2.0</license>`
- `drone/ros2_ws/src/bennu_camera/setup.py` — change `license='MIT'` to `license='Apache-2.0'`
- `drone/ros2_ws/src/bennu_bringup/package.xml` — same change

**Step 3: Commit**

```bash
git add LICENSE CONTRIBUTING.md SECURITY.md
git commit -m "docs: add project governance files (LICENSE, CONTRIBUTING, SECURITY)"
```

---

### Task 5: bennu_core Package — Drone Identity

**Files:**
- Create: `drone/ros2_ws/src/bennu_core/package.xml`
- Create: `drone/ros2_ws/src/bennu_core/setup.py`
- Create: `drone/ros2_ws/src/bennu_core/setup.cfg`
- Create: `drone/ros2_ws/src/bennu_core/resource/bennu_core`
- Create: `drone/ros2_ws/src/bennu_core/bennu_core/__init__.py`
- Create: `drone/ros2_ws/src/bennu_core/bennu_core/drone_identity.py`
- Test: `drone/ros2_ws/src/bennu_core/test/test_drone_identity.py`

**Context:** Every mission bundle needs drone_id and hardware manifest. This module manages the drone's identity (ID, hardware config, Ed25519 keypair). It does NOT depend on ROS2 at runtime for the identity/signing logic — pure Python with optional ROS2 node wrapper.

**Step 1: Write the failing test**

```python
# drone/ros2_ws/src/bennu_core/test/test_drone_identity.py
import pytest
from bennu_core.drone_identity import DroneIdentity

def test_drone_identity_loads_config():
    identity = DroneIdentity(
        drone_id="bennu-001",
        flight_controller="Pixhawk6C",
        px4_version="1.16.1",
        gps_model="F9P",
        sensors=["rgb:IMX477"],
    )
    assert identity.drone_id == "bennu-001"
    assert identity.hardware_manifest()["flight_controller"] == "Pixhawk6C"

def test_hardware_manifest_structure():
    identity = DroneIdentity(
        drone_id="bennu-001",
        flight_controller="Pixhawk6C",
        px4_version="1.16.1",
        gps_model="M9N",
        sensors=["rgb:IMX477"],
    )
    manifest = identity.hardware_manifest()
    assert "flight_controller" in manifest
    assert "px4_version" in manifest
    assert "gps_model" in manifest
    assert "sensors" in manifest
    assert isinstance(manifest["sensors"], list)
```

**Step 2: Run test to verify it fails**

Run: `cd /home/fadi/projects/bennu && python -m pytest drone/ros2_ws/src/bennu_core/test/test_drone_identity.py -v`
Expected: FAIL (module does not exist)

**Step 3: Implement DroneIdentity**

```python
# drone/ros2_ws/src/bennu_core/bennu_core/drone_identity.py
from dataclasses import dataclass, field

@dataclass
class DroneIdentity:
    drone_id: str
    flight_controller: str
    px4_version: str
    gps_model: str
    sensors: list[str] = field(default_factory=list)

    def hardware_manifest(self) -> dict:
        return {
            "flight_controller": self.flight_controller,
            "px4_version": self.px4_version,
            "gps_model": self.gps_model,
            "sensors": self.sensors,
        }
```

Create standard ROS2 Python package boilerplate (package.xml, setup.py, setup.cfg, resource marker, `__init__.py`).

**Step 4: Run tests to verify they pass**

Run: `cd /home/fadi/projects/bennu && pip install -e drone/ros2_ws/src/bennu_core && python -m pytest drone/ros2_ws/src/bennu_core/test/test_drone_identity.py -v`
Expected: 2 PASS

**Step 5: Commit**

```bash
git add drone/ros2_ws/src/bennu_core/ drone/ros2_ws/src/bennu_core/test/test_drone_identity.py
git commit -m "feat: add bennu_core package with drone identity module"
```

---

### Task 6: Ed25519 Manifest Signing

**Files:**
- Create: `drone/ros2_ws/src/bennu_dataset/package.xml`
- Create: `drone/ros2_ws/src/bennu_dataset/setup.py`
- Create: `drone/ros2_ws/src/bennu_dataset/setup.cfg`
- Create: `drone/ros2_ws/src/bennu_dataset/resource/bennu_dataset`
- Create: `drone/ros2_ws/src/bennu_dataset/bennu_dataset/__init__.py`
- Create: `drone/ros2_ws/src/bennu_dataset/bennu_dataset/signer.py`
- Test: `drone/ros2_ws/src/bennu_dataset/test/test_signer.py`

**Context:** The drone signs manifest.json with Ed25519. The platform verifies on ingest. This module generates keypairs, signs JSON content, and verifies signatures. Uses PyNaCl.

**Step 1: Add PyNaCl to requirements**

Add `pynacl>=1.5` to `requirements-dev.txt`.

**Step 2: Write the failing test**

```python
# drone/ros2_ws/src/bennu_dataset/test/test_signer.py
import json
import pytest
from bennu_dataset.signer import ManifestSigner

def test_sign_and_verify():
    signer = ManifestSigner.generate()
    manifest = {"contract_version": "v1", "mission_id": "test-001"}
    canonical = signer.canonicalize(manifest)
    signature = signer.sign(canonical)
    assert signer.verify(canonical, signature)

def test_canonicalize_is_deterministic():
    signer = ManifestSigner.generate()
    m1 = {"b": 2, "a": 1}
    m2 = {"a": 1, "b": 2}
    assert signer.canonicalize(m1) == signer.canonicalize(m2)
    assert signer.canonicalize(m1) == '{"a":1,"b":2}'

def test_verify_rejects_tampered():
    signer = ManifestSigner.generate()
    manifest = {"contract_version": "v1", "mission_id": "test-001"}
    canonical = signer.canonicalize(manifest)
    signature = signer.sign(canonical)
    tampered = signer.canonicalize({"contract_version": "v1", "mission_id": "TAMPERED"})
    assert not signer.verify(tampered, signature)

def test_export_and_import_keys(tmp_path):
    signer = ManifestSigner.generate()
    key_file = tmp_path / "drone.key"
    pub_file = tmp_path / "drone.pub"
    signer.save_keys(key_file, pub_file)
    loaded = ManifestSigner.from_files(key_file, pub_file)
    manifest = json.dumps({"test": True})
    sig = signer.sign(manifest)
    assert loaded.verify(manifest, sig)
```

**Step 3: Run test to verify it fails**

Run: `cd /home/fadi/projects/bennu && python -m pytest drone/ros2_ws/src/bennu_dataset/test/test_signer.py -v`
Expected: FAIL (module does not exist)

**Step 4: Implement ManifestSigner**

```python
# drone/ros2_ws/src/bennu_dataset/bennu_dataset/signer.py
import base64
from pathlib import Path
from nacl.signing import SigningKey, VerifyKey
from nacl.exceptions import BadSignatureError

class ManifestSigner:
    def __init__(self, signing_key: SigningKey, verify_key: VerifyKey):
        self._signing_key = signing_key
        self._verify_key = verify_key

    @classmethod
    def generate(cls) -> "ManifestSigner":
        sk = SigningKey.generate()
        return cls(sk, sk.verify_key)

    @classmethod
    def from_files(cls, key_path: Path, pub_path: Path) -> "ManifestSigner":
        sk = SigningKey(Path(key_path).read_bytes())
        vk = VerifyKey(Path(pub_path).read_bytes())
        return cls(sk, vk)

    def save_keys(self, key_path: Path, pub_path: Path) -> None:
        Path(key_path).write_bytes(bytes(self._signing_key))
        Path(pub_path).write_bytes(bytes(self._verify_key))

    @staticmethod
    def canonicalize(manifest: dict) -> str:
        """Canonical JSON: sorted keys, compact separators. Deterministic across implementations."""
        import json
        return json.dumps(manifest, sort_keys=True, separators=(",", ":"))

    def sign(self, data: str) -> str:
        signed = self._signing_key.sign(data.encode())
        return base64.b64encode(signed.signature).decode()

    def verify(self, data: str, signature_b64: str) -> bool:
        try:
            sig = base64.b64decode(signature_b64)
            self._verify_key.verify(data.encode(), sig)
            return True
        except (BadSignatureError, Exception):
            return False
```

Create standard ROS2 Python package boilerplate for bennu_dataset.

**Step 5: Run tests to verify they pass**

Run: `cd /home/fadi/projects/bennu && pip install pynacl && pip install -e drone/ros2_ws/src/bennu_dataset && python -m pytest drone/ros2_ws/src/bennu_dataset/test/test_signer.py -v`
Expected: 3 PASS

**Step 6: Commit**

```bash
git add drone/ros2_ws/src/bennu_dataset/ drone/ros2_ws/src/bennu_dataset/test/test_signer.py requirements-dev.txt
git commit -m "feat: add Ed25519 manifest signing (bennu_dataset.signer)"
```

---

**Phase 0 Exit Gate:**
- CI runs lint + tests on every PR
- Contract v1 schema validates example manifest
- DroneIdentity produces hardware manifest dict
- ManifestSigner signs and verifies JSON payloads
- Governance files committed (LICENSE, CONTRIBUTING, SECURITY)
- Compatibility matrix documented

---

## Phase 1: Data Quality Baseline

### Task 7: Image Quality Scoring

**Files:**
- Create: `drone/ros2_ws/src/bennu_camera/bennu_camera/quality.py`
- Test: `drone/ros2_ws/src/bennu_camera/test/test_quality.py`

**Context:** Every captured image gets a 0.0-1.0 quality score based on blur detection (Laplacian variance) and exposure analysis (histogram). Quality flags (ok, blur, overexposed, underexposed) are recorded in images.csv.

**Step 1: Write the failing test**

```python
# drone/ros2_ws/src/bennu_camera/test/test_quality.py
import numpy as np
import pytest
from bennu_camera.quality import ImageQualityScorer

def test_sharp_image_scores_high():
    scorer = ImageQualityScorer(blur_threshold=100.0)
    # Create a sharp image (high frequency content)
    img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    result = scorer.score(img)
    assert result.score > 0.5
    assert "blur" not in result.flags

def test_blurry_image_flagged():
    scorer = ImageQualityScorer(blur_threshold=100.0)
    # Create a uniform (blurry) image
    img = np.ones((480, 640, 3), dtype=np.uint8) * 128
    result = scorer.score(img)
    assert "blur" in result.flags

def test_overexposed_image_flagged():
    scorer = ImageQualityScorer(blur_threshold=100.0)
    img = np.ones((480, 640, 3), dtype=np.uint8) * 250
    result = scorer.score(img)
    assert "overexposed" in result.flags

def test_underexposed_image_flagged():
    scorer = ImageQualityScorer(blur_threshold=100.0)
    img = np.ones((480, 640, 3), dtype=np.uint8) * 5
    result = scorer.score(img)
    assert "underexposed" in result.flags

def test_score_result_structure():
    scorer = ImageQualityScorer()
    img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    result = scorer.score(img)
    assert 0.0 <= result.score <= 1.0
    assert isinstance(result.flags, list)
    assert isinstance(result.blur_variance, float)
```

**Step 2: Run test to verify it fails**

Run: `cd /home/fadi/projects/bennu && python -m pytest drone/ros2_ws/src/bennu_camera/test/test_quality.py -v`
Expected: FAIL

**Step 3: Implement ImageQualityScorer**

The scorer:
- Computes Laplacian variance for blur detection (cv2.Laplacian → variance)
- Analyzes histogram for exposure (mean brightness < 30 → underexposed, > 225 → overexposed)
- Combines scores into 0.0-1.0 composite
- Returns `QualityResult(score, flags, blur_variance)`

Add `opencv-python-headless>=4.8` and `numpy>=1.26` to `requirements-dev.txt`.

**Step 4: Run tests to verify they pass**

Run: `cd /home/fadi/projects/bennu && pip install -e drone/ros2_ws/src/bennu_camera && python -m pytest drone/ros2_ws/src/bennu_camera/test/test_quality.py -v`
Expected: 5 PASS

**Step 5: Commit**

```bash
git add drone/ros2_ws/src/bennu_camera/bennu_camera/quality.py drone/ros2_ws/src/bennu_camera/test/test_quality.py requirements-dev.txt
git commit -m "feat: add image quality scoring (blur + exposure detection)"
```

---

### Task 8: Enhanced Geotagging

**Files:**
- Modify: `drone/ros2_ws/src/bennu_camera/bennu_camera/geotag.py`
- Test: `drone/ros2_ws/src/bennu_camera/test/test_geotag.py`

**Context:** The existing geotag.py writes basic EXIF GPS data. Enhance it to produce the full images.csv row: attitude (heading, pitch, roll), RTK fix type, position accuracy, GSD calculation, quality score, quality flags. This data feeds directly into the mission bundle.

**Step 1: Write the failing test**

```python
# drone/ros2_ws/src/bennu_camera/test/test_geotag.py
import pytest
from bennu_camera.geotag import ImageMetadata, compute_gsd

def test_compute_gsd():
    # 12.3MP sensor (7.9mm height), 6mm lens, 80m altitude
    gsd = compute_gsd(altitude_m=80.0, focal_length_mm=6.0, sensor_height_mm=7.9, image_height_px=3040)
    assert 1.5 < gsd < 3.5  # ~2.1 cm/px expected

def test_image_metadata_to_csv_row():
    meta = ImageMetadata(
        sequence=1,
        filename="0001_rgb.jpg",
        sensor="rgb",
        timestamp_utc="2026-03-15T10:32:00Z",
        lat=35.6762,
        lon=139.6503,
        alt_msl=120.5,
        alt_agl=80.0,
        heading_deg=45.0,
        pitch_deg=-90.0,
        roll_deg=0.0,
        rtk_fix_type="RTK_FIXED",
        position_accuracy_m=0.08,
        gsd_cm=2.1,
        quality_score=0.95,
        quality_flags="ok",
        ambient_light_lux=45000.0,
        capture_offset_ms=None,
    )
    row = meta.to_csv_dict()
    assert row["sequence"] == 1
    assert row["rtk_fix_type"] == "RTK_FIXED"
    assert row["quality_score"] == 0.95
    assert len(row) == 18  # All columns present (including capture_offset_ms)

def test_gsd_scales_with_altitude():
    gsd_low = compute_gsd(40.0, 6.0, 7.9, 3040)
    gsd_high = compute_gsd(80.0, 6.0, 7.9, 3040)
    assert gsd_high > gsd_low
    assert abs(gsd_high / gsd_low - 2.0) < 0.01  # Linear relationship
```

**Step 2: Run test to verify it fails**

Run: `cd /home/fadi/projects/bennu && pip install -e drone/ros2_ws/src/bennu_camera && python -m pytest drone/ros2_ws/src/bennu_camera/test/test_geotag.py -v`
Expected: FAIL

**Step 3: Implement enhanced geotag module**

Add `ImageMetadata` dataclass with all 18 CSV columns (including `capture_offset_ms`) and `to_csv_dict()` method. Add `compute_gsd(altitude_m, focal_length_mm, sensor_height_mm, image_height_px)` function.

Keep existing EXIF writing functions. Add the new metadata structures alongside.

**Step 4: Run tests to verify they pass**

Run: `cd /home/fadi/projects/bennu && pip install -e drone/ros2_ws/src/bennu_camera && python -m pytest drone/ros2_ws/src/bennu_camera/test/test_geotag.py -v`
Expected: 3 PASS

**Step 5: Commit**

```bash
git add drone/ros2_ws/src/bennu_camera/bennu_camera/geotag.py drone/ros2_ws/src/bennu_camera/test/test_geotag.py
git commit -m "feat: add extended image metadata and GSD calculation"
```

---

### Task 9: Mission Manifest Generator

**Files:**
- Create: `drone/ros2_ws/src/bennu_mission/package.xml`
- Create: `drone/ros2_ws/src/bennu_mission/setup.py`
- Create: `drone/ros2_ws/src/bennu_mission/setup.cfg`
- Create: `drone/ros2_ws/src/bennu_mission/resource/bennu_mission`
- Create: `drone/ros2_ws/src/bennu_mission/bennu_mission/__init__.py`
- Create: `drone/ros2_ws/src/bennu_mission/bennu_mission/mission_manifest.py`
- Test: `drone/ros2_ws/src/bennu_mission/test/test_mission_manifest.py`

**Context:** Generates `manifest.json` and `images.csv` from a list of ImageMetadata records + DroneIdentity + mission parameters. Output must validate against the contract v1 schema.

**Step 1: Write the failing test**

```python
# drone/ros2_ws/src/bennu_mission/test/test_mission_manifest.py
import json
import jsonschema
import pytest
from pathlib import Path
from bennu_mission.mission_manifest import ManifestGenerator
from bennu_core.drone_identity import DroneIdentity
from bennu_camera.geotag import ImageMetadata

CONTRACT_SCHEMA = Path(__file__).parent.parent.parent / "contract" / "v1" / "manifest.schema.json"

def test_generate_manifest_validates_against_schema():
    identity = DroneIdentity(
        drone_id="bennu-001",
        flight_controller="Pixhawk6C",
        px4_version="1.16.1",
        gps_model="F9P",
        sensors=["rgb:IMX477"],
    )
    images = [
        ImageMetadata(
            sequence=i, filename=f"{i:04d}_rgb.jpg", sensor="rgb",
            timestamp_utc=f"2026-03-15T10:3{i}:00Z",
            lat=35.6762, lon=139.6503, alt_msl=120.5, alt_agl=80.0,
            heading_deg=45.0, pitch_deg=-90.0, roll_deg=0.0,
            rtk_fix_type="RTK_FIXED", position_accuracy_m=0.08,
            gsd_cm=2.1, quality_score=0.95, quality_flags="ok",
            ambient_light_lux=45000.0,
        )
        for i in range(1, 4)
    ]
    gen = ManifestGenerator(identity=identity, mission_id="test-mission-001")
    manifest = gen.generate_manifest(
        images=images,
        sensor_config="mapping",
        trigger_mode="distance",
        trigger_distance_m=5.0,
        site_id="site-alpha",
        planned_altitude_m=80,
        planned_overlap_front=0.75,
        planned_overlap_side=0.65,
        planned_gsd_cm=2.1,
    )
    schema = json.loads(CONTRACT_SCHEMA.read_text())
    # Remove signature field for validation (added by signer separately)
    manifest["signature"] = "placeholder"
    jsonschema.validate(manifest, schema)

def test_generate_images_csv():
    identity = DroneIdentity(
        drone_id="bennu-001",
        flight_controller="Pixhawk6C",
        px4_version="1.16.1",
        gps_model="M9N",
        sensors=["rgb:IMX477"],
    )
    images = [
        ImageMetadata(
            sequence=1, filename="0001_rgb.jpg", sensor="rgb",
            timestamp_utc="2026-03-15T10:32:00Z",
            lat=35.6762, lon=139.6503, alt_msl=120.5, alt_agl=80.0,
            heading_deg=45.0, pitch_deg=-90.0, roll_deg=0.0,
            rtk_fix_type="AUTONOMOUS", position_accuracy_m=2.5,
            gsd_cm=2.1, quality_score=0.90, quality_flags="ok",
            ambient_light_lux=None, capture_offset_ms=None,
        ),
    ]
    gen = ManifestGenerator(identity=identity, mission_id="test-002")
    csv_content = gen.generate_images_csv(images)
    lines = csv_content.strip().split("\n")
    assert len(lines) == 2  # header + 1 row
    header = lines[0].split(",")
    assert "sequence" in header
    assert "rtk_fix_type" in header
    assert len(header) == 18  # includes capture_offset_ms

def test_quality_summary_counts():
    identity = DroneIdentity("bennu-001", "Pixhawk6C", "1.16.1", "F9P", ["rgb:IMX477"])
    images = [
        ImageMetadata(1, "0001_rgb.jpg", "rgb", "2026-03-15T10:32:00Z",
                      35.0, 139.0, 120.0, 80.0, 0.0, -90.0, 0.0,
                      "RTK_FIXED", 0.08, 2.1, 0.95, "ok", 45000.0, None),
        ImageMetadata(2, "0002_rgb.jpg", "rgb", "2026-03-15T10:32:05Z",
                      35.0, 139.0, 120.0, 80.0, 0.0, -90.0, 0.0,
                      "RTK_FIXED", 0.08, 2.1, 0.3, "blur", 45000.0, None),
        ImageMetadata(3, "0003_rgb.jpg", "rgb", "2026-03-15T10:32:10Z",
                      35.0, 139.0, 120.0, 80.0, 0.0, -90.0, 0.0,
                      "RTK_FLOAT", 0.5, 2.1, 0.2, "blur,overexposed", 45000.0, None),
    ]
    gen = ManifestGenerator(identity=identity, mission_id="test-003")
    manifest = gen.generate_manifest(
        images=images, sensor_config="mapping", trigger_mode="distance",
        trigger_distance_m=5.0, site_id="test", planned_altitude_m=80,
        planned_overlap_front=0.75, planned_overlap_side=0.65, planned_gsd_cm=2.1,
    )
    qs = manifest["quality_summary"]
    assert qs["images_total"] == 3
    assert qs["images_passed"] == 1
    assert qs["images_failed"] == 2
    assert qs["failure_reasons"]["blur"] == 2
```

**Step 2: Run test to verify it fails**

Run: `cd /home/fadi/projects/bennu && python -m pytest drone/ros2_ws/src/bennu_mission/test/test_mission_manifest.py -v`
Expected: FAIL

**Step 3: Implement ManifestGenerator**

The generator:
- Takes DroneIdentity + mission parameters + list of ImageMetadata
- Produces manifest.json dict matching contract v1 schema
- Computes quality_summary from image quality scores (threshold: 0.5 for pass/fail)
- Generates images.csv string from ImageMetadata.to_csv_dict()

**Step 4: Run tests to verify they pass**

Run: `cd /home/fadi/projects/bennu && pip install -e drone/ros2_ws/src/bennu_core -e drone/ros2_ws/src/bennu_camera -e drone/ros2_ws/src/bennu_mission && python -m pytest drone/ros2_ws/src/bennu_mission/test/test_mission_manifest.py -v`
Expected: 3 PASS

**Step 5: Commit**

```bash
git add drone/ros2_ws/src/bennu_mission/ drone/ros2_ws/src/bennu_mission/test/test_mission_manifest.py
git commit -m "feat: add mission manifest generator (contract v1 compliant)"
```

---

### Task 10: Bundle Packager

**Files:**
- Create: `drone/ros2_ws/src/bennu_dataset/bennu_dataset/packager.py`
- Test: `drone/ros2_ws/src/bennu_dataset/test/test_packager.py`

**Context:** Assembles the full mission bundle directory structure: copies images, generates checksums, signs manifest, produces the final export-ready directory.

**Step 1: Write the failing test**

```python
# drone/ros2_ws/src/bennu_dataset/test/test_packager.py
import json
import hashlib
import pytest
from pathlib import Path
from bennu_dataset.packager import BundlePackager

def test_package_creates_bundle_structure(tmp_path):
    # Set up source images
    images_dir = tmp_path / "capture"
    images_dir.mkdir()
    (images_dir / "0001_rgb.jpg").write_bytes(b"fake-image-1")
    (images_dir / "0002_rgb.jpg").write_bytes(b"fake-image-2")

    manifest = {"contract_version": "v1", "mission_id": "test-001"}
    images_csv = "sequence,filename\n1,0001_rgb.jpg\n2,0002_rgb.jpg\n"
    flight_log = b"fake-ulg-data"

    output_dir = tmp_path / "bundle"
    packager = BundlePackager(output_dir=output_dir)
    quality_report = {
        "per_image": [
            {"filename": "0001_rgb.jpg", "score": 0.95, "flags": ["ok"]},
            {"filename": "0002_rgb.jpg", "score": 0.88, "flags": ["ok"]},
        ]
    }
    packager.package(
        mission_id="test-001",
        manifest=manifest,
        images_csv=images_csv,
        image_files=[images_dir / "0001_rgb.jpg", images_dir / "0002_rgb.jpg"],
        flight_log=flight_log,
        quality_report=quality_report,
    )

    bundle = output_dir / "test-001"
    assert (bundle / "contract_version").read_text() == "v1"
    assert (bundle / "manifest.json").exists()
    assert (bundle / "images" / "0001_rgb.jpg").exists()
    assert (bundle / "images" / "0002_rgb.jpg").exists()
    assert (bundle / "metadata" / "images.csv").exists()
    assert (bundle / "telemetry" / "flight.ulg").exists()
    assert (bundle / "quality" / "report.json").exists()
    assert (bundle / "checksums.sha256").exists()

def test_checksums_are_valid(tmp_path):
    images_dir = tmp_path / "capture"
    images_dir.mkdir()
    content = b"test-image-content"
    (images_dir / "0001_rgb.jpg").write_bytes(content)

    output_dir = tmp_path / "bundle"
    packager = BundlePackager(output_dir=output_dir)
    packager.package(
        mission_id="chk-test",
        manifest={"contract_version": "v1", "mission_id": "chk-test"},
        images_csv="sequence,filename\n1,0001_rgb.jpg\n",
        image_files=[images_dir / "0001_rgb.jpg"],
        flight_log=b"log",
        quality_report={"per_image": [{"filename": "0001_rgb.jpg", "score": 0.9, "flags": ["ok"]}]},
    )

    checksums_text = (output_dir / "chk-test" / "checksums.sha256").read_text()
    for line in checksums_text.strip().split("\n"):
        expected_hash, filepath = line.split("  ", 1)
        actual = hashlib.sha256((output_dir / "chk-test" / filepath).read_bytes()).hexdigest()
        assert actual == expected_hash
```

**Step 2: Run test to verify it fails**

Run: `cd /home/fadi/projects/bennu && pip install -e drone/ros2_ws/src/bennu_dataset && python -m pytest drone/ros2_ws/src/bennu_dataset/test/test_packager.py -v`
Expected: FAIL

**Step 3: Implement BundlePackager**

The packager:
- Creates `{mission_id}/` directory structure (images/, metadata/, telemetry/, quality/)
- Writes `contract_version` file
- Copies image files to `images/`
- Writes `metadata/images.csv`
- Writes `telemetry/flight.ulg`
- Writes `quality/report.json` (per-image quality scores and flags)
- Writes `manifest.json`
- Computes SHA-256 of all files → `checksums.sha256`

**Step 4: Run tests to verify they pass**

Run: `cd /home/fadi/projects/bennu && pip install -e drone/ros2_ws/src/bennu_dataset && python -m pytest drone/ros2_ws/src/bennu_dataset/test/test_packager.py -v`
Expected: 2 PASS

**Step 5: Commit**

```bash
git add drone/ros2_ws/src/bennu_dataset/bennu_dataset/packager.py drone/ros2_ws/src/bennu_dataset/test/test_packager.py
git commit -m "feat: add bundle packager with checksum generation"
```

---

### Task 11: End-to-End Bundle Generation Test

**Files:**
- Test: `tests/integration/test_bundle_e2e.py`

**Context:** Integration test that exercises the full pipeline: DroneIdentity → ImageMetadata → quality scoring → ManifestGenerator → BundlePackager → signer → schema validation. This is the most critical test — it proves the drone produces valid bundles.

**Step 1: Write the integration test**

```python
# tests/integration/test_bundle_e2e.py
import json
import jsonschema
import numpy as np
import pytest
from pathlib import Path
from bennu_core.drone_identity import DroneIdentity
from bennu_camera.geotag import ImageMetadata, compute_gsd
from bennu_camera.quality import ImageQualityScorer
from bennu_mission.mission_manifest import ManifestGenerator
from bennu_dataset.packager import BundlePackager
from bennu_dataset.signer import ManifestSigner

CONTRACT_SCHEMA = Path(__file__).parent.parent.parent / "contract" / "v1" / "manifest.schema.json"

def test_full_bundle_pipeline(tmp_path):
    # 1. Setup identity
    identity = DroneIdentity("bennu-001", "Pixhawk6C", "1.16.1", "F9P", ["rgb:IMX477"])

    # 2. Simulate captures with quality scoring
    scorer = ImageQualityScorer()
    images_dir = tmp_path / "captures"
    images_dir.mkdir()

    metadata_list = []
    for i in range(1, 6):
        img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        # Save as JPEG bytes
        import cv2
        filepath = images_dir / f"{i:04d}_rgb.jpg"
        cv2.imwrite(str(filepath), img)

        result = scorer.score(img)
        meta = ImageMetadata(
            sequence=i, filename=f"{i:04d}_rgb.jpg", sensor="rgb",
            timestamp_utc=f"2026-03-15T10:3{i}:00Z",
            lat=35.6762 + i * 0.0001, lon=139.6503, alt_msl=120.5, alt_agl=80.0,
            heading_deg=90.0, pitch_deg=-90.0, roll_deg=0.0,
            rtk_fix_type="RTK_FIXED", position_accuracy_m=0.08,
            gsd_cm=compute_gsd(80.0, 6.0, 7.9, 3040),
            quality_score=result.score,
            quality_flags=",".join(result.flags) if result.flags else "ok",
            ambient_light_lux=45000.0,
        )
        metadata_list.append(meta)

    # 3. Generate manifest
    gen = ManifestGenerator(identity=identity, mission_id="e2e-test-001")
    manifest = gen.generate_manifest(
        images=metadata_list, sensor_config="mapping",
        trigger_mode="distance", trigger_distance_m=5.0,
        site_id="e2e-site", planned_altitude_m=80,
        planned_overlap_front=0.75, planned_overlap_side=0.65, planned_gsd_cm=2.1,
    )
    images_csv = gen.generate_images_csv(metadata_list)

    # 4. Sign manifest
    signer = ManifestSigner.generate()
    manifest_json = json.dumps(manifest, sort_keys=True)
    manifest["signature"] = signer.sign(manifest_json)

    # 5. Package bundle
    output_dir = tmp_path / "bundles"
    packager = BundlePackager(output_dir=output_dir)
    image_files = sorted(images_dir.glob("*.jpg"))
    packager.package(
        mission_id="e2e-test-001",
        manifest=manifest,
        images_csv=images_csv,
        image_files=image_files,
        flight_log=b"fake-ulg-data",
    )

    # 6. Validate bundle
    bundle_dir = output_dir / "e2e-test-001"
    assert bundle_dir.exists()

    # Schema validation
    schema = json.loads(CONTRACT_SCHEMA.read_text())
    produced_manifest = json.loads((bundle_dir / "manifest.json").read_text())
    jsonschema.validate(produced_manifest, schema)

    # Signature verification
    sig = produced_manifest.pop("signature")
    assert signer.verify(json.dumps(produced_manifest, sort_keys=True), sig)

    # All images present
    assert len(list((bundle_dir / "images").glob("*.jpg"))) == 5

    # CSV has correct row count
    csv_lines = (bundle_dir / "metadata" / "images.csv").read_text().strip().split("\n")
    assert len(csv_lines) == 6  # header + 5 rows
```

**Step 2: Run the integration test**

Run: `cd /home/fadi/projects/bennu && pip install -e drone/ros2_ws/src/bennu_core -e drone/ros2_ws/src/bennu_camera -e drone/ros2_ws/src/bennu_dataset -e drone/ros2_ws/src/bennu_mission && python -m pytest tests/integration/test_bundle_e2e.py -v`
Expected: 1 PASS

**Step 3: Commit**

```bash
git add tests/integration/test_bundle_e2e.py
git commit -m "test: add end-to-end bundle generation integration test"
```

---

**Phase 1 Exit Gate:**
- Image quality scoring produces blur/exposure flags with 0.0-1.0 score
- Enhanced geotag produces all 18 CSV columns including RTK fix type, GSD, and capture_offset_ms
- ManifestGenerator produces contract v1 compliant manifest.json
- BundlePackager assembles complete bundle with valid checksums
- End-to-end test passes: identity → capture → score → manifest → package → sign → validate
- ≥99% images have complete metadata fields (all 18 columns populated, nullable fields allowed)

---

## Phase 2: Sensor Configuration & Calibration

### Task 12: Sensor Configuration System

**Files:**
- Create: `drone/ros2_ws/src/bennu_camera/bennu_camera/sensor_config.py`
- Create: `drone/ros2_ws/src/bennu_bringup/config/sensor_configs/survey.yaml`
- Create: `drone/ros2_ws/src/bennu_bringup/config/sensor_configs/inspection.yaml`
- Create: `drone/ros2_ws/src/bennu_bringup/config/sensor_configs/mapping.yaml`
- Test: `drone/ros2_ws/src/bennu_camera/test/test_sensor_config.py`

**Context:** The drone carries one sensor configuration per flight (survey, inspection, mapping). The config determines which camera nodes to launch and what metadata fields to populate.

**Step 1: Write the failing test**

```python
# drone/ros2_ws/src/bennu_camera/test/test_sensor_config.py
import pytest
from bennu_camera.sensor_config import SensorConfig, load_sensor_config

def test_mapping_config():
    config = SensorConfig(name="mapping", sensors=["rgb:IMX477"])
    assert config.name == "mapping"
    assert len(config.sensors) == 1
    assert config.has_sensor("rgb")
    assert not config.has_sensor("nir")
    assert not config.has_sensor("thermal")

def test_survey_config():
    config = SensorConfig(
        name="survey",
        sensors=["rgb:IMX477", "nir:IMX708_NoIR"],
        has_ambient_light=True,
    )
    assert config.has_sensor("nir")
    assert config.has_ambient_light

def test_inspection_config():
    config = SensorConfig(
        name="inspection",
        sensors=["rgb:IMX477", "thermal:Lepton3.5"],
    )
    assert config.has_sensor("thermal")

def test_load_from_yaml(tmp_path):
    yaml_content = """
name: mapping
sensors:
  - rgb:IMX477
has_ambient_light: false
"""
    config_file = tmp_path / "mapping.yaml"
    config_file.write_text(yaml_content)
    config = load_sensor_config(config_file)
    assert config.name == "mapping"
    assert config.sensors == ["rgb:IMX477"]
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest drone/ros2_ws/src/bennu_camera/test/test_sensor_config.py -v`
Expected: FAIL

**Step 3: Implement SensorConfig**

Simple dataclass + YAML loader. Add `pyyaml>=6.0` to `requirements-dev.txt`.

Create the three YAML config files matching the design doc sensor configurations.

**Step 4: Run tests to verify they pass**

Expected: 4 PASS

**Step 5: Commit**

```bash
git add drone/ros2_ws/src/bennu_camera/bennu_camera/sensor_config.py \
  drone/ros2_ws/src/bennu_bringup/config/sensor_configs/ \
  drone/ros2_ws/src/bennu_camera/test/test_sensor_config.py requirements-dev.txt
git commit -m "feat: add sensor configuration system (survey, inspection, mapping)"
```

---

### Task 13: Calibration Data Collection

**Files:**
- Create: `drone/ros2_ws/src/bennu_camera/bennu_camera/calibration.py`
- Test: `drone/ros2_ws/src/bennu_camera/test/test_calibration.py`

**Context:** For Config A (survey), ambient light readings from BH1750 are recorded per capture. This module stores calibration readings and generates `calibration.csv` for the bundle.

**Step 1: Write the failing test**

```python
# drone/ros2_ws/src/bennu_camera/test/test_calibration.py
import pytest
from bennu_camera.calibration import CalibrationCollector

def test_add_and_export_readings():
    collector = CalibrationCollector()
    collector.add_reading(sequence=1, timestamp="2026-03-15T10:32:00Z", ambient_lux=45000.0)
    collector.add_reading(sequence=2, timestamp="2026-03-15T10:32:05Z", ambient_lux=44500.0)
    csv = collector.to_csv()
    lines = csv.strip().split("\n")
    assert len(lines) == 3  # header + 2
    assert "ambient_lux" in lines[0]

def test_empty_collector():
    collector = CalibrationCollector()
    csv = collector.to_csv()
    lines = csv.strip().split("\n")
    assert len(lines) == 1  # header only
```

**Step 2-5:** Standard TDD cycle: run failing → implement → run passing → commit.

```bash
git commit -m "feat: add calibration data collector for ambient light readings"
```

---

**Phase 2 Exit Gate:**
- Sensor configurations loadable from YAML
- Config determines which sensors are active per flight
- Calibration CSV generated for ambient light readings
- Bundle includes calibration.csv when sensor config has ambient light

---

## Phase 3: Survey Intelligence

### Task 14: Survey Grid Planner

**Files:**
- Create: `drone/ros2_ws/src/bennu_survey/package.xml`
- Create: `drone/ros2_ws/src/bennu_survey/setup.py`
- Create: `drone/ros2_ws/src/bennu_survey/setup.cfg`
- Create: `drone/ros2_ws/src/bennu_survey/resource/bennu_survey`
- Create: `drone/ros2_ws/src/bennu_survey/bennu_survey/__init__.py`
- Create: `drone/ros2_ws/src/bennu_survey/bennu_survey/grid_planner.py`
- Test: `drone/ros2_ws/src/bennu_survey/test/test_grid_planner.py`

**Context:** Generates a survey grid (list of waypoints) from an AOI polygon + desired overlap + altitude + GSD. This is the core of mission planning. Uses simple UTM projection for distance calculations.

**Step 1: Write the failing test**

```python
# drone/ros2_ws/src/bennu_survey/test/test_grid_planner.py
import pytest
from bennu_survey.grid_planner import GridPlanner

def test_square_aoi_generates_grid():
    # 100m x 100m square
    aoi = [
        (35.0, 139.0),
        (35.0, 139.001),
        (35.001, 139.001),
        (35.001, 139.0),
    ]
    planner = GridPlanner(
        overlap_front=0.75,
        overlap_side=0.65,
        altitude_m=80,
        gsd_cm=2.1,
        sensor_width_px=4056,
        sensor_height_px=3040,
        focal_length_mm=6.0,
        sensor_width_mm=7.9 * 4056 / 3040,  # ~10.6mm
    )
    waypoints = planner.plan(aoi)
    assert len(waypoints) > 0
    for wp in waypoints:
        assert "lat" in wp
        assert "lon" in wp
        assert "alt" in wp
        assert wp["alt"] == 80

def test_line_spacing_respects_overlap():
    aoi = [
        (35.0, 139.0),
        (35.0, 139.002),
        (35.002, 139.002),
        (35.002, 139.0),
    ]
    planner = GridPlanner(
        overlap_front=0.75, overlap_side=0.65,
        altitude_m=80, gsd_cm=2.1,
        sensor_width_px=4056, sensor_height_px=3040,
        focal_length_mm=6.0, sensor_width_mm=10.6,
    )
    waypoints = planner.plan(aoi)
    # With 65% side overlap, line spacing should be ~35% of ground coverage width
    assert len(waypoints) >= 4  # At least 2 lines with 2+ points each
```

**Step 2-5:** Standard TDD cycle.

```bash
git commit -m "feat: add survey grid planner with overlap-based waypoint generation"
```

---

### Task 15: DEM-Based Terrain Following

**Files:**
- Create: `drone/ros2_ws/src/bennu_survey/bennu_survey/terrain_follow.py`
- Test: `drone/ros2_ws/src/bennu_survey/test/test_terrain_follow.py`

**Context:** Adjusts planned waypoint altitudes based on ground elevation from a DEM (GeoTIFF). Target AGL remains constant regardless of terrain undulation. Uses rasterio.

**Step 1: Write the failing test**

```python
# drone/ros2_ws/src/bennu_survey/test/test_terrain_follow.py
import numpy as np
import pytest
from bennu_survey.terrain_follow import adjust_waypoints_for_terrain

def test_flat_terrain_no_change():
    waypoints = [
        {"lat": 35.0, "lon": 139.0, "alt": 80},
        {"lat": 35.001, "lon": 139.0, "alt": 80},
    ]
    # Flat DEM: all elevations = 100m MSL
    def mock_elevation(lat, lon):
        return 100.0

    adjusted = adjust_waypoints_for_terrain(waypoints, target_agl=80, elevation_fn=mock_elevation)
    assert adjusted[0]["alt"] == 180.0  # 100m ground + 80m AGL
    assert adjusted[1]["alt"] == 180.0

def test_sloped_terrain_adjusts():
    waypoints = [
        {"lat": 35.0, "lon": 139.0, "alt": 80},
        {"lat": 35.001, "lon": 139.0, "alt": 80},
    ]
    def mock_elevation(lat, lon):
        return 100.0 if lat < 35.0005 else 150.0

    adjusted = adjust_waypoints_for_terrain(waypoints, target_agl=80, elevation_fn=mock_elevation)
    assert adjusted[0]["alt"] == 180.0  # 100 + 80
    assert adjusted[1]["alt"] == 230.0  # 150 + 80
```

**Step 2-5:** Standard TDD cycle.

```bash
git commit -m "feat: add DEM-based terrain following for survey waypoints"
```

---

### Task 16: Coverage Tracker

**Files:**
- Create: `drone/ros2_ws/src/bennu_mission/bennu_mission/coverage_tracker.py`
- Test: `drone/ros2_ws/src/bennu_mission/test/test_coverage_tracker.py`

**Context:** Tracks which planned grid cells have been covered by actual image captures, reports coverage percentage, and identifies gaps. Uses image footprints (computed from GSD + sensor dimensions) to determine which grid cells each capture covers. This is more accurate than waypoint proximity — it reflects actual photogrammetric coverage even when triggers are missed or spacing changes. Feeds into `quality_summary.coverage_pct` in the manifest.

**Step 1: Write the failing test**

```python
# drone/ros2_ws/src/bennu_mission/test/test_coverage_tracker.py
import pytest
from bennu_mission.coverage_tracker import CoverageTracker

def test_coverage_starts_at_zero():
    """Grid cells with no image footprints report 0% coverage."""
    grid_cells = [
        {"lat": 35.0, "lon": 139.0},
        {"lat": 35.001, "lon": 139.0},
        {"lat": 35.002, "lon": 139.0},
    ]
    tracker = CoverageTracker(grid_cells, cell_size_m=20.0)
    assert tracker.coverage_pct() == 0.0

def test_coverage_from_image_footprint():
    """An image at a grid cell position with sufficient GSD covers that cell."""
    grid_cells = [
        {"lat": 35.0, "lon": 139.0},
        {"lat": 35.0001, "lon": 139.0},  # ~11m apart
    ]
    tracker = CoverageTracker(grid_cells, cell_size_m=20.0)
    # Image at first cell: footprint_m = gsd_cm/100 * image_width_px
    # 2.1cm GSD * 4056px = ~85m footprint — covers both cells
    tracker.record_capture(lat=35.0, lon=139.0, gsd_cm=2.1, image_width_px=4056, image_height_px=3040)
    assert tracker.coverage_pct() == 1.0

def test_partial_coverage():
    """Well-separated cells require separate captures."""
    grid_cells = [
        {"lat": 35.0, "lon": 139.0},
        {"lat": 35.005, "lon": 139.0},  # ~550m apart
    ]
    tracker = CoverageTracker(grid_cells, cell_size_m=20.0)
    tracker.record_capture(lat=35.0, lon=139.0, gsd_cm=2.1, image_width_px=4056, image_height_px=3040)
    assert tracker.coverage_pct() == 0.5

def test_gaps_reported():
    """Uncovered grid cells are reported as gaps."""
    grid_cells = [
        {"lat": 35.0, "lon": 139.0},
        {"lat": 35.005, "lon": 139.0},  # ~550m apart
        {"lat": 35.010, "lon": 139.0},  # ~1100m apart
    ]
    tracker = CoverageTracker(grid_cells, cell_size_m=20.0)
    tracker.record_capture(lat=35.0, lon=139.0, gsd_cm=2.1, image_width_px=4056, image_height_px=3040)
    tracker.record_capture(lat=35.010, lon=139.0, gsd_cm=2.1, image_width_px=4056, image_height_px=3040)
    gaps = tracker.gaps()
    assert len(gaps) == 1
    assert gaps[0]["lat"] == 35.005
```

**Step 2-5:** Standard TDD cycle.

```bash
git commit -m "feat: add coverage tracker for survey gap detection"
```

---

### Task 17: Repeat Mission Support

**Files:**
- Create: `drone/ros2_ws/src/bennu_mission/bennu_mission/repeat_mission.py`
- Test: `drone/ros2_ws/src/bennu_mission/test/test_repeat_mission.py`

**Context:** Re-fly the same grid for change detection. Loads a previous mission's waypoints and replays them. Tracks deviation from the planned path for repeatability metrics.

**Step 1: Write the failing test**

```python
# drone/ros2_ws/src/bennu_mission/test/test_repeat_mission.py
import json
import pytest
from bennu_mission.repeat_mission import RepeatMission

def test_load_previous_waypoints():
    previous = {
        "mission_id": "site-alpha-001",
        "waypoints": [
            {"lat": 35.0, "lon": 139.0, "alt": 80},
            {"lat": 35.001, "lon": 139.0, "alt": 80},
        ],
    }
    repeat = RepeatMission.from_previous(previous)
    assert repeat.reference_mission_id == "site-alpha-001"
    assert len(repeat.waypoints) == 2

def test_deviation_zero_for_exact_match():
    previous = {
        "mission_id": "ref-001",
        "waypoints": [{"lat": 35.0, "lon": 139.0, "alt": 80}],
    }
    repeat = RepeatMission.from_previous(previous)
    deviation = repeat.compute_deviation(
        actual_positions=[{"lat": 35.0, "lon": 139.0}]
    )
    assert deviation["max_deviation_m"] < 1.0
    assert deviation["mean_deviation_m"] < 1.0
```

**Step 2-5:** Standard TDD cycle.

```bash
git commit -m "feat: add repeat mission support for change detection workflows"
```

---

---

### Task 18: Mission Execution Node

**Files:**
- Create: `drone/ros2_ws/src/bennu_mission/bennu_mission/mission_node.py`
- Create: `drone/ros2_ws/src/bennu_bringup/launch/survey.launch.py`
- Create: `drone/ros2_ws/src/bennu_bringup/launch/mapping.launch.py`
- Test: `drone/ros2_ws/src/bennu_mission/test/test_mission_node.py`

**Context:** The grid planner produces waypoints but nothing executes them. `mission_node.py` is a ROS2 node that uploads waypoints to PX4 via uXRCE-DDS (using `TrajectorySetpoint` or `VehicleCommand` messages), monitors flight progress, triggers capture pipeline at each waypoint, and transitions through mission states (idle → armed → takeoff → mission → RTL → land). Launch files wire everything together for specific mission profiles.

**Step 1: Write the failing test**

```python
# drone/ros2_ws/src/bennu_mission/test/test_mission_node.py
import pytest
from bennu_mission.mission_node import MissionExecutor, MissionState

def test_mission_starts_idle():
    executor = MissionExecutor(waypoints=[])
    assert executor.state == MissionState.IDLE

def test_mission_state_transitions():
    waypoints = [
        {"lat": 35.0, "lon": 139.0, "alt": 80},
        {"lat": 35.001, "lon": 139.0, "alt": 80},
    ]
    executor = MissionExecutor(waypoints=waypoints)
    assert executor.state == MissionState.IDLE
    executor.arm()
    assert executor.state == MissionState.ARMED
    executor.takeoff()
    assert executor.state == MissionState.TAKEOFF

def test_waypoint_progress():
    waypoints = [
        {"lat": 35.0, "lon": 139.0, "alt": 80},
        {"lat": 35.001, "lon": 139.0, "alt": 80},
        {"lat": 35.002, "lon": 139.0, "alt": 80},
    ]
    executor = MissionExecutor(waypoints=waypoints)
    assert executor.current_waypoint_index == 0
    executor.advance_waypoint()
    assert executor.current_waypoint_index == 1
    assert executor.progress_pct() == pytest.approx(1 / 3, abs=0.01)
```

**Step 2-5:** Standard TDD cycle. The full ROS2 node (publishing to PX4 topics) is tested in SITL; the unit tests cover state machine logic and waypoint management only.

```bash
git commit -m "feat: add mission execution node with state machine and launch files"
```

---

**Phase 3 Exit Gate:**
- Grid planner generates waypoints from AOI polygon + overlap parameters
- Terrain following adjusts waypoint altitudes based on DEM
- Coverage tracker reports image-footprint-based percentage and identifies gaps
- Mission executor manages flight state machine and waypoint progress
- Launch files wire survey and mapping mission profiles
- Repeat mission re-uses previous waypoints with deviation tracking

---

## Phase Summary

| Phase | Tasks | Key Deliverable |
|---|---|---|
| 0: Foundation | 1-6 | Contract schema, CI, governance, identity, signing |
| 1: Data Quality | 7-11 | Quality scoring, geotagging, manifest, packager, e2e test |
| 2: Sensor Config | 12-13 | Sensor configs, calibration data |
| 3: Survey Intelligence | 14-18 | Grid planner, terrain following, coverage, mission execution, repeat missions |

Total: 18 tasks, each independently testable and committable.

After all tasks, the drone can:
1. Plan a survey grid for any polygon AOI
2. Adjust altitudes for terrain
3. Execute a planned mission (upload waypoints, fly, trigger captures)
4. Capture images with quality scoring
5. Generate full metadata (18 columns including RTK, GSD, and capture_offset_ms)
6. Package a signed, schema-validated mission bundle
7. Track coverage via image footprints and identify gaps
8. Repeat missions for change detection
