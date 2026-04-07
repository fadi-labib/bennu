# ADR-007: Platform Readiness — Phases 0–2

## Status

Accepted (implemented 2026-03-08 through 2026-03-17)

## Context

Bennu began as a photogrammetry prototype with basic camera capture and EXIF geotagging. To feed an independent geospatial analysis platform, the drone needed to produce versioned, signed, schema-validated mission bundles — not just a folder of geotagged JPEGs.

The platform's only coupling point with Bennu is the mission bundle contract. Everything downstream (ingestion, STAC catalog, ML inference) depends on bundles conforming to that contract.

## Decision

Implement platform readiness in three phases, each gated by passing tests.

### Phase 0: Foundation & Governance

- **Contract schema** (`contract/v1/`): JSON Schema defining `manifest.json` structure and `images.csv` 18-column spec. The schema is the single source of truth for what constitutes a valid bundle.
- **DroneIdentity** (`bennu_core`): Dataclass encoding hardware config (flight controller, PX4 version, GPS, sensors). Every manifest references this.
- **Ed25519 signing** (`bennu_dataset/signer.py`): Manifest is canonicalized (deterministic JSON), signed with PyNaCl. Platform rejects unsigned bundles.
- **CI pipeline** (`.github/workflows/ci.yml`): ruff + pytest on every PR. Python 3.12 on Ubuntu 24.04.
- **License**: Apache-2.0 across all packages.

### Phase 1: Data Quality Baseline

- **Image quality scoring** (`bennu_camera/quality.py`): Laplacian variance for blur, histogram analysis for exposure. Produces 0.0–1.0 score with categorical flags.
- **18-column ImageMetadata** (`bennu_camera/geotag.py`): Full per-image metadata including RTK fix type, GSD, quality score, ambient light. Replaces the original basic lat/lon/alt geotag.
- **Mission manifest generator** (`bennu_mission/mission_manifest.py`): Aggregates identity + images + quality into a contract-v1-compliant `manifest.json` and `images.csv`.
- **Bundle packager** (`bennu_dataset/packager.py`): Assembles the physical directory structure, computes SHA-256 checksums for integrity chain.
- **E2E integration test** (`tests/integration/test_bundle_e2e.py`): Full pipeline from identity → capture → score → manifest → package → sign → validate.

### Phase 2: Sensor Configuration & Calibration

- **YAML sensor configs** (`bennu_camera/sensor_config.py`): Three profiles — survey (RGB+NIR+ambient), inspection (RGB+thermal), mapping (RGB only). Config drives which capture nodes launch.
- **Calibration data** (`bennu_camera/calibration.py`): BH1750 ambient light readings captured alongside images when sensor config includes ambient light sensor. Written as `calibration.csv` in the bundle.

## Consequences

- Any drone (not just Bennu) can produce valid bundles if it honors the contract schema.
- The integrity chain (checksums → manifest → signature) provides tamper-evidence without requiring network connectivity during flight.
- Quality scoring happens onboard in real-time, enabling future abort-on-quality-degradation.
- Sensor configs make the system extensible to new sensor combinations without code changes.
- The E2E test is the project's most important regression gate — if it passes, the drone produces valid bundles.

## Related

- Design doc: `docs/plans/2026-03-08-drone-platform-readiness-design.md`
- Phase 3 (Survey Intelligence): in progress — grid planner, terrain following, coverage analysis
