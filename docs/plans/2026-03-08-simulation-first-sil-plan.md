# Simulation-First SIL — Owner Walkthrough

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform the existing PX4 SITL stack into a simulation-first development environment with automated testing, explicit camera backends, MAVSDK mission automation, and CI gates.

**Architecture:** Layered Docker Compose (dev, sil, debug profiles), Makefile interface, 5-tier test pyramid. Camera node refactored around explicit backends. MAVSDK replaces QGroundControl for automated testing. Prebuilt images on GHCR for CI speed.

**Tech Stack:** Docker Compose, PX4 SITL v1.16.1, Gazebo Harmonic, ROS2 Jazzy, MAVSDK-Python, pytest, pytest-watch, GitHub Actions

**Design Doc:** `docs/plans/2026-03-08-simulation-first-sil-design.md`

---

## Phase 0: Infrastructure

### Task 1: Split Docker Compose Files

**What:** Replace the single `docker-compose.sim.yml` with three compose files for different use cases: interactive dev, headless SIL testing, and GUI debugging.

**Why:** The current single compose file mixes interactive dev, testing, and GPU rendering concerns. Splitting them lets CI run headless without GPU, devs get pytest-watch, and debug sessions get Gazebo GUI.

**Files:**
- Create: `sim/docker-compose.dev.yml`
- Create: `sim/docker-compose.sil.yml`
- Create: `sim/docker-compose.debug.yml`
- Delete: `sim/docker-compose.sim.yml`
- Modify: `.devcontainer/devcontainer.json` (point to `docker-compose.dev.yml`)
- Modify: `sim/README.md`

**docker-compose.dev.yml** (interactive development + pytest-watch):
```yaml
# Bennu Dev Environment
# Usage: make dev or make dev-watch
services:
  px4-sitl:
    build:
      context: ..
      dockerfile: sim/Dockerfile.px4
    container_name: bennu-px4-sitl
    environment:
      - PX4_SYS_AUTOSTART=4001
      - PX4_GZ_MODEL=x500
      - HEADLESS=1
    ports:
      - "14540:14540/udp"
      - "14580:14580/udp"
    networks:
      - bennu-sim

  ros2-dev:
    build:
      context: ..
      dockerfile: sim/Dockerfile.ros2
    container_name: bennu-ros2-dev
    volumes:
      - ../drone/ros2_ws/src:/ros2_ws/src/bennu:rw
      - ../tests:/ros2_ws/tests:rw
      - ../contract:/ros2_ws/contract:rw
    depends_on:
      - px4-sitl
    networks:
      - bennu-sim
    stdin_open: true
    tty: true

networks:
  bennu-sim:
    driver: bridge
```

**docker-compose.sil.yml** (headless CI + smoke tests):
```yaml
# Bennu SIL Testing — Headless, no GPU
# Usage: make test-sitl
services:
  px4-sitl:
    image: ghcr.io/fadi-labib/bennu/px4-sitl:v1.16.1
    build:
      context: ..
      dockerfile: sim/Dockerfile.px4
    container_name: bennu-px4-sitl
    environment:
      - PX4_SYS_AUTOSTART=4001
      - PX4_GZ_MODEL=x500
      - HEADLESS=1
      - PX4_GZ_STANDALONE=1
    ports:
      - "14540:14540/udp"
    networks:
      - bennu-sim

  test-runner:
    build:
      context: ..
      dockerfile: sim/Dockerfile.ros2
    container_name: bennu-test-runner
    volumes:
      - ../drone/ros2_ws/src:/ros2_ws/src/bennu:rw
      - ../tests:/ros2_ws/tests:rw
      - ../contract:/ros2_ws/contract:rw
      - ../sim/scripts:/ros2_ws/scripts:ro
      - ../sim/scenarios:/ros2_ws/scenarios:ro
      - ./artifacts:/ros2_ws/artifacts:rw
    depends_on:
      - px4-sitl
    networks:
      - bennu-sim
    entrypoint: ["bash", "-c", "python3 /ros2_ws/scripts/run_mission.py --scenario /ros2_ws/scenarios/nominal_survey.yaml"]

networks:
  bennu-sim:
    driver: bridge
```

**docker-compose.debug.yml** (GUI + QGC + GPU):
```yaml
# Bennu Debug Environment — Full GUI
# Usage: make dev GAZEBO_GUI=1
services:
  px4-sitl:
    build:
      context: ..
      dockerfile: sim/Dockerfile.px4
    container_name: bennu-px4-sitl
    environment:
      - DISPLAY=${DISPLAY}
      - QT_QPA_PLATFORM=xcb
      - PX4_SYS_AUTOSTART=4001
      - PX4_GZ_MODEL=x500
      - __GLX_VENDOR_LIBRARY_NAME=nvidia
      - __EGL_VENDOR_LIBRARY_FILENAMES=/usr/share/glvnd/egl_vendor.d/10_nvidia.json
    volumes:
      - /tmp/.X11-unix:/tmp/.X11-unix:rw
    ports:
      - "14540:14540/udp"
      - "14580:14580/udp"
    networks:
      - bennu-sim
    devices:
      - nvidia.com/gpu=all

  ros2-dev:
    build:
      context: ..
      dockerfile: sim/Dockerfile.ros2
    container_name: bennu-ros2-dev
    environment:
      - DISPLAY=${DISPLAY}
      - QT_QPA_PLATFORM=xcb
    volumes:
      - /tmp/.X11-unix:/tmp/.X11-unix:rw
      - ../drone/ros2_ws/src:/ros2_ws/src/bennu:rw
      - ../tests:/ros2_ws/tests:rw
      - ../contract:/ros2_ws/contract:rw
    depends_on:
      - px4-sitl
    networks:
      - bennu-sim
    stdin_open: true
    tty: true

networks:
  bennu-sim:
    driver: bridge
```

**Your Audit:**
1. Read all three compose files — verify no GPU in dev/sil, GPU only in debug
2. Verify `HEADLESS=1` is set in dev and sil compose files
3. Verify volume mounts include `tests/` and `contract/` directories
4. Run: `cd sim && docker compose -f docker-compose.dev.yml config` — should parse without errors
5. Verify `.devcontainer/devcontainer.json` now points to `docker-compose.dev.yml`

**Accept:**
- [ ] Three compose files exist with correct separation of concerns
- [ ] No GPU requirements in dev or sil compose files
- [ ] devcontainer updated
- [ ] Old `docker-compose.sim.yml` removed

---

### Task 2: Makefile Developer Interface

**What:** A Makefile in `sim/` that provides the primary developer interface for all test and dev commands.

**Why:** Developers should type `make test-unit`, not remember Docker Compose flags.

**Files:**
- Create: `sim/Makefile`

**Makefile contents:**
```makefile
.PHONY: dev dev-watch test-unit test-component test-sitl test-scenarios clean help

COMPOSE_DEV = docker compose -f docker-compose.dev.yml
COMPOSE_SIL = docker compose -f docker-compose.sil.yml
COMPOSE_DBG = docker compose -f docker-compose.debug.yml
ROS2_EXEC = docker exec bennu-ros2-dev bash -c

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

dev: ## Start dev environment (headless PX4 + ros2-dev shell)
	$(COMPOSE_DEV) up -d
	@echo "Dev environment ready. Run: docker exec -it bennu-ros2-dev bash"

dev-watch: dev ## Start dev + pytest-watch auto-rerun
	$(ROS2_EXEC) "pip install -e /ros2_ws/src/bennu/* 2>/dev/null; \
		cd /ros2_ws && ptw --runner 'python -m pytest --tb=short -q' src/bennu/*/test/ tests/"

dev-debug: ## Start debug environment with Gazebo GUI (requires GPU + xhost)
	$(COMPOSE_DBG) up -d
	@echo "Debug environment ready with Gazebo GUI."

test-unit: ## Run Tier 0: unit + contract + integration tests (no PX4)
	$(COMPOSE_DEV) up -d ros2-dev
	$(ROS2_EXEC) "cd /ros2_ws && pip install -e src/bennu/* 2>/dev/null && \
		python -m pytest src/bennu/*/test/ tests/ -v"

test-sitl: ## Run Tier 2: full mission SIL headless (<10 min)
	$(COMPOSE_SIL) up --build --abort-on-container-exit --exit-code-from test-runner
	$(COMPOSE_SIL) down -v

test-scenarios: ## Run Tier 3: scenario matrix (20-40 min)
	$(COMPOSE_SIL) run --rm test-runner \
		python3 /ros2_ws/scripts/run_scenarios.py --dir /ros2_ws/scenarios/

test-all: test-unit test-sitl ## Run Tiers 0 + 2

clean: ## Stop all containers, remove volumes
	$(COMPOSE_DEV) down -v 2>/dev/null || true
	$(COMPOSE_SIL) down -v 2>/dev/null || true
	$(COMPOSE_DBG) down -v 2>/dev/null || true
```

**Your Audit:**
1. Read the Makefile — verify each target maps to the correct compose file
2. Run: `cd sim && make help` — should list all commands with descriptions
3. Run: `cd sim && make test-unit` — should start ros2-dev and run pytest (will fail if no tests yet, that's OK)
4. Verify `make dev-watch` installs packages and starts `ptw`

**Accept:**
- [ ] `make help` shows all commands
- [ ] `make test-unit` runs pytest inside container
- [ ] `make clean` stops all containers

---

### Task 3: Update Dockerfile.ros2 for Testing

**What:** Add pytest, pytest-watch, MAVSDK-Python, and test dependencies to the ROS2 container image.

**Why:** The container needs test tooling for both interactive dev and CI test runs.

**Files:**
- Modify: `sim/Dockerfile.ros2`

**Changes to add after existing pip install section:**
```dockerfile
# Test and simulation dependencies
RUN pip3 install --break-system-packages \
    pytest \
    pytest-watch \
    jsonschema \
    pynacl \
    mavsdk \
    ruff
```

**Your Audit:**
1. Read `sim/Dockerfile.ros2` — verify new packages are added
2. Run: `cd sim && docker compose -f docker-compose.dev.yml build ros2-dev` — should build successfully
3. Run: `docker exec bennu-ros2-dev python3 -c "import pytest; import mavsdk; import jsonschema; print('OK')"` — should print OK

**Accept:**
- [ ] Dockerfile builds with new deps
- [ ] pytest, mavsdk, jsonschema importable inside container

---

### Task 4: GHCR Image Build Workflow

**What:** GitHub Actions workflow that builds and pushes Docker images to GHCR on Dockerfile changes or weekly schedule.

**Why:** CI jobs pull prebuilt images (~30s) instead of building from source (~10 min).

**Files:**
- Create: `.github/workflows/docker-images.yml`

**Workflow:**
```yaml
name: Build Docker Images

on:
  push:
    branches: [main]
    paths:
      - 'sim/Dockerfile.*'
  schedule:
    - cron: '0 4 * * 0'  # Weekly Sunday 4am UTC
  workflow_dispatch:

env:
  REGISTRY: ghcr.io
  PX4_IMAGE: ghcr.io/fadi-labib/bennu/px4-sitl
  ROS2_IMAGE: ghcr.io/fadi-labib/bennu/ros2-dev

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4

      - uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - uses: docker/build-push-action@v5
        with:
          context: .
          file: sim/Dockerfile.px4
          push: true
          tags: ${{ env.PX4_IMAGE }}:v1.16.1,${{ env.PX4_IMAGE }}:latest

      - uses: docker/build-push-action@v5
        with:
          context: .
          file: sim/Dockerfile.ros2
          push: true
          tags: ${{ env.ROS2_IMAGE }}:jazzy,${{ env.ROS2_IMAGE }}:latest
```

**Your Audit:**
1. Read the workflow — verify it triggers on Dockerfile changes and weekly
2. Verify image names match what `docker-compose.sil.yml` references
3. Push to main — verify workflow runs and images appear at `ghcr.io/fadi-labib/bennu/`

**Accept:**
- [ ] Workflow triggers on Dockerfile changes
- [ ] Images pushed to GHCR
- [ ] `docker-compose.sil.yml` references the GHCR image names

---

**Phase 0 Exit Gate:**
- [ ] Three compose files working (dev, sil, debug)
- [ ] Makefile provides `make dev`, `make test-unit`, `make test-sitl`, `make clean`
- [ ] ROS2 container has all test deps
- [ ] GHCR images building

---

## Phase 1: Camera Backend Refactor

### Task 5: Abstract Capture Backend

**What:** Create a `CaptureBackend` abstract base class and extract the existing libcamera and placeholder logic into separate backend implementations.

**Why:** The current camera node detects simulation by catching `FileNotFoundError` on `libcamera-still`. This is implicit and fragile. Explicit backends make simulation intentional and testable.

**Files:**
- Create: `drone/ros2_ws/src/bennu_camera/bennu_camera/capture_backend.py`
- Create: `drone/ros2_ws/src/bennu_camera/bennu_camera/backends/__init__.py`
- Create: `drone/ros2_ws/src/bennu_camera/bennu_camera/backends/libcamera_backend.py`
- Create: `drone/ros2_ws/src/bennu_camera/bennu_camera/backends/placeholder_backend.py`
- Test: `drone/ros2_ws/src/bennu_camera/test/test_backends.py`

**capture_backend.py** (abstract base):
```python
from abc import ABC, abstractmethod
from pathlib import Path


class CaptureBackend(ABC):
    """Abstract base for image capture backends."""

    @abstractmethod
    def capture(self, filepath: Path, width: int, height: int) -> bool:
        """Capture an image to filepath. Returns True on success."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Backend identifier string."""
        ...
```

**backends/placeholder_backend.py:**
```python
from pathlib import Path
from bennu_camera.capture_backend import CaptureBackend


class PlaceholderBackend(CaptureBackend):
    """Generates minimal valid JPEG files for simulation."""

    MINIMAL_JPEG = bytes([
        0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46,
        0x49, 0x46, 0x00, 0x01, 0x01, 0x00, 0x00, 0x01,
        0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
        0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08,
        0x07, 0x07, 0x07, 0x09, 0x09, 0x08, 0x0A, 0x0C,
        0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
        0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D,
        0x1A, 0x1C, 0x1C, 0x20, 0x24, 0x2E, 0x27, 0x20,
        0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
        0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27,
        0x39, 0x3D, 0x38, 0x32, 0x3C, 0x2E, 0x33, 0x34,
        0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
        0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4,
        0x00, 0x1F, 0x00, 0x00, 0x01, 0x05, 0x01, 0x01,
        0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04,
        0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0xFF,
        0xDA, 0x00, 0x08, 0x01, 0x01, 0x00, 0x00, 0x3F,
        0x00, 0x7B, 0x40, 0x1B, 0xFF, 0xD9,
    ])

    def capture(self, filepath: Path, width: int, height: int) -> bool:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_bytes(self.MINIMAL_JPEG)
        return True

    @property
    def name(self) -> str:
        return "placeholder"
```

**backends/libcamera_backend.py:**
```python
import subprocess
from pathlib import Path
from bennu_camera.capture_backend import CaptureBackend


class LibcameraBackend(CaptureBackend):
    """Captures images using libcamera-still on real hardware."""

    def capture(self, filepath: Path, width: int, height: int) -> bool:
        try:
            subprocess.run(
                [
                    "libcamera-still",
                    "-o", str(filepath),
                    "--width", str(width),
                    "--height", str(height),
                    "--nopreview",
                    "-t", "1",
                ],
                check=True,
                capture_output=True,
                timeout=10,
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired,
                FileNotFoundError):
            return False

    @property
    def name(self) -> str:
        return "libcamera"
```

**Tests (3):**
```python
# test_backends.py
def test_placeholder_creates_valid_jpeg()    # File exists, starts with JPEG magic bytes
def test_placeholder_name()                  # .name == "placeholder"
def test_libcamera_returns_false_when_missing()  # libcamera-still not installed → False
```

**Your Audit:**
1. Read `capture_backend.py` — verify ABC with `capture()` and `name` property
2. Read `placeholder_backend.py` — verify JPEG bytes match existing `camera_node.py` placeholder
3. Read `libcamera_backend.py` — verify it handles all 3 exceptions (CalledProcessError, TimeoutExpired, FileNotFoundError)
4. Run: `cd sim && make test-unit` — verify backend tests pass
5. Verify the placeholder JPEG is byte-for-byte identical to the one in current `camera_node.py`

**Accept:**
- [ ] ABC defines the contract
- [ ] Placeholder produces valid JPEG
- [ ] Libcamera gracefully returns False when not available
- [ ] Tests pass

---

### Task 6: Refactor camera_node to Use Backends

**What:** Modify `camera_node.py` to accept a `camera_backend` ROS2 parameter and delegate capture to the selected backend. Remove the inline `FileNotFoundError` detection and `_write_placeholder_jpeg`.

**Why:** This makes simulation explicit. Launch files choose the backend, not runtime error handling.

**Files:**
- Modify: `drone/ros2_ws/src/bennu_camera/bennu_camera/camera_node.py`
- Modify: `drone/ros2_ws/src/bennu_bringup/launch/drone.launch.py`
- Test: `drone/ros2_ws/src/bennu_camera/test/test_camera_node.py`

**Key changes to camera_node.py:**
```python
# New parameter
self.declare_parameter("camera_backend", "libcamera")
backend_name = self.get_parameter("camera_backend").value

# Backend factory
BACKENDS = {
    "libcamera": LibcameraBackend,
    "placeholder": PlaceholderBackend,
}
if backend_name not in BACKENDS:
    raise ValueError(f"Unknown camera backend: {backend_name}")
self._backend = BACKENDS[backend_name]()
self.get_logger().info(f"Camera backend: {self._backend.name}")
```

**Key change to `_capture_image()`:**
```python
success = self._backend.capture(Path(filepath), self.width, self.height)
if not success:
    self.get_logger().error(f"Capture failed via {self._backend.name}")
    return
```

**Remove:** `_write_placeholder_jpeg()` method (now in PlaceholderBackend).

**Remove:** `try/except FileNotFoundError` block in `_capture_image()`.

**Key change to drone.launch.py:**
```python
# Add camera_backend argument
camera_backend_arg = DeclareLaunchArgument(
    "camera_backend",
    default_value="libcamera",
    description="Camera capture backend (libcamera, placeholder)",
)

# Pass to camera node
camera_node = Node(
    package="bennu_camera",
    executable="camera_node",
    name="camera_capture_node",
    parameters=[
        {"output_dir": LaunchConfiguration("output_dir")},
        {"image_width": 4056},
        {"image_height": 3040},
        {"camera_backend": LaunchConfiguration("camera_backend")},
    ],
    output="screen",
)
```

**Usage changes:**
- Hardware: `ros2 launch bennu_bringup drone.launch.py` (defaults to libcamera)
- Simulation: `ros2 launch bennu_bringup drone.launch.py use_sim:=true camera_backend:=placeholder`

**Tests (2):**
```python
# test_camera_node.py
def test_backend_factory_placeholder()   # "placeholder" → PlaceholderBackend instance
def test_backend_factory_invalid()       # "nonexistent" → ValueError
```

**Your Audit:**
1. Read `camera_node.py` — verify `_write_placeholder_jpeg` is gone, `FileNotFoundError` catch is gone
2. Verify backend is selected by parameter, not by exception
3. Read `drone.launch.py` — verify `camera_backend` parameter is passed through
4. Run: `cd sim && make test-unit` — all camera tests pass
5. Run in sim: `ros2 launch bennu_bringup drone.launch.py use_sim:=true camera_backend:=placeholder` — verify it logs "Camera backend: placeholder"

**Accept:**
- [ ] No implicit sim detection in camera_node.py
- [ ] Backend chosen by `camera_backend` parameter
- [ ] Launch file passes backend parameter
- [ ] Existing geotag tests still pass
- [ ] New backend factory tests pass

---

**Phase 1 Exit Gate:**
- [ ] Camera backends are explicit (parameter-driven, not exception-driven)
- [ ] `camera_backend:=placeholder` works in simulation
- [ ] `camera_backend:=libcamera` is the default for hardware
- [ ] All tests pass

---

## Phase 2: Mission Automation

### Task 7: PX4 Readiness Script

**What:** A Python script that polls PX4 SITL over MAVLink until it reports ready (armed-capable state). Used by all SIL tests as a prerequisite.

**Why:** PX4 SITL takes 10-30 seconds to start. Tests that connect immediately fail with connection errors. This script blocks until PX4 is ready.

**Files:**
- Create: `sim/scripts/wait_for_px4.py`
- Test: manual — script exits 0 when PX4 is running, exits 1 on timeout

**Script:**
```python
#!/usr/bin/env python3
"""Wait for PX4 SITL to be ready for mission upload."""
import asyncio
import sys
from mavsdk import System


async def wait_for_px4(address: str = "udp://:14540", timeout: int = 120):
    drone = System()
    await drone.connect(system_address=address)

    print(f"Waiting for PX4 at {address}...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("PX4 connected.")
            break

    print("Waiting for GPS fix...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("PX4 ready: GPS fix OK, home position set.")
            return True

    return False


if __name__ == "__main__":
    try:
        ok = asyncio.run(wait_for_px4())
        sys.exit(0 if ok else 1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
```

**Your Audit:**
1. Start PX4 SITL: `cd sim && make dev`
2. Run: `docker exec bennu-ros2-dev python3 /ros2_ws/scripts/wait_for_px4.py` — should print "PX4 ready" and exit 0
3. Without PX4 running, verify timeout and exit 1

**Accept:**
- [ ] Script exits 0 when PX4 is ready
- [ ] Script exits 1 on timeout
- [ ] Works from inside the Docker network

---

### Task 8: MAVSDK Mission Runner

**What:** A Python script that uploads a small grid mission to PX4, arms, takes off, flies waypoints, and lands. Returns exit code 0 on success.

**Why:** This replaces QGroundControl for automated testing. Without this, every SITL test requires manual interaction.

**Files:**
- Create: `sim/scripts/run_mission.py`

**What the script does:**
1. Call `wait_for_px4()` to ensure PX4 is ready
2. Load scenario YAML for mission parameters (altitude, speed, waypoint count)
3. Generate a small grid of waypoints (using home position + offsets)
4. Upload mission via MAVSDK
5. Arm and start mission
6. Monitor mission progress until LANDED state
7. Exit 0 on successful landing, exit 1 on timeout or failure

**Your Audit:**
1. Start PX4 SITL: `cd sim && make dev`
2. Run: `docker exec bennu-ros2-dev python3 /ros2_ws/scripts/run_mission.py --scenario /ros2_ws/scenarios/nominal_survey.yaml`
3. Watch PX4 logs — should see arm, takeoff, waypoint progress, land
4. Verify exit code 0

**Accept:**
- [ ] Mission uploads and starts without QGroundControl
- [ ] Drone takes off, flies waypoints, and lands
- [ ] Script exits 0 on success
- [ ] Script exits 1 on mission failure or timeout

---

### Task 9: Nominal Survey Scenario

**What:** YAML scenario definition for the baseline happy-path test. Defines world, vehicle, mission parameters, and assertions.

**Why:** Every test run is driven by a versioned scenario file, not hard-coded values.

**Files:**
- Create: `sim/scenarios/nominal_survey.yaml`

**Content:**
```yaml
name: nominal_survey
description: Baseline happy path — flat world, small grid, complete bundle
world: default
vehicle: x500
mission:
  type: grid
  altitude_m: 30
  speed_mps: 3
  waypoints: 6
  trigger_distance_m: 10
camera_backend: placeholder
assertions:
  min_triggers: 4
  expected_end_state: landed
  max_duration_s: 180
  require_bundle: false   # Bundle validation added in Phase 3
```

**Your Audit:**
1. Read the YAML — verify mission parameters are reasonable for SITL (low altitude, few waypoints, slow speed)
2. Verify `camera_backend: placeholder` matches the launch parameter name
3. Verify `require_bundle: false` for now (bundle pipeline not wired into SITL yet)

**Accept:**
- [ ] Scenario file is valid YAML
- [ ] Parameters produce a short mission (~1-2 min in sim)
- [ ] Assertions are reasonable for the nominal case

---

### Task 10: Artifact Validation Script

**What:** A Python script that inspects the output directory after a mission and validates artifacts against the scenario's assertions.

**Why:** SITL tests need to assert on outputs (images, metadata), not just "the drone didn't crash."

**Files:**
- Create: `sim/scripts/validate_artifacts.py`
- Test: `sim/scripts/test_validate_artifacts.py`

**What the script does:**
1. Load scenario YAML assertions
2. Count images in output directory
3. Verify count >= `min_triggers`
4. Verify all images are valid JPEGs (start with `FF D8`)
5. Check for geotag EXIF data if present
6. Print pass/fail summary
7. Exit 0 if all assertions pass, exit 1 otherwise

**Tests (3):**
```python
def test_passes_with_enough_images()    # 6 images, min_triggers=4 → pass
def test_fails_with_too_few()           # 2 images, min_triggers=4 → fail
def test_validates_jpeg_magic_bytes()   # Non-JPEG file → fail
```

**Your Audit:**
1. Read the script — verify it checks image count, JPEG validity
2. Run tests: `cd sim && python -m pytest scripts/test_validate_artifacts.py -v`
3. After a successful SITL run, run: `python3 validate_artifacts.py --scenario nominal_survey.yaml --output-dir /tmp/captures`

**Accept:**
- [ ] Validates image count against scenario threshold
- [ ] Detects invalid (non-JPEG) files
- [ ] Tests pass

---

**Phase 2 Exit Gate:**
- [ ] `wait_for_px4.py` reliably detects PX4 readiness
- [ ] `run_mission.py` flies a mission without QGroundControl
- [ ] Nominal survey scenario completes in <3 min
- [ ] `validate_artifacts.py` asserts on mission outputs
- [ ] `make test-sitl` runs the full Tier 2 flow end-to-end

---

## Phase 3: CI Integration

### Task 11: CI Workflow — Lint and Unit Tests

**What:** GitHub Actions workflow that runs ruff + pytest on every PR. No Docker, no PX4 — just Python tests.

**Why:** Fast feedback (< 3 min) catches most regressions before the heavier SIL job.

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `requirements-dev.txt`

**requirements-dev.txt:**
```
pytest
pytest-watch
jsonschema
pynacl
ruff
```

**Workflow:**
```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint-and-unit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r requirements-dev.txt
      - run: pip install -e drone/ros2_ws/src/bennu_camera
      - run: ruff check .
      - run: python -m pytest drone/ros2_ws/src/*/test/ tests/ -v
```

**Your Audit:**
1. Read the workflow — verify it runs on push+PR to main
2. Push a branch, open a draft PR — verify CI runs and passes
3. Verify `requirements-dev.txt` has all needed packages

**Accept:**
- [ ] CI runs on every PR
- [ ] ruff + pytest both execute
- [ ] Passes on current codebase

---

### Task 12: CI Workflow — SIL Smoke Test

**What:** GitHub Actions workflow that pulls prebuilt images from GHCR, starts PX4 SITL headless, runs the nominal survey scenario, and validates artifacts.

**Why:** This is the merge gate that proves the full pipeline works.

**Files:**
- Create: `.github/workflows/sil-smoke.yml`

**Workflow:**
```yaml
name: SIL Smoke Test

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  sil-smoke:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4

      - name: Pull prebuilt images
        run: |
          docker pull ghcr.io/fadi-labib/bennu/px4-sitl:v1.16.1 || true
          docker pull ghcr.io/fadi-labib/bennu/ros2-dev:jazzy || true

      - name: Run SIL smoke test
        working-directory: sim
        run: |
          docker compose -f docker-compose.sil.yml up \
            --abort-on-container-exit \
            --exit-code-from test-runner

      - name: Upload artifacts on failure
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: sil-artifacts
          path: sim/artifacts/

      - name: Cleanup
        if: always()
        working-directory: sim
        run: docker compose -f docker-compose.sil.yml down -v
```

**Your Audit:**
1. Read the workflow — verify it pulls prebuilt images, falls back to build if not available
2. Verify artifact upload happens on failure only
3. Verify timeout is set (15 min)
4. Push to a branch, open PR — verify SIL smoke test runs

**Accept:**
- [ ] SIL smoke test runs in CI
- [ ] Failed runs upload artifacts for debugging
- [ ] Total job time under 15 minutes

---

**Phase 3 Exit Gate:**
- [ ] Every PR runs lint + unit tests (< 3 min)
- [ ] Every PR runs SIL smoke test (< 15 min)
- [ ] Failed SIL runs upload artifacts
- [ ] Both jobs pass on current codebase

---

## Phase 4: pytest-watch Dev Loop

### Task 13: pytest-watch Configuration

**What:** Configure pytest-watch inside the ros2-dev container for auto-rerunning tests on file changes.

**Why:** The fast inner loop: edit Python on host → volumes sync → pytest-watch reruns → see results in <2 seconds.

**Files:**
- Create: `pytest.ini` (project root)
- Modify: `sim/Makefile` (already has `dev-watch` target from Task 2)

**pytest.ini:**
```ini
[pytest]
testpaths =
    drone/ros2_ws/src/bennu_camera/test
    tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

**Your Audit:**
1. Run: `cd sim && make dev-watch`
2. In another terminal, edit a test file (add a print statement)
3. Verify pytest-watch detects the change and reruns within 1-2 seconds
4. Revert the edit — verify it reruns again

**Accept:**
- [ ] File changes trigger automatic test rerun
- [ ] Rerun completes in <5 seconds
- [ ] Both package-local and top-level tests are discovered

---

**Phase 4 Exit Gate:**
- [ ] `make dev-watch` provides instant feedback on code changes
- [ ] pytest discovers all test directories

---

## Phase Summary

| Phase | Tasks | Key Deliverable |
|---|---|---|
| 0: Infrastructure | 1-4 | Split compose files, Makefile, test deps in container, GHCR images |
| 1: Camera Backends | 5-6 | Explicit camera backends, refactored camera_node |
| 2: Mission Automation | 7-10 | MAVSDK runner, scenario YAML, artifact validation |
| 3: CI Integration | 11-12 | Lint+unit CI job, SIL smoke test CI job |
| 4: Dev Loop | 13 | pytest-watch auto-rerun |

**After all tasks:**
1. `make test-unit` runs all Python tests inside Docker in seconds
2. `make test-sitl` flies a headless mission and validates artifacts
3. `make dev-watch` auto-reruns tests on file changes
4. Every PR runs lint + unit + SIL smoke test in CI
5. Camera simulation is explicit and parameter-driven
6. No developer needs QGroundControl for standard testing
7. Failed CI runs upload debugging artifacts
