# Run SIL Tests

Run automated Software-in-the-Loop (SIL) mission tests against PX4 SITL. These tests fly the simulated drone through a complete mission — takeoff, waypoints, camera triggers, RTL, landing — and verify the outcome.

!!! abstract "Prerequisites"

    - Docker and Docker Compose installed
    - First run pulls ~4GB of prebuilt images from GHCR (PX4 SITL + ROS2)
    - No GPU required (headless mode)

## Quick Start

```bash
cd sim
make test-smoke
```

This starts PX4 SITL + Gazebo (headless), waits for GPS lock, runs the default survey mission, and exits with code 0 on success or 1 on failure. Containers are cleaned up automatically.

## Run a SIL Test Manually

`make test-smoke` is the one-shot path. To step through the same flow interactively
— so you can pause, inspect state, tweak a scenario, or re-run a single stage —
use the SIL compose stack directly with an overridden command.

### 1. Bring up PX4 SITL only

```bash
cd sim
docker compose -f docker-compose.sil.yml up -d px4-sitl
```

Wait for the container to report `healthy` (the healthcheck polls UDP port 18570,
which PX4 binds once it's ready):

```bash
docker ps --filter "name=bennu-px4-sitl-sil"
# STATUS column should read: Up X seconds (healthy)
```

If it stays `(health: starting)` for >60s, tail the logs:

```bash
docker logs --tail 50 bennu-px4-sitl-sil
```

### 2. Open an interactive test-runner shell

The test-runner image already has MAVSDK (`mavsdk>=2,<3`), the scenarios, and the
mission scripts mounted. Override its default command to drop into a shell:

```bash
docker compose -f docker-compose.sil.yml run --rm -it --entrypoint bash test-runner
```

You're now inside the container at `/ros2_ws`. PX4 SITL is reachable on
`udp://:14540` (host networking).

### 3. Run the smoke mission by hand

```bash
python3 /ros2_ws/scripts/run_mission.py \
    --scenario /ros2_ws/scenarios/nominal_survey.yaml \
    --timeout 180
```

Expected output, stage by stage:

```
[run_mission] Scenario: nominal_survey
[run_mission] Connected on attempt 1
[run_mission] Waiting for PX4 readiness (GPS fix + home position)...
[run_mission] Home: (47.397742, 8.545594)
[run_mission] Generated 6 waypoints
[run_mission] Uploading mission...
[run_mission] Arming...
[run_mission] Starting mission...
[run_mission] Progress: 1/6
[run_mission] Progress: 2/6
...
[run_mission] Progress: 6/6
[run_mission] Mission items complete, waiting for landing...
[run_mission] Landed successfully
[run_mission] Mission finished successfully
```

Exit code is `0` on success, `1` on any failure (timeout, GPS lock, mission overrun).

### 4. Watch the mission live

In a separate terminal on the host, open QGroundControl. Both the SIL
PX4 container and QGC use UDP 14550, so QGC auto-connects and shows the
drone flying the lawnmower pattern in real time. Useful for:

- Visually confirming the waypoint grid matches the scenario
- Spotting unexpected behavior (drift, RTL kicking in early)
- Checking telemetry (battery, GPS, mode transitions)

### 5. Iterate on a scenario

Edit `sim/scenarios/nominal_survey.yaml` (or any other scenario) on the host —
the file is bind-mounted read-only into the container as `/ros2_ws/scenarios/`,
so changes appear immediately. Re-run step 3 with the same command.

To create and run a new scenario:

```bash
# On the host
cp sim/scenarios/nominal_survey.yaml sim/scenarios/my_scenario.yaml
$EDITOR sim/scenarios/my_scenario.yaml

# Inside the test-runner shell
python3 /ros2_ws/scripts/run_mission.py \
    --scenario /ros2_ws/scenarios/my_scenario.yaml
```

### 6. Tear it all down

Exit the test-runner shell (`exit` or Ctrl+D), then on the host:

```bash
cd sim
docker compose -f docker-compose.sil.yml down -v
```

The `-v` flag also removes the ephemeral volumes — important so the next run
starts from a clean PX4 state, not a stale parameter cache.

!!! tip "Use the dev stack instead?"

    The dev compose (`make dev`) doesn't mount `sim/scripts/` or `sim/scenarios/`
    into the ros2-dev container, so `run_mission.py` isn't directly available
    there. If you want to keep your `make dev` session running and also do a
    manual SIL test, copy the script in:

    ```bash
    docker cp sim/scripts/run_mission.py bennu-ros2-dev:/tmp/run_mission.py
    docker cp sim/scripts/wait_for_px4.py bennu-ros2-dev:/tmp/wait_for_px4.py
    docker cp sim/scenarios/ bennu-ros2-dev:/tmp/scenarios
    docker exec -it bennu-ros2-dev bash -c \
        "cd /tmp && python3 run_mission.py --scenario scenarios/nominal_survey.yaml"
    ```

## How It Works

```mermaid
sequenceDiagram
    participant M as make test-smoke
    participant P as PX4 SITL
    participant T as test-runner
    
    M->>P: Start px4-sitl container
    P->>P: Boot PX4 + Gazebo (headless)
    P->>P: Healthcheck: wait for port 18570
    M->>T: Start test-runner (after healthcheck passes)
    T->>P: Connect via MAVSDK (UDP 14540)
    T->>P: Wait for GPS fix + home position
    T->>P: Upload mission waypoints
    T->>P: Arm + start mission
    T->>P: Monitor progress
    P->>T: Mission complete
    T->>P: Wait for landing
    T-->>M: Exit code 0 (success)
```

## Scenario Files

SIL tests are driven by YAML scenario files in `sim/scenarios/`. Each scenario defines a mission profile and expected outcomes.

### Scenario Format

```yaml
name: nominal_survey
description: Baseline happy path — flat world, small grid
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
  require_bundle: false
```

| Field | Description |
|-------|-------------|
| `name` | Scenario identifier (used in logs) |
| `mission.altitude_m` | Flight altitude in meters |
| `mission.speed_mps` | Cruise speed in m/s |
| `mission.waypoints` | Number of waypoints to generate in a lawnmower grid |
| `mission.trigger_distance_m` | Distance-based camera trigger interval |
| `assertions.max_duration_s` | Timeout — fail if mission takes longer |
| `assertions.expected_end_state` | Expected final state (`landed`) |
| `assertions.min_triggers` | Minimum camera triggers expected |

### Available Scenarios

| Scenario | File | Description |
|----------|------|-------------|
| `nominal_survey` | `scenarios/nominal_survey.yaml` | Baseline happy path — 6 waypoints, 30m altitude, flat world |

### Writing a New Scenario

Create a YAML file in `sim/scenarios/`:

```yaml
name: high_altitude_survey
description: Survey at 80m with tighter waypoint spacing
world: default
vehicle: x500
mission:
  type: grid
  altitude_m: 80
  speed_mps: 5
  waypoints: 10
  trigger_distance_m: 5
camera_backend: placeholder
assertions:
  min_triggers: 8
  expected_end_state: landed
  max_duration_s: 300
  require_bundle: false
```

Run it:

```bash
cd sim
docker compose -f docker-compose.sil.yml run --rm test-runner \
  python3 /ros2_ws/scripts/run_mission.py \
  --scenario /ros2_ws/scenarios/high_altitude_survey.yaml
```

Or run all scenarios:

```bash
cd sim
make test-sitl
```

## Make Targets

| Command | What it does |
|---------|-------------|
| `make test-smoke` | Run default SIL mission (nominal_survey) |
| `make test-sitl` | Run all scenarios in `sim/scenarios/` |
| `make test` | Run unit tests only (no PX4 needed) |
| `make test-all` | Run unit tests + SIL test |
| `make clean` | Stop all containers and remove volumes |

## Timeouts and Timing

SIL tests have multiple timeout layers:

| Timeout | Default | Where |
|---------|---------|-------|
| PX4 healthcheck | 345s max (45s start + 30x10s) | `docker-compose.sil.yml` |
| MAVSDK connection | 5 retries with exponential backoff | `run_mission.py` |
| PX4 readiness (GPS lock) | 180s | `run_mission.py --timeout` |
| Mission duration | 180s (per scenario) | `assertions.max_duration_s` |
| Landing wait | 60s | `run_mission.py` (hardcoded) |
| GitHub Actions job | 30 min | `sil-smoke.yml` |

!!! tip "Slow machines"

    If PX4 takes too long to get GPS lock, increase the readiness timeout:

    ```bash
    docker compose -f docker-compose.sil.yml run --rm test-runner \
      python3 /ros2_ws/scripts/run_mission.py \
      --scenario /ros2_ws/scenarios/nominal_survey.yaml \
      --timeout 300
    ```

## Debugging Failures

### PX4 never becomes healthy

The healthcheck waits for UDP port 18570 to open. If it never passes:

```bash
# Check PX4 logs
docker logs bennu-px4-sitl-sil 2>&1 | tail -50

# Common causes:
# - Port conflict (another PX4 instance running)
# - Insufficient memory for Gazebo
```

### MAVSDK can't connect

```
[run_mission] Connection attempt 1 failed: ...
[run_mission] Retrying in 1s...
```

The test-runner retries up to 5 times with exponential backoff. If all attempts fail:

```bash
# Verify PX4 is actually listening
docker exec bennu-px4-sitl-sil grep ':388C ' /proc/net/udp
# 388C = port 14540 (MAVSDK offboard API)
```

### GPS lock timeout

```
[run_mission] TIMEOUT: PX4 not ready
```

PX4 SITL GPS simulation takes 30-120s depending on machine speed. On slow CI runners this can exceed the default timeout.

```bash
# Run with longer timeout
make test-smoke TIMEOUT=300
```

### Mission timeout

```
[run_mission] TIMEOUT: mission did not complete in 180s
```

The mission took longer than `assertions.max_duration_s`. Either increase the timeout in the scenario YAML or reduce the number of waypoints.

### Inspecting Artifacts

Failed runs save artifacts to `sim/artifacts/`:

```bash
ls sim/artifacts/
```

In GitHub Actions, artifacts are uploaded automatically on failure and can be downloaded from the workflow run page.

## CI Integration

SIL tests run automatically on:

- Pull requests to `main`
- Weekday schedule (6am UTC)
- Manual dispatch (`gh workflow run sil-smoke.yml`)

The CI workflow pulls prebuilt Docker images from GHCR instead of building from source, saving ~15 minutes per run.

!!! warning "Known CI Timing Issue"

    GitHub Actions shared runners are slower than local machines. PX4 GPS lock can take longer than expected. The healthcheck and connection timeouts are tuned for this, but occasional flaky failures may occur. Re-run the workflow if it times out.
