# Bennu

[![CI](https://github.com/fadi-labib/bennu/actions/workflows/ci.yml/badge.svg)](https://github.com/fadi-labib/bennu/actions/workflows/ci.yml)
[![SIL](https://github.com/fadi-labib/bennu/actions/workflows/sil-smoke.yml/badge.svg)](https://github.com/fadi-labib/bennu/actions/workflows/sil-smoke.yml)
[![Docker](https://github.com/fadi-labib/bennu/actions/workflows/docker-images.yml/badge.svg)](https://github.com/fadi-labib/bennu/actions/workflows/docker-images.yml)
[![codecov](https://codecov.io/gh/fadi-labib/bennu/graph/badge.svg)](https://codecov.io/gh/fadi-labib/bennu)
[![Docs](https://img.shields.io/badge/docs-live-brightgreen)](https://fadi-labib.github.io/bennu/)
[![License](https://img.shields.io/github/license/fadi-labib/bennu)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/)
[![ROS2](https://img.shields.io/badge/ROS2-Jazzy-blue)](https://docs.ros.org/en/jazzy/)
[![PX4](https://img.shields.io/badge/PX4-v1.16-blue)](https://docs.px4.io/)

DIY 7" photogrammetry drone built with PX4, ROS2, and OpenDroneMap.

Bennu produces versioned, signed, schema-validated mission bundles from autonomous survey flights. The bundles feed an independent geospatial analysis platform via a contract-first data interface.

## Hardware

| Component | Part |
|-----------|------|
| Frame | [TBS Source One V5 7" Deadcat](https://github.com/tbs-trappy/source_one) + custom 3D-printed adapters |
| Flight Controller | Holybro Pixhawk 6C (PX4 v1.16) |
| Companion Computer | Raspberry Pi 4 (4GB), Ubuntu 24.04, ROS2 Jazzy |
| Camera | Raspberry Pi HQ Camera (IMX477) + 6mm CS-mount lens |
| GPS | Holybro M9N (u-blox M9N) |
| ESC | Holybro Tekko32 F4 4-in-1 50A |
| Motors | T-Motor Velox V2207.5 1950KV x4 |
| Battery | 4S 2200-3000mAh LiPo |
| Target AUW | <830g |

## Architecture

```
Ground Station                    Drone (onboard Pi 4)
+--------------+                  +------------------+
| QGroundControl|<--- MAVLink --->| Pixhawk 6C (PX4) |
+--------------+                  +--------+---------+
                                           |
| WebODM       |<--- bundle --->  +--------+---------+
+--------------+    transfer      | ROS2 Jazzy       |
                                  |  bennu_camera     |
                                  |  bennu_mission    |
                                  |  bennu_survey     |
                                  |  bennu_dataset    |
                                  +------------------+
```

The drone captures geotagged images during autonomous survey flights, scores image quality onboard, packages everything into a signed mission bundle, and exports it for processing in WebODM or a geospatial platform.

## Quick Start

```bash
# Clone
git clone https://github.com/fadi-labib/bennu.git
cd bennu

# Install dev dependencies (Python 3.12)
pip install -r requirements-dev.txt
pip install -e drone/ros2_ws/src/bennu_camera \
            -e drone/ros2_ws/src/bennu_core \
            -e drone/ros2_ws/src/bennu_dataset \
            -e drone/ros2_ws/src/bennu_mission \
            -e drone/ros2_ws/src/bennu_survey

# Run tests
python -m pytest drone/ros2_ws/src/*/test/ tests/ -v

# Lint
ruff check .

# Start simulation (requires Docker)
cd sim && make dev
```

## ROS2 Packages

| Package | Description |
|---------|-------------|
| `bennu_camera` | Camera capture, image quality scoring, geotagging (18-column metadata), sensor config |
| `bennu_core` | Drone identity and hardware manifest |
| `bennu_dataset` | Mission bundle packaging, Ed25519 signing, checksums |
| `bennu_mission` | Mission manifest generation (contract v1 compliant) |
| `bennu_survey` | Survey grid planner (lawnmower pattern, UTM projection) |
| `bennu_bringup` | Launch files and sensor configuration profiles |

## Mission Bundle Contract

The drone produces a versioned mission bundle — the only coupling point with downstream platforms:

```
{mission_id}/
├── contract_version       # "v1"
├── manifest.json          # Mission metadata (signed)
├── images/                # Geotagged survey images
├── metadata/images.csv    # 18-column per-image metadata
├── quality/report.json    # Image quality scores
└── checksums.sha256       # SHA-256 integrity chain
```

The manifest is canonicalized, signed with Ed25519, and validated against a JSON schema in CI.

## Simulation

Bennu uses a Docker-based PX4 SITL + Gazebo Harmonic simulation stack:

```bash
cd sim
make dev          # Start headless sim (PX4 + ROS2)
make dev-debug    # Start with Gazebo GUI (requires GPU + X11)
make test-unit    # Run unit tests in container
make test-sitl    # Run SIL mission smoke test
make clean        # Stop and remove containers
```

## Documentation

Full documentation is at [fadi-labib.github.io/bennu](https://fadi-labib.github.io/bennu/), including:

- [Build Guide & Parts Checklist](https://fadi-labib.github.io/bennu/build-guide/00-parts-checklist/)
- [Bill of Materials](https://fadi-labib.github.io/bennu/reference/bill-of-materials/)
- [Wiring Diagram](https://fadi-labib.github.io/bennu/reference/wiring-diagram/)
- [Power Architecture](https://fadi-labib.github.io/bennu/reference/power-architecture/)
- [Frame Specifications](https://fadi-labib.github.io/bennu/reference/frame-specifications/)
- [Architecture Decision Records](https://fadi-labib.github.io/bennu/decisions/)

## License

Apache-2.0 — see [LICENSE](LICENSE).
