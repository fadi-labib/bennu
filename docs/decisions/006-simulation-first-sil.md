# ADR-006: Simulation-First SIL Infrastructure

## Status

Accepted (implemented 2026-03-17)

## Context

Bennu's PX4 SITL stack was a manual developer workflow, not a merge gate. QGroundControl was required for mission testing. The camera node detected simulation implicitly via `FileNotFoundError` on `libcamera-still`. No CI job ran simulation. No automated mission runner existed.

We needed to make simulation the default development interface: every meaningful change tested locally and in CI before hardware.

## Decision

Implement a layered simulation infrastructure with these architectural choices:

### Docker Compose split (3 profiles)

- **dev** — interactive development with `pytest-watch`, headless PX4 + Gazebo
- **sil** — headless CI-only, prebuilt GHCR images, exit-code-from test-runner
- **debug** — GPU-enabled with Gazebo GUI and X11 forwarding

### Makefile developer interface

All sim commands go through `sim/Makefile`: `make dev`, `make test-unit`, `make test-sitl`, `make clean`. Developers never type docker compose flags directly.

### Explicit camera backends

Replaced implicit `FileNotFoundError` detection with parameter-driven backends:
- `camera_backend=libcamera` (default, real hardware)
- `camera_backend=placeholder` (simulation, generates minimal valid JPEG)

Selection via ROS2 `camera_backend` parameter in launch files.

### MAVSDK mission automation

- `wait_for_px4.py` — polls PX4 via MAVSDK until GPS fix + home position, with `asyncio.wait_for` timeout
- `run_mission.py` — loads scenario YAML, generates lawnmower grid waypoints around home position, uploads mission plan via MAVSDK, arms + flies + monitors + lands
- `validate_artifacts.py` — checks captured images against scenario assertions (count, JPEG validity)

### Scenario-driven testing

Scenario YAML files define mission parameters (altitude, speed, waypoints, trigger distance) and assertions (min triggers, expected end state, max duration). Currently one scenario: `nominal_survey.yaml`.

### CI gates

- **ci.yml** — ruff lint + pytest on every PR (< 1 min)
- **sil-smoke.yml** — full PX4 SITL mission run on every PR (< 15 min)
- **docker-images.yml** — build + push to GHCR on Dockerfile changes and weekly

### pytest-watch dev loop

`make dev-watch` auto-reruns tests on file changes inside the Docker container. Host volume mounts propagate edits instantly.

## Consequences

- Simulation is the primary merge gate, not a side path
- QGroundControl is no longer needed for standard testing
- Camera simulation is explicit and parameter-driven
- Every PR runs lint + unit tests + SIL smoke test
- Failed CI runs upload debugging artifacts
- GHCR prebuilt images keep CI fast (~30s pull vs ~10 min build)
- Test pyramid: unit (Tier 0) → component (Tier 1) → SIL mission (Tier 2) → scenario matrix (Tier 3)

## Files

- `sim/docker-compose.{dev,sil,debug}.yml` — compose profiles
- `sim/Makefile` — developer interface
- `sim/Dockerfile.{px4,ros2}` — container images
- `sim/scripts/{wait_for_px4,run_mission,validate_artifacts,run_scenarios}.py` — automation
- `sim/scenarios/nominal_survey.yaml` — baseline scenario
- `.github/workflows/{ci,sil-smoke,docker-images}.yml` — CI gates
- `drone/ros2_ws/src/bennu_camera/bennu_camera/{capture_backend,backends/}.py` — camera backends
- `pytest.ini` — test discovery config

## Design Reference

See `docs/plans/2026-03-08-simulation-first-sil-design.md` for the full architecture design.
