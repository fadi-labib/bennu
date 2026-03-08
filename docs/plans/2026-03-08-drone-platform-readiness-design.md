# Drone Platform-Readiness Design

**Date:** 2026-03-08
**Status:** Proposed

## Goal

Evolve Bennu from a photogrammetry prototype into a production-grade data
acquisition system that can feed an independent geospatial analysis platform.
The platform is a separate, proprietary product built on OSS. Bennu is the
open-source reference drone.

## Strategic Context

### Competitive Landscape

DJI dominates the commercial drone survey market with tight vertical integration
(Mavic 3M → SmartFarm → AGRAS sprayers). Key specs for the Mavic 3M benchmark:

- 20MP RGB + 4× 5MP multispectral (Green, Red, Red Edge, NIR)
- Built-in RTK (1cm + 1ppm horizontal)
- 43 min flight time, 200 ha/flight
- Incident light sensor for radiometric calibration
- Terrain following
- ~$6,000-8,000

DJI SmartFarm provides NDVI mapping, AI crop health, variable-rate prescription
maps, and yield estimation — all locked to DJI hardware, agriculture-only,
cloud-hosted.

### Where We Compete

We do not compete on hardware specs. We compete on:

1. **Vendor neutrality** — platform works with any drone that produces conformant bundles.
2. **Domain breadth** — infrastructure, construction, environmental, forestry — not just ag.
3. **Data sovereignty** — self-hosted, air-gapped capable.
4. **Custom ML** — bring your own models (TorchGeo, TerraTorch, SAM).
5. **Cost** — ~$900-1,100 drone vs $6-8K, free OSS vs platform fees.
6. **Transparency** — open algorithms, reproducible analysis, auditable pipelines.

DJI is banned or restricted by government agencies in several countries. An open,
self-hosted alternative has genuine demand for government, military, infrastructure,
and critical asset inspection.

## System Boundaries

### Bennu (this repo) — Data Acquisition

Owns: flight stack, onboard capture, sensor integration, mission execution,
quality checks, dataset packaging, mission bundle export (offline-first).

Does not own: platform backend, catalog/database, dashboards, user management,
ML training, analytics.

### Platform (separate repo) — Analysis & Decision

Owns: ingestion, object storage, STAC catalog, PostGIS, APIs, workflow
orchestration, ML inference, map UI, alerting, auth/RBAC/audit, SLO operations.

### Coupling Point: Mission Bundle Contract

The ONLY integration point is a versioned mission bundle (see Data Contract below).
Either side can change internals without breaking the other, as long as the
contract is honored.

## Data Contract

The mission bundle is the mandatory first deliverable. Schema authority lives in
the platform repo. The drone repo imports the schema version and runs conformance
tests in CI.

### Bundle Structure

```
{mission_id}/
├── contract_version          # "v1"
├── manifest.json             # Mission-level metadata (signed)
├── images/
│   ├── 0001_rgb.jpg
│   ├── 0001_nir.jpg          # (if multispectral config)
│   ├── 0001_thermal.tiff     # (if thermal config)
│   └── ...
├── metadata/
│   ├── images.csv            # Per-image metadata table
│   └── calibration.csv       # Ambient light / panel readings (if applicable)
├── telemetry/
│   └── flight.ulg            # PX4 flight log
├── quality/
│   └── report.json           # Per-image quality scores + summary
└── checksums.sha256           # SHA-256 of all files
```

### manifest.json (Mission-Level)

```json
{
  "contract_version": "v1",
  "mission_id": "2026-03-15-site-alpha-003",
  "drone_id": "bennu-001",
  "drone_hardware": {
    "flight_controller": "Pixhawk6C",
    "px4_version": "1.16.1",
    "gps_model": "F9P",
    "sensors": ["rgb:IMX477", "nir:IMX708_NoIR"]
  },
  "capture": {
    "start_time": "2026-03-15T10:32:00Z",
    "end_time": "2026-03-15T10:47:00Z",
    "image_count": 120,
    "sensor_config": "survey",
    "trigger_mode": "distance",
    "trigger_distance_m": 5.0
  },
  "survey": {
    "site_id": "site-alpha",
    "aoi_geojson": "...",
    "planned_altitude_m": 80,
    "planned_overlap_front": 0.75,
    "planned_overlap_side": 0.65,
    "planned_gsd_cm": 2.1
  },
  "quality_summary": {
    "images_total": 120,
    "images_passed": 117,
    "images_failed": 3,
    "failure_reasons": {"blur": 2, "exposure": 1},
    "rtk_fixed_pct": 0.95,
    "coverage_pct": 0.98
  },
  "checksums_digest": "sha256-of-checksums.sha256-file",
  "signature": "base64-encoded-ed25519-signature"
}
```

**Required vs optional fields:**
- Required: `contract_version`, `mission_id`, `drone_id`, `drone_hardware`, `capture`,
  `quality_summary` (with `coverage_pct` nullable), `checksums_digest`, `signature`
- Optional: `survey` (omitted for manual flights, test flights, non-grid missions)

### images.csv (Per-Image)

| Column | Type | Description |
|---|---|---|
| sequence | int | Capture sequence number |
| filename | string | Image filename |
| sensor | string | rgb, nir, thermal |
| timestamp_utc | ISO8601 | Capture time (PX4 trigger clock) |
| lat | float | WGS84 latitude |
| lon | float | WGS84 longitude |
| alt_msl | float | Altitude above mean sea level (m) |
| alt_agl | float | Altitude above ground level (m), estimated |
| heading_deg | float | Camera heading (0-360) |
| pitch_deg | float | Camera pitch |
| roll_deg | float | Camera roll |
| rtk_fix_type | string | RTK_FIXED, RTK_FLOAT, DGPS, AUTONOMOUS |
| position_accuracy_m | float | Estimated horizontal accuracy |
| gsd_cm | float | Calculated ground sample distance |
| quality_score | float | 0.0-1.0 composite quality score |
| quality_flags | string | Comma-separated: ok, blur, overexposed, underexposed |
| ambient_light_lux | float | BH1750 reading (if sensor present), nullable |
| capture_offset_ms | float | Offset from trigger timestamp for this sensor (multi-sensor sync), nullable |

### Contract Rules

- Semantic versioning (v1, v1.1, v2)
- Strict JSON Schema validation in CI for `manifest.json` (both repos)
- CSV validation: column names, types, and row count checked via schema definition
  in `contract/v1/images.schema.json` (defines columns, types, constraints)
- Minor versions add optional fields only (backward compatible)
- Major versions may remove or change fields (migration notes required)
- Schema authority: contract schema lives in a shared artifact (git submodule or
  versioned release). The drone repo pins a contract version tag and runs
  conformance tests. The platform repo is the schema author.

## Drone Hardware Architecture

### Core Platform (Always Present)

| Component | Current | Upgraded | Role |
|---|---|---|---|
| Companion computer | Pi 5 (8GB) | Same | ROS2, sensor management, packaging |
| Flight controller | Pixhawk 6C | Same | PX4, stabilization, nav, triggers |
| GPS | Holybro M9N | Holybro H-RTK F9P | Positioning (1.5m → conditional cm) |
| Barometer | Pixhawk built-in | Same | Altitude reference |
| Camera (RGB) | Pi HQ Camera IMX477 | Same | 12.3MP primary capture |

### Sensor Configurations

Each configuration is a physical mount + ROS2 driver. The drone carries one
config per flight.

**Config A: Survey (RGB + Proxy NIR)**

| Sensor | Part | Cost | Weight |
|---|---|---|---|
| RGB camera | Pi HQ Camera (IMX477) | existing | existing |
| NIR camera | Pi Camera Module 3 NoIR | ~$35 | ~5g |
| Blue filter | Roscolux #2007 on NoIR lens | ~$5 | <1g |
| Ambient light | BH1750 (I2C) | ~$3 | ~2g |

Produces: RGB images + broadband NIR images + ambient light readings.
Capability: **Proxy NDVI only (trend/change detection)**. Not science-grade.

Limitations (documented, not hidden):
- NoIR gives one broad NIR band (~700-1000nm), not narrow-band like Mavic 3M.
- BH1750 measures photopic lux, not spectral irradiance. Cannot normalize
  reflectance per band. Useful only as a relative brightness reference
  across captures within a single flight.
- Proxy NDVI answers "is this area greener than last week?" not "what is the
  absolute chlorophyll content?"
- For science-grade multispectral: requires dedicated camera (Micasense RedEdge,
  ~$2,000, ~150g, needs frame upgrade).

**Config B: Inspection (RGB + Thermal)**

| Sensor | Part | Cost | Weight |
|---|---|---|---|
| RGB camera | Pi HQ Camera (IMX477) | existing | existing |
| Thermal camera | FLIR Lepton 3.5 (160×120) | ~$200 | ~5g (module) |
| Breakout board | PureThermal 3 (USB) | ~$50 | ~10g |

Produces: RGB images + radiometric thermal images (TIFF).
Capability: Hotspot detection, thermal anomaly mapping, temperature measurement.
Use cases: Solar panel inspection, building envelope, infrastructure, SAR.

**Config C: Mapping (RGB High-Overlap)**

| Sensor | Part | Cost | Weight |
|---|---|---|---|
| RGB camera | Pi HQ Camera (IMX477) | existing | existing |

Produces: High-overlap RGB images for photogrammetry.
Capability: 3D reconstruction, orthomosaic, volumetric measurement.
Use cases: Construction progress, terrain mapping, stockpile measurement.

### Terrain Following

DEM-based terrain following is the v1 approach (pure software, no extra hardware):

- Pre-load a DEM (SRTM 30m, or local DTM if available) for the survey area.
- `terrain_follow.py` adjusts planned waypoint altitudes based on DEM elevation
  under each waypoint.
- Accuracy: ±5-30m depending on DEM source (SRTM) or ±1-2m (local survey DTM).
- GSD variation within a flight is bounded by DEM accuracy.

For real-time AGL at mapping altitude (50-120m), the appropriate sensor is a
Lightware SF11/C laser altimeter (~$300, ~35g, 120m range). This is an optional
upgrade, not a v1 requirement.

VL53L1X (4m max range) is NOT suitable for outdoor AGL at mapping altitudes.

### Accuracy Budget

RTK GPS accuracy depends on conditions. Honest claims:

| Condition | Horizontal Accuracy | Notes |
|---|---|---|
| RTK Fixed, slow flight (2 m/s), lever-arm calibrated | 5-10 cm | Best case |
| RTK Fixed, survey speed (5 m/s), no lever-arm cal | 15-30 cm | Typical survey |
| RTK Float | 30-100 cm | Degraded correction |
| DGPS / SBAS | 50-150 cm | No RTK base |
| Autonomous GPS (current M9N) | 150-300 cm | Current Bennu |

Additional error sources for image geotagging:
- Trigger latency: ~10-50ms (Pi 5 libcamera-still) → 5-25cm at 5 m/s
- Rolling shutter: top-to-bottom exposure sweep adds position smear
- Lever-arm offset: GPS antenna to camera lens, must be measured and documented
- No mid-exposure position interpolation in v1

Every image is tagged with `rtk_fix_type` and `position_accuracy_m` so the
platform knows the confidence level. "Survey-grade" is never claimed without
qualifying conditions.

### Multi-Sensor Synchronization

Pi 5 has two CSI ports but no hardware-synchronized trigger. Software-triggered
dual capture has 10-50ms latency between cameras. At 5 m/s, that is 5-25cm
spatial misalignment between RGB and NIR.

v1 strategy:
- PX4 `camera_trigger` timestamp is authoritative capture time.
- Both cameras are triggered in sequence; offset is recorded per capture pair.
- Platform handles band alignment in post-processing using position + offset.
- Hardware trigger sync (GPIO from Pixhawk → CSI trigger pins) is a future
  hardware revision.

## Drone Software Architecture

### ROS2 Packages

```
drone/ros2_ws/src/
├── bennu_core/                    # Drone identity + health monitoring
│   ├── drone_identity.py          # Drone ID, hardware manifest, key management
│   └── health_monitor.py          # Battery, GPS quality, sensor health
│
├── bennu_camera/                  # Capture + quality (enhanced existing)
│   ├── camera_node.py             # RGB capture (existing, enhanced with attitude)
│   ├── nir_node.py                # NIR camera capture (Config A) [deferred: needs hardware]
│   ├── thermal_node.py            # FLIR Lepton driver (Config B) [deferred: needs hardware]
│   ├── sync_manager.py            # Multi-sensor trigger coordination [deferred: needs hardware]
│   ├── calibration.py             # Light sensor + panel capture
│   ├── quality.py                 # Blur, exposure, histogram scoring
│   └── geotag.py                  # Enhanced: attitude, RTK fix, GSD, accuracy
│
├── bennu_survey/                  # Mission planning
│   ├── grid_planner.py            # Survey grid from polygon + overlap + GSD
│   ├── corridor_planner.py        # Linear path (powerlines, roads)
│   ├── orbit_planner.py           # Point-of-interest orbit (structures)
│   ├── terrain_follow.py          # DEM-based altitude adjustment
│   └── config/sites/              # GeoJSON site definitions
│
├── bennu_mission/                 # Mission execution + packaging
│   ├── mission_node.py            # Waypoint execution via uXRCE-DDS
│   ├── repeat_mission.py          # Re-fly same grid for change detection
│   ├── coverage_tracker.py        # Image-footprint-based coverage, find gaps
│   └── mission_manifest.py        # Generate manifest.json + images.csv
│
├── bennu_dataset/                 # Bundle packaging + export
│   ├── packager.py                # Assemble mission bundle structure
│   ├── signer.py                  # Ed25519 manifest signing
│   ├── flight_log.py              # Extract PX4 .ulg flight log
│   └── transfer.py                # Export: local, rsync, HTTP upload
│
└── bennu_bringup/                 # Launch configurations
    ├── launch/
    │   ├── drone.launch.py        # Existing basic launch
    │   ├── survey.launch.py       # Grid survey mission
    │   ├── inspection.launch.py   # Thermal inspection mission
    │   └── mapping.launch.py      # High-overlap 3D mapping
    └── config/
        ├── camera_params.yaml     # Existing
        ├── survey_params.yaml     # Grid overlap, GSD, altitude
        └── sensor_configs/
            ├── survey.yaml        # Config A: RGB + NIR + light
            ├── inspection.yaml    # Config B: RGB + thermal
            └── mapping.yaml       # Config C: RGB high-res only
```

### Capture Pipeline (Per Trigger Event)

**v1 (RGB only — Config C / single-sensor):**

```
PX4 camera trigger (distance-based)
    │
    ▼
camera_node receives trigger timestamp
    │
    ▼
camera_node captures RGB image
    │
    ▼
quality.py scores image
    │  - Laplacian variance (blur detection)
    │  - Histogram analysis (exposure check)
    │  - Composite 0.0-1.0 score
    │
    ▼
geotag.py writes extended metadata
    │  - Position: lat, lon, alt (from VehicleGlobalPosition)
    │  - Attitude: heading, pitch, roll (from VehicleAttitude)
    │  - RTK fix type + estimated accuracy
    │  - GSD (calculated from altitude + lens + sensor)
    │  - Sequence number, mission ID, drone ID
    │  - Capture timestamp (PX4 trigger clock)
    │  - Quality score + flags
    │
    ▼
coverage_tracker updates progress
    │  - Mark grid cell as covered (image footprint)
    │  - Flag if quality below threshold
    │
    ▼
Image saved: {mission_id}/images/{sequence:04d}_rgb.jpg
```

**Future multi-sensor (deferred: needs hardware):**

When NIR (Config A) or thermal (Config B) sensors are added, `sync_manager.py`
will coordinate multi-camera trigger sequencing. Each additional sensor captures
with a recorded `capture_offset_ms` from the trigger timestamp. The v1 pipeline
above remains the core path; multi-sensor adds parallel capture branches after
the trigger event.

### Mission End Pipeline

```
Mission complete (all waypoints visited or RTL triggered)
    │
    ▼
coverage_tracker generates coverage report
    │
    ▼
mission_manifest generates manifest.json + images.csv
    │  - Aggregates per-image metadata
    │  - Computes quality summary
    │  - Includes drone hardware manifest
    │
    ▼
flight_log extracts PX4 .ulg file
    │
    ▼
packager assembles bundle directory structure
    │
    ▼
checksums.sha256 computed for all files
    │
    ▼
signer signs manifest.json with drone's Ed25519 private key
    │
    ▼
Bundle ready for export (local storage, rsync, or HTTP upload)
```

## Security Model

### Signed Manifests (Not "Immutable Audit Trail")

- Each drone has an Ed25519 keypair provisioned during setup.
- Private key stored on Pi 5 (`/etc/bennu/keys/drone.key`).
- Public key registered with the platform.

**Signing order (integrity chain):**

1. Compute SHA-256 of every file in the bundle → write `checksums.sha256`
2. Compute SHA-256 of `checksums.sha256` → set `checksums_digest` in manifest
3. Serialize manifest to canonical JSON (sorted keys, no whitespace: `json.dumps(m, sort_keys=True, separators=(',', ':'))`)
4. Sign the canonical JSON bytes with Ed25519 → set `signature` in manifest
5. Write final `manifest.json` (includes `checksums_digest` and `signature`)

This creates a Merkle-like chain: signature covers manifest, manifest covers
checksums file, checksums file covers all content files.

**Canonical serialization:** The signing format is JSON with sorted keys and
compact separators (`json.dumps(obj, sort_keys=True, separators=(',', ':'))`).
This is deterministic across Python implementations. For cross-language
verification, the platform must use equivalent sorted-key compact JSON. The
`signature` field is excluded from the signed payload (sign the manifest dict
without the `signature` key, then add it).

- Platform verifies signature on ingest. Reject unsigned or tampered bundles.

This establishes: "this dataset was produced by drone bennu-001 and has not been
modified since capture." Full chain of custody (append-only storage, access logs)
is the platform's responsibility.

### Telemetry Security (Deferred to Phase 5)

When LTE/MQTT telemetry is added:
- mTLS for drone-to-platform authentication.
- Telemetry is read-only status data (position, battery, progress). No command
  path from platform to drone.
- Offline queue on Pi 5 for connectivity gaps.
- Threat model: information disclosure only (drone position). No actuator control.

## Testing Strategy

Tests are structured in two tiers:

1. **Package tests** (pytest): Pure Python tests inside each package's `test/`
   directory. CI installs packages with `pip install -e` and runs pytest across
   all `<package>/test/` directories. In a ROS2 environment, `colcon test` also
   discovers and runs these tests.
2. **Contract tests** (top-level `tests/`): Schema validation and integration tests
   that span multiple packages. These use `pip install -e` for package imports,
   not raw PYTHONPATH hacks.

| Test Type | Scope | Tooling | Location | When |
|---|---|---|---|---|
| Unit | Geotag math, quality scoring, signer | pytest | `<package>/test/` | CI on every PR |
| Schema conformance | manifest.json + images.csv validate against contract schema | jsonschema + pytest | `tests/contract/` | CI on every PR |
| Bundle integration | End-to-end bundle generation + validation | pytest | `tests/integration/` | CI on every PR |
| SITL integration | Full capture pipeline in Gazebo sim | Docker Compose sim stack | `tests/sitl/` | CI (nightly or per-PR) |
| HIL (hardware-in-loop) | Real sensors on bench, no flight | Manual | — | Per-phase gate |
| Flight test | Actual flight, validate bundle end-to-end | Manual | — | Per-phase gate |

Pass/fail thresholds:
- Unit: 100% pass
- Schema conformance: 100% pass (contract violations block merge)
- SITL: Bundle generated with all required fields populated
- HIL: All sensors produce expected data format
- Flight: ≥99% images with complete metadata, coverage ≥95% of planned grid

## Risks and Mitigations

1. **Over-optimistic sensor assumptions** — Validate each sensor in controlled
   bench tests before committing to architecture. Document capabilities honestly
   with measured tolerances, not datasheet specs.

2. **Scope creep across drone and platform** — Enforce repo boundaries. The bundle
   contract is the only coupling point. No direct API calls between repos.

3. **Version drift** — Pinned dependencies, compatibility matrix
   (PX4/ROS2/px4_msgs/XRCE), release notes for every version.

4. **Production claims without ops maturity** — SLOs, runbooks, backups, and CI
   gates required before any "production" label.

5. **Multi-sensor sync quality** — Document sync latency per configuration.
   Platform must handle band alignment in post-processing.

6. **RTK availability** — RTK Fixed is not guaranteed (base station distance,
   sky view, multipath). Every image carries fix type — platform degrades
   gracefully for non-RTK images.

## Success Metrics

- Bundle reliability: ≥99% successful bundle generation from completed missions
- Metadata completeness: ≥99% required fields present
- Mission repeatability: overlap/GSD variance within ±10% of planned profile
- Schema conformance: 100% of bundles pass platform schema validator
- Integration reliability: ≥99% successful ingest from valid bundles
