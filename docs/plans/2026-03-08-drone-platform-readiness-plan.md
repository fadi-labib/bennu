# Drone Platform-Readiness — Owner Walkthrough

**Goal:** Evolve Bennu from a photogrammetry prototype into a production-grade data acquisition system that produces versioned, signed mission bundles.

**How this works:** Claude implements each task. You audit the code, run the tests, and accept before moving to the next task. Each task produces one testable module. Bug fixes come first (safety-critical), then new features phase by phase.

**Design Doc:** `docs/plans/2026-03-08-drone-platform-readiness-design.md`

**Tech Stack:** Python 3.12, ROS2 Jazzy, PX4 v1.16+, uXRCE-DDS, pytest, jsonschema, PyNaCl, Gazebo Harmonic

---

## Pre-flight: Bug Fixes

These are open GitHub issues. Fix them before building new features.

### Bug 1: NAV_DLL_ACT Failsafe Disabled (GitHub #1) — SAFETY

**What:** `NAV_DLL_ACT: 0` in `firmware/px4/params/base_params.yaml` means failsafe is **disabled**, not RTL. On data link loss the drone does nothing.

**Fix:** Change to `NAV_DLL_ACT: 2` (RTL). Update the comment to show valid values.

**File:** `firmware/px4/params/base_params.yaml`

**Your Audit:**
- Open the file, verify `NAV_DLL_ACT: 2` with a comment listing all values (0=Disabled 1=Hold 2=RTL 3=Land)
- Cross-check with [PX4 parameter reference](https://docs.px4.io/main/en/advanced_config/parameter_reference.html)

---

### Bug 2: Double XRCE-DDS Agent in Sim (GitHub #2)

**What:** `drone.launch.py` starts an XRCE-DDS agent, but `docker-compose.sim.yml` also starts one in the ros2-dev container entrypoint. Two agents = port conflict.

**Fix:** Remove the agent from the Docker entrypoint; let the launch file manage it.

**Files:** `sim/Dockerfile.ros2`, `sim/docker-compose.sim.yml`

**Your Audit:**
- Verify Dockerfile.ros2 entrypoint no longer starts MicroXRCEAgent
- Run `cd sim && docker compose -f docker-compose.sim.yml up` — confirm only one agent in logs

---

### Bug 3: bennu_camera Not ament_python Compliant (GitHub #3)

**What:** Package may be missing `setup.cfg` entries or have incorrect `ament_python` packaging.

**Fix:** Ensure `setup.cfg`, `setup.py`, `package.xml`, and resource marker follow ament_python conventions.

**Files:** `drone/ros2_ws/src/bennu_camera/setup.cfg`, `setup.py`, `package.xml`

**Your Audit:**
- `setup.cfg` has `[develop] script_dir=$base/lib/bennu_camera` and `[install] install_scripts=$base/lib/bennu_camera`
- `package.xml` has `<build_type>ament_python</build_type>`
- `resource/bennu_camera` marker file exists
- Run `cd drone/ros2_ws && colcon build --packages-select bennu_camera` — should succeed

---

### Bug 4: XRCE-DDS Agent Binary Name Mismatch (GitHub #4)

**What:** Different environments use different binary names (`MicroXRCEAgent` vs `micro_ros_agent`).

**Fix:** Use the correct binary name for ROS2 Jazzy (`MicroXRCEAgent`), add a check in the launch file.

**Your Audit:**
- Verify launch file uses the correct binary name
- Run the sim stack and confirm agent starts without "command not found"

---

### Bug 5: PX4 Parameter Uploader Fragile (GitHub #5)

**What:** `upload_params.sh` has minimal error handling.

**Fix:** Add parameter file existence checks, MAVLink connection validation, and clearer error messages.

**File:** `firmware/px4/upload_params.sh`

**Your Audit:**
- Run `./firmware/px4/upload_params.sh` with no drone connected — should show helpful error, not crash
- Run with a nonexistent param file — should report which file is missing

---

### Bug 6: ODM Process Script Fails on Empty Folder (GitHub #6)

**What:** `ground/odm/process.sh` crashes with unclear error when given an empty image folder.

**Fix:** Check for images before invoking ODM Docker, show clear message.

**File:** `ground/odm/process.sh`

**Your Audit:**
- Create empty folder, run `./ground/odm/process.sh /tmp/empty-test` — should say "No images found" and exit cleanly

---

### Bug 7-8: Documentation Issues (GitHub #7, #8)

**What:** Missing docs on Pi 5 power architecture and vibration damping for camera mount.

**Fix:** Add documentation pages.

**Your Audit:**
- Pages exist and are linked in mkdocs.yml nav
- Content is technically accurate (you know the hardware)

---

**Pre-flight Gate:** All 8 bugs fixed, pushed, issues closed.

---

## Phase 0: Foundation & Governance

### Task 1: Mission Bundle Contract Schema

**What:** The mission bundle is the ONLY coupling point between drone and platform. This JSON schema defines exactly what the drone must produce. Everything else builds on this contract.

**Why it matters:** If the schema is wrong, every downstream module produces invalid data.

**Files:**
- Create: `contract/v1/manifest.schema.json`
- Create: `contract/v1/images.schema.json` (18-column CSV definitions)
- Create: `contract/v1/README.md`
- Create: `contract/v1/example/manifest.json`
- Create: `contract/v1/example/images.csv`
- Test: `tests/contract/test_schema_validation.py`

**Key decisions baked into the schema:**
- `survey` is **optional** — manual/test flights omit it
- `coverage_pct` is **nullable** — null when no survey grid defined
- `checksums_digest` is **required** — SHA-256 of checksums.sha256 (integrity chain)
- 18 CSV columns including `capture_offset_ms` (nullable, for multi-sensor sync)

**Tests (6):**

```python
# tests/contract/test_schema_validation.py
def test_example_manifest_validates()          # Example passes schema
def test_manifest_rejects_missing_required()   # Missing fields → rejected
def test_contract_version_is_v1()              # Version pinned
def test_manifest_without_survey_validates()   # Optional survey works
def test_checksums_digest_required()           # Integrity chain enforced
def test_images_csv_columns_match_schema()     # CSV header matches schema
```

**Your Audit:**
1. Read `contract/v1/manifest.schema.json` — verify every field from the design doc's manifest.json example is present
2. Read `contract/v1/images.schema.json` — verify 18 columns match design doc's images.csv table
3. Read `contract/v1/example/manifest.json` — should be a valid, realistic example
4. Run: `python -m pytest tests/contract/ -v` — all 6 pass
5. Try breaking the example (delete a required field, re-run tests) — verify schema catches it

**Accept:**
- [ ] Schema matches design doc manifest structure
- [ ] Example validates against schema
- [ ] Removing `survey` still validates
- [ ] Removing `checksums_digest` fails validation
- [ ] CSV columns match schema exactly (18 columns)

---

### Task 2: Compatibility Matrix

**What:** Pin exact versions of PX4, ROS2, px4_msgs, XRCE-DDS that are tested together.

**Why:** Version drift silently breaks builds.

**File:** `docs/reference/compatibility-matrix.md`

**Content:**

| Component | Version | Notes |
|---|---|---|
| PX4 Autopilot | v1.16.1 | Pinned tag |
| ROS2 | Jazzy Jalisco | Ubuntu 24.04 |
| px4_msgs | Match PX4 v1.16.1 tag | Must match PX4 version exactly |
| Micro-XRCE-DDS Agent | v2.4.x | From ROS2 Jazzy repos |
| Gazebo | Harmonic | SITL only |
| Python | 3.12 | Ubuntu 24.04 default |
| Ubuntu | 24.04 LTS | Pi 5 and Docker |

**Your Audit:**
- Cross-check versions against what's in `sim/Dockerfile.px4` and `sim/Dockerfile.ros2`

**Accept:**
- [ ] Versions match what's actually pinned in Docker and configs

---

### Task 3: CI Pipeline

**What:** GitHub Actions runs lint (ruff) + tests (pytest) on every PR.

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `requirements-dev.txt`

**CI does:**
1. Install dev requirements (pytest, jsonschema, ruff)
2. `pip install -e` all bennu packages
3. `ruff check .`
4. `python -m pytest drone/ros2_ws/src/*/test/ tests/ -v`

**Your Audit:**
1. Read `.github/workflows/ci.yml` — verify it runs on push+PR to main
2. Run locally: `pip install -r requirements-dev.txt && ruff check . && python -m pytest tests/ -v`
3. Push a branch, open a draft PR — verify CI runs

**Accept:**
- [ ] CI passes locally
- [ ] CI runs on GitHub Actions

---

### Task 4: Governance Files

**What:** LICENSE (Apache-2.0), CONTRIBUTING.md, SECURITY.md. Update existing packages from MIT to Apache-2.0.

**Files:**
- Create: `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`
- Modify: `drone/ros2_ws/src/bennu_camera/package.xml` (MIT → Apache-2.0)
- Modify: `drone/ros2_ws/src/bennu_camera/setup.py` (MIT → Apache-2.0)
- Modify: `drone/ros2_ws/src/bennu_bringup/package.xml` (MIT → Apache-2.0)

**Your Audit:**
- Verify LICENSE is full Apache 2.0 text
- Grep for "MIT" in `drone/ros2_ws/src/` — should find nothing

**Accept:**
- [ ] LICENSE file is Apache-2.0
- [ ] No MIT references remain in package files

---

### Task 5: bennu_core — Drone Identity

**What:** `DroneIdentity` dataclass that holds drone ID, hardware config (flight controller, PX4 version, GPS model, sensors). Every manifest needs this.

**Why:** Identity is the foundation for signing and manifest generation.

**Package:** `drone/ros2_ws/src/bennu_core/`
**Module:** `bennu_core/drone_identity.py`
**Test:** `drone/ros2_ws/src/bennu_core/test/test_drone_identity.py`

**What the code does:**
- `DroneIdentity(drone_id, flight_controller, px4_version, gps_model, sensors)` — stores drone hardware info
- `.hardware_manifest()` → returns dict matching `drone_hardware` in manifest.json

**Tests (2):**
```python
def test_drone_identity_loads_config()     # Fields stored correctly
def test_hardware_manifest_structure()     # Output dict has all required keys
```

**Your Audit:**
1. Read `drone_identity.py` — it should be a simple dataclass, ~20 lines
2. Verify `hardware_manifest()` returns keys matching `drone_hardware` in the JSON schema
3. Run: `pip install -e drone/ros2_ws/src/bennu_core && python -m pytest drone/ros2_ws/src/bennu_core/test/ -v`

**Accept:**
- [ ] `hardware_manifest()` keys match `manifest.schema.json`'s `drone_hardware` properties
- [ ] Tests pass

---

### Task 6: bennu_dataset — Ed25519 Signer

**What:** `ManifestSigner` generates Ed25519 keypairs, signs canonical JSON, verifies signatures. Used in the integrity chain: manifest covers checksums, signature covers manifest.

**Why:** Platform rejects unsigned bundles. This is how the drone proves data authenticity.

**Package:** `drone/ros2_ws/src/bennu_dataset/`
**Module:** `bennu_dataset/signer.py`
**Test:** `drone/ros2_ws/src/bennu_dataset/test/test_signer.py`

**What the code does:**
- `ManifestSigner.generate()` — creates new keypair
- `ManifestSigner.from_files(key_path, pub_path)` — loads existing keys
- `.canonicalize(dict)` → deterministic JSON (`json.dumps(m, sort_keys=True, separators=(",",":"))`)
- `.sign(data_str)` → base64 Ed25519 signature
- `.verify(data_str, signature)` → True/False

**Tests (4):**
```python
def test_sign_and_verify()                 # Round-trip sign → verify
def test_canonicalize_is_deterministic()   # Key order doesn't matter
def test_verify_rejects_tampered()         # Modified data → reject
def test_export_and_import_keys()          # Save/load keypair from files
```

**Your Audit:**
1. Read `signer.py` — verify it uses `nacl.signing` (not custom crypto)
2. Verify `canonicalize()` uses `sort_keys=True, separators=(",",":")`
3. Test manually: `python -c "from bennu_dataset.signer import ManifestSigner; s = ManifestSigner.generate(); print(s.canonicalize({'b':2,'a':1}))"`  — should print `{"a":1,"b":2}`
4. Run: `pip install -e drone/ros2_ws/src/bennu_dataset && python -m pytest drone/ros2_ws/src/bennu_dataset/test/ -v`

**Accept:**
- [ ] Uses PyNaCl (not hand-rolled crypto)
- [ ] Canonical JSON is deterministic
- [ ] Tampered data is rejected
- [ ] Keys can be saved/loaded from disk
- [ ] Tests pass

---

**Phase 0 Exit Gate:**
- [ ] CI runs lint + tests on every PR
- [ ] Contract schema validates example manifest
- [ ] DroneIdentity produces hardware manifest dict
- [ ] ManifestSigner signs and verifies with canonical JSON
- [ ] Apache-2.0 license, governance files in place

---

## Phase 1: Data Quality Baseline

### Task 7: Image Quality Scoring

**What:** `ImageQualityScorer` analyzes an image and returns a 0.0-1.0 quality score with flags (ok, blur, overexposed, underexposed). Uses Laplacian variance for blur detection and histogram analysis for exposure.

**Why:** The platform needs to know which images are usable. Bad images (blurry from vibration, over/underexposed) should be flagged, not silently included.

**Module:** `bennu_camera/quality.py`
**Test:** `drone/ros2_ws/src/bennu_camera/test/test_quality.py`

**What the code does:**
- `ImageQualityScorer(blur_threshold)` — configurable blur sensitivity
- `.score(image_array)` → `QualityResult(score, flags, blur_variance)`
- Blur: Laplacian variance < threshold → "blur" flag
- Exposure: histogram analysis → "overexposed" or "underexposed" flags

**Tests (5):**
```python
def test_sharp_image_scores_high()         # Random noise (high freq) → score > 0.5
def test_blurry_image_scores_low()         # Gaussian-blurred → score < 0.5, "blur" flag
def test_overexposed_image_flagged()       # White image → "overexposed" flag
def test_underexposed_image_flagged()      # Black image → "underexposed" flag
def test_quality_flags_include_ok()        # Normal image → "ok" flag only
```

**Your Audit:**
1. Read `quality.py` — verify Laplacian variance formula is correct (`cv2.Laplacian(gray, cv2.CV_64F).var()`)
2. Check threshold logic: blur_variance < blur_threshold → blurry
3. Check histogram analysis: does it correctly detect over/underexposure?
4. Run: `pip install -e drone/ros2_ws/src/bennu_camera && python -m pytest drone/ros2_ws/src/bennu_camera/test/test_quality.py -v`

**Accept:**
- [ ] Laplacian-based blur detection works (real drone images will vibrate)
- [ ] Histogram-based exposure detection works
- [ ] Score is 0.0-1.0 range
- [ ] Tests pass

---

### Task 8: Enhanced Geotag — 18-Column ImageMetadata

**What:** `ImageMetadata` dataclass with all 18 CSV columns. `compute_gsd()` function calculates ground sample distance from altitude + lens params. This replaces the existing basic geotag with full metadata.

**Why:** The platform needs precise per-image metadata for georeferencing, quality assessment, and coverage analysis.

**Module:** `bennu_camera/geotag.py` (enhanced — existing code stays)
**Test:** `drone/ros2_ws/src/bennu_camera/test/test_geotag.py`

**The 18 columns:**
sequence, filename, sensor, timestamp_utc, lat, lon, alt_msl, alt_agl, heading_deg, pitch_deg, roll_deg, rtk_fix_type, position_accuracy_m, gsd_cm, quality_score, quality_flags, ambient_light_lux, capture_offset_ms

**What the code does:**
- `ImageMetadata(...)` — dataclass with all 18 fields
- `.to_csv_dict()` → ordered dict for CSV writing
- `compute_gsd(altitude_m, focal_length_mm, sensor_height_mm, image_height_px)` → GSD in cm

**Tests (3):**
```python
def test_image_metadata_to_csv_row()       # All 18 fields present, correct values
def test_gsd_scales_with_altitude()        # Double altitude → double GSD (linear)
def test_gsd_known_value()                 # 80m, 6mm lens, IMX477 → ~2.1cm (sanity)
```

**Your Audit:**
1. Read `geotag.py` — verify all 18 columns from design doc's images.csv table are in the dataclass
2. Check `to_csv_dict()` column order matches `images.schema.json`
3. Verify GSD formula: `gsd_cm = (altitude_m * sensor_height_mm) / (focal_length_mm * image_height_px) * 100`
4. Verify nullable fields: `ambient_light_lux` and `capture_offset_ms` can be None
5. Run: `python -m pytest drone/ros2_ws/src/bennu_camera/test/test_geotag.py -v`

**Accept:**
- [ ] 18 columns match design doc exactly
- [ ] GSD formula produces ~2.1cm at 80m with 6mm lens on IMX477
- [ ] Nullable fields handled correctly
- [ ] Tests pass

---

### Task 9: Mission Manifest Generator

**What:** `ManifestGenerator` takes drone identity + captured image metadata + mission parameters and produces a contract v1 compliant `manifest.json` dict and `images.csv` string.

**Why:** This is where all the per-image data gets aggregated into the bundle's metadata files.

**Package:** `drone/ros2_ws/src/bennu_mission/`
**Module:** `bennu_mission/mission_manifest.py`
**Test:** `drone/ros2_ws/src/bennu_mission/test/test_mission_manifest.py`

**What the code does:**
- `ManifestGenerator(identity, mission_id)` — bound to a specific drone + mission
- `.generate_manifest(images, sensor_config, ...)` → manifest dict
- `.generate_images_csv(images)` → CSV string with header + rows
- Quality summary: counts passed/failed (threshold: 0.5), failure reasons, RTK fixed percentage

**Tests (3):**
```python
def test_manifest_matches_schema()         # Output validates against manifest.schema.json
def test_generate_images_csv()             # CSV has correct header (18 cols) and row count
def test_quality_summary_counts()          # 3 images (1 pass, 2 fail) → correct counts
```

**Your Audit:**
1. Read `mission_manifest.py` — verify output structure matches `manifest.schema.json`
2. Validate the generated manifest against schema manually:
   ```python
   import json, jsonschema
   schema = json.load(open("contract/v1/manifest.schema.json"))
   jsonschema.validate(generated_manifest, schema)
   ```
3. Check CSV header order matches `images.schema.json` column order
4. Check quality_summary logic: `score < 0.5` → failed, failure reasons aggregated
5. Run: `pip install -e drone/ros2_ws/src/bennu_core -e drone/ros2_ws/src/bennu_camera -e drone/ros2_ws/src/bennu_mission && python -m pytest drone/ros2_ws/src/bennu_mission/test/ -v`

**Accept:**
- [ ] Generated manifest validates against schema
- [ ] CSV has exactly 18 columns in correct order
- [ ] Quality summary counts are correct
- [ ] Tests pass

---

### Task 10: Bundle Packager

**What:** `BundlePackager` assembles the complete mission bundle directory: copies images, writes metadata, generates quality report, computes checksums.

**Why:** This creates the actual directory structure that gets signed and exported.

**Module:** `bennu_dataset/packager.py`
**Test:** `drone/ros2_ws/src/bennu_dataset/test/test_packager.py`

**Bundle structure produced:**
```
{mission_id}/
├── contract_version          # "v1"
├── manifest.json
├── images/
│   └── *.jpg
├── metadata/
│   └── images.csv
├── telemetry/
│   └── flight.ulg
├── quality/
│   └── report.json
└── checksums.sha256
```

**What the code does:**
- `BundlePackager(output_dir)` — sets output location
- `.package(mission_id, manifest, images_csv, image_files, flight_log, quality_report)` — assembles everything
- Computes SHA-256 of every file → writes `checksums.sha256`

**Tests (2):**
```python
def test_package_creates_bundle_structure()   # All dirs and files exist
def test_checksums_are_valid()                # SHA-256 checksums actually match file contents
```

**Your Audit:**
1. Read `packager.py` — verify it creates ALL directories from the design doc bundle structure
2. Verify `quality/report.json` is written (was missing before)
3. Verify checksum format: `<hex-sha256>  <relative-path>` (two spaces, standard `sha256sum` format)
4. Run: `python -m pytest drone/ros2_ws/src/bennu_dataset/test/test_packager.py -v`
5. Manual check: inspect the tmp output directory to verify the actual file tree

**Accept:**
- [ ] Bundle structure matches design doc exactly
- [ ] quality/report.json is included
- [ ] checksums.sha256 contains valid hashes for every file
- [ ] Tests pass

---

### Task 11: End-to-End Bundle Test

**What:** Integration test that runs the full pipeline: identity → quality scoring → geotag → manifest → packager → signer → schema validation. Proves the drone can produce a valid, signed, schema-compliant bundle.

**Why:** This is the most important test. If this passes, the drone produces valid bundles.

**Test:** `tests/integration/test_bundle_e2e.py`

**Pipeline exercised:**
1. Create DroneIdentity
2. Generate fake images + score them with ImageQualityScorer
3. Create ImageMetadata for each (18 columns)
4. Generate manifest.json + images.csv via ManifestGenerator
5. Sign manifest with ManifestSigner
6. Package everything with BundlePackager
7. Validate: schema, signature, checksums, file counts

**Your Audit:**
1. Read the test — follow the data flow from step 1 to 7
2. Run: `pip install -e drone/ros2_ws/src/bennu_core -e drone/ros2_ws/src/bennu_camera -e drone/ros2_ws/src/bennu_dataset -e drone/ros2_ws/src/bennu_mission && python -m pytest tests/integration/test_bundle_e2e.py -v`
3. Understand: this test proves the contract is honored end-to-end

**Accept:**
- [ ] Test exercises every module from Phase 0 and Phase 1
- [ ] Generated bundle validates against contract schema
- [ ] Signature verification passes
- [ ] Test passes

---

**Phase 1 Exit Gate:**
- [ ] Image quality scoring produces blur/exposure flags with 0.0-1.0 score
- [ ] Enhanced geotag produces all 18 CSV columns
- [ ] ManifestGenerator produces contract v1 compliant manifest
- [ ] BundlePackager assembles complete bundle with quality/report.json and checksums
- [ ] E2E test passes: identity → capture → score → manifest → package → sign → validate

---

## Phase 2: Sensor Configuration & Calibration

### Task 12: Sensor Configuration System

**What:** YAML-based sensor config that determines which sensors are active per flight. Configs: survey (RGB+NIR), inspection (RGB+thermal), mapping (RGB only).

**Why:** Different missions need different sensor combinations. Config drives what capture nodes launch and what metadata columns are populated.

**Module:** `bennu_camera/sensor_config.py`
**Configs:** `bennu_bringup/config/sensor_configs/{survey,inspection,mapping}.yaml`
**Test:** `drone/ros2_ws/src/bennu_camera/test/test_sensor_config.py`

**What the code does:**
- `SensorConfig.from_yaml(path)` → loads config
- `.sensors` → list of active sensors (e.g., ["rgb", "nir"])
- `.has_ambient_light` → bool (BH1750 present?)
- `.capture_order` → ordered list for sync timing

**Tests (3):**
```python
def test_load_survey_config()         # survey.yaml → rgb + nir + ambient light
def test_load_mapping_config()        # mapping.yaml → rgb only, no ambient light
def test_unknown_sensor_raises()      # Invalid sensor name → ValueError
```

**Your Audit:**
1. Read each YAML config — verify sensor lists match design doc's Config A/B/C
2. Read `sensor_config.py` — verify it validates sensor names against a known set
3. Run: `python -m pytest drone/ros2_ws/src/bennu_camera/test/test_sensor_config.py -v`

**Accept:**
- [ ] Three configs match design doc sensor configurations
- [ ] Invalid configs are rejected
- [ ] Tests pass

---

### Task 13: Calibration Data Capture

**What:** Ambient light readings (BH1750 sensor) captured alongside images. Writes `calibration.csv` to the bundle when sensor config includes ambient light.

**Why:** Ambient light is needed for radiometric normalization of NIR imagery (Config A).

**Module:** `bennu_camera/calibration.py`
**Test:** `drone/ros2_ws/src/bennu_camera/test/test_calibration.py`

**Your Audit:**
1. Verify calibration.csv format matches design doc
2. Verify it's only generated when `has_ambient_light` is True
3. Run tests

**Accept:**
- [ ] calibration.csv generated only for configs with ambient light
- [ ] Tests pass

---

**Phase 2 Exit Gate:**
- [ ] Sensor configs loadable from YAML
- [ ] Config determines which sensors are active per flight
- [ ] Calibration CSV generated when applicable

---

## Phase 3: Survey Intelligence

### Task 14: Grid Planner

**What:** `GridPlanner` generates survey waypoints from an AOI polygon + desired overlap + altitude + GSD. Core of autonomous mission planning.

**Why:** Without a planner, the user manually creates waypoints in QGroundControl. With a planner, the drone auto-generates optimal coverage patterns.

**Package:** `drone/ros2_ws/src/bennu_survey/`
**Module:** `bennu_survey/grid_planner.py`
**Test:** `drone/ros2_ws/src/bennu_survey/test/test_grid_planner.py`

**What the code does:**
- `GridPlanner(overlap_front, overlap_side, altitude_m, gsd_cm, sensor_params...)` — configures grid
- `.plan(aoi_polygon)` → list of waypoints `[{lat, lon, alt}, ...]`
- Computes line spacing from overlap + footprint
- Uses UTM projection for distance calculations

**Tests (4):**
```python
def test_square_aoi_generates_grid()           # 100×100m → reasonable number of waypoints
def test_higher_overlap_more_waypoints()        # 80% overlap > 60% overlap
def test_rectangular_aoi()                       # Non-square works
def test_empty_polygon_raises()                  # Degenerate input rejected
```

**Your Audit:**
1. Read `grid_planner.py` — verify line spacing calculation:
   - `footprint_m = gsd_cm/100 * image_width_px`
   - `line_spacing = footprint_m * (1 - overlap_side)`
2. Verify UTM projection is used (not naive lat/lon arithmetic)
3. Verify waypoints include correct altitude
4. Run: `python -m pytest drone/ros2_ws/src/bennu_survey/test/ -v`

**Accept:**
- [ ] Line spacing formula is correct for photogrammetric overlap
- [ ] UTM projection used for distance
- [ ] Tests pass

---

### Task 15: Terrain Following

**What:** `adjust_waypoints_for_terrain()` takes planned waypoints and a DEM elevation function, adjusts each waypoint's altitude to maintain constant AGL.

**Why:** Over hilly terrain, flat altitude = variable GSD. Terrain following keeps GSD consistent.

**Module:** `bennu_survey/terrain_follow.py`
**Test:** `drone/ros2_ws/src/bennu_survey/test/test_terrain_follow.py`

**What the code does:**
- `adjust_waypoints_for_terrain(waypoints, target_agl, elevation_fn)` → adjusted waypoints
- Each waypoint's alt = `elevation_fn(lat, lon) + target_agl`

**Tests (2):**
```python
def test_flat_terrain_unchanged()              # All elevations 0 → alt = target_agl
def test_hilly_terrain_adjusts()               # Elevation 100m, 150m → alt 180m, 230m (target_agl=80)
```

**Your Audit:**
1. Read `terrain_follow.py` — verify the altitude formula
2. Verify it works with any `elevation_fn(lat, lon) → float`
3. Run tests

**Accept:**
- [ ] Altitude = ground_elevation + target_agl
- [ ] Tests pass

---

### Task 16: Coverage Tracker (Image Footprint Based)

**What:** `CoverageTracker` tracks which planned grid cells are covered by actual image footprints (not waypoint proximity). Reports coverage percentage and identifies gaps.

**Why:** Distance-triggered capture can miss triggers or change spacing. Footprint-based coverage tells you what's actually photographed, not just where the drone flew.

**Module:** `bennu_mission/coverage_tracker.py`
**Test:** `drone/ros2_ws/src/bennu_mission/test/test_coverage_tracker.py`

**What the code does:**
- `CoverageTracker(grid_cells, cell_size_m)` — initializes with planned grid
- `.record_capture(lat, lon, gsd_cm, image_width_px, image_height_px)` — records an image with its footprint
- `.coverage_pct()` → 0.0-1.0 (cells covered / total cells)
- `.gaps()` → list of uncovered grid cells

**Key insight:** Coverage is computed from image ground footprint = `gsd_cm/100 * image_width_px`. A single image covers all grid cells within its footprint rectangle.

**Tests (4):**
```python
def test_coverage_starts_at_zero()           # No captures → 0%
def test_coverage_from_image_footprint()     # Large footprint covers nearby cells
def test_partial_coverage()                  # Distant cells require separate captures
def test_gaps_reported()                     # Uncovered cells listed
```

**Your Audit:**
1. Read `coverage_tracker.py` — verify footprint calculation uses GSD × image dimensions
2. Verify it uses haversine or UTM for distance (not naive lat/lon comparison)
3. Verify `coverage_pct()` feeds into `quality_summary.coverage_pct` in the manifest
4. Run tests

**Accept:**
- [ ] Coverage is footprint-based, not waypoint-proximity-based
- [ ] Gap detection works
- [ ] Tests pass

---

### Task 17: Repeat Mission

**What:** `RepeatMission` loads a previous mission's waypoints and replays them. Tracks deviation from the planned path for repeatability metrics.

**Why:** Change detection requires flying the exact same grid repeatedly. Deviation tracking quantifies how reproducible the flights are.

**Module:** `bennu_mission/repeat_mission.py`
**Test:** `drone/ros2_ws/src/bennu_mission/test/test_repeat_mission.py`

**Tests (2):**
```python
def test_load_previous_waypoints()           # Loads waypoints from previous mission JSON
def test_deviation_zero_for_exact_match()    # Same positions → deviation < 1m
```

**Your Audit:**
1. Verify it loads waypoints from a standard format (mission JSON)
2. Verify deviation is computed in meters (haversine or UTM)
3. Run tests

**Accept:**
- [ ] Previous mission waypoints loaded correctly
- [ ] Deviation metric makes physical sense (meters)
- [ ] Tests pass

---

### Task 18: Mission Execution Node

**What:** `MissionExecutor` manages flight state machine (idle → armed → takeoff → mission → RTL → land) and waypoint progress. Launch files wire everything for survey and mapping profiles.

**Why:** The planner produces waypoints but nothing executes them. This closes the loop.

**Module:** `bennu_mission/mission_node.py`
**Launch files:** `bennu_bringup/launch/survey.launch.py`, `mapping.launch.py`
**Test:** `drone/ros2_ws/src/bennu_mission/test/test_mission_node.py`

**What the code does:**
- `MissionExecutor(waypoints)` — holds waypoint list
- `.state` → current `MissionState` enum (IDLE, ARMED, TAKEOFF, MISSION, RTL, LANDED)
- `.arm()`, `.takeoff()`, `.advance_waypoint()` — state transitions
- `.progress_pct()` → fraction of waypoints completed
- Full ROS2 node behavior (PX4 topic publishing) tested in SITL, not unit tests

**Tests (3):**
```python
def test_mission_starts_idle()              # Initial state is IDLE
def test_mission_state_transitions()        # arm → ARMED, takeoff → TAKEOFF
def test_waypoint_progress()                # advance_waypoint increments, progress_pct correct
```

**Your Audit:**
1. Read state machine — verify transitions are valid (can't arm if already flying, etc.)
2. Read launch files — verify they include all necessary nodes (camera, DDS agent, mission executor)
3. Run: `python -m pytest drone/ros2_ws/src/bennu_mission/test/test_mission_node.py -v`
4. SITL validation: run full sim stack, verify mission progresses through states

**Accept:**
- [ ] State machine has reasonable transitions
- [ ] Launch files wire camera + DDS + executor
- [ ] Unit tests pass
- [ ] SITL smoke test works (deferred to integration phase)

---

**Phase 3 Exit Gate:**
- [ ] Grid planner generates waypoints from AOI polygon
- [ ] Terrain following adjusts altitudes from DEM
- [ ] Coverage tracker uses image footprints (not waypoint proximity)
- [ ] Mission executor manages flight state machine
- [ ] Launch files exist for survey and mapping profiles
- [ ] Repeat mission loads previous waypoints with deviation tracking

---

## Phase Summary

| Phase | Tasks | Key Deliverable |
|---|---|---|
| Pre-flight | Bugs 1-8 | Safety and correctness fixes |
| 0: Foundation | 1-6 | Contract schema, CI, governance, identity, signing |
| 1: Data Quality | 7-11 | Quality scoring, geotagging, manifest, packager, e2e test |
| 2: Sensor Config | 12-13 | Sensor configs, calibration data |
| 3: Survey Intelligence | 14-18 | Grid planner, terrain following, coverage, mission execution, repeat |

**After all tasks, the drone can:**
1. Plan a survey grid for any polygon AOI
2. Adjust altitudes for terrain
3. Execute a planned mission (upload waypoints, fly, trigger captures)
4. Capture images with quality scoring (blur, exposure)
5. Generate full metadata (18 columns including RTK, GSD, capture_offset_ms)
6. Package a signed, schema-validated mission bundle
7. Track coverage via image footprints and identify gaps
8. Repeat missions for change detection
