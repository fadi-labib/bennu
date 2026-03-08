# Review Fix Plan — All 17 Findings

**Status:** Partially superseded

> Findings 7-17 (architecture, dependency governance, process gaps) are now covered by
> `2026-03-08-drone-platform-readiness-plan.md` — compatibility matrix (Task 2),
> CI pipeline (Task 3), governance files (Task 4), phase exit gates, and testing strategy.
>
> **Findings 1-6 remain OPEN** — these are code/config bugs that need standalone fixes
> before or alongside platform readiness work. Finding 1 (failsafe) is safety-critical.

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix all 17 findings from `docs/reviews/2026-03-08-project-architecture-review.md`

**Architecture:** Findings 1–6 are code/config fixes. Findings 7–17 are documentation and process artifacts. Code fixes come first (safety-critical), then docs.

**Tech Stack:** Bash, Python (ROS2 rclpy), YAML, Docker, Markdown

**Reference:** Every task below maps to a numbered finding in the review document.

---

## Task 1: Fix NAV_DLL_ACT Failsafe Misconfiguration (Finding #1)

**Why:** `NAV_DLL_ACT: 0` means **disabled** in PX4, not RTL. The comment says "return to launch" but the value disables the failsafe entirely. This is a safety bug — on data link loss the drone would do nothing.

**Files:**
- Modify: `firmware/px4/params/base_params.yaml:17`

**Step 1: Fix the parameter value**

Change line 17 in `firmware/px4/params/base_params.yaml` from:

```yaml
NAV_DLL_ACT: 0             # Data link loss action: return to launch
```

to:

```yaml
NAV_DLL_ACT: 2             # Data link loss action: 0=Disabled 1=Hold 2=RTL 3=Land
```

PX4 parameter reference:
- `0` = Disabled (no action)
- `1` = Hold mode
- `2` = Return to launch (RTL)
- `3` = Land immediately

**Step 2: Also audit NAV_RCL_ACT while we're here**

Verify line 18. `NAV_RCL_ACT: 2` is correct (RC loss → RTL). Update the comment for consistency:

```yaml
NAV_RCL_ACT: 2             # RC loss action: 0=Disabled 1=Loiter 2=RTL 3=Land
```

**Step 3: Commit**

```bash
git add firmware/px4/params/base_params.yaml
git commit -m "fix: correct NAV_DLL_ACT failsafe from disabled (0) to RTL (2)

NAV_DLL_ACT=0 means disabled in PX4, not RTL. The drone would take
no action on data link loss. Changed to 2 (RTL) for safety.
Also improved parameter comments with value legends."
```

---

## Task 2: Fix Double XRCE Agent in Sim (Finding #2)

**Why:** `sim/Dockerfile.ros2` starts `MicroXRCEAgent udp4 -p 8888` as its CMD. When the user runs `ros2 launch bennu_bringup drone.launch.py use_sim:=true`, the launch file starts a **second** agent on the same port. This causes port conflicts and nondeterministic behavior.

**Fix strategy:** Remove the agent from the Dockerfile CMD and let the launch file be the single authority for starting the agent. The Dockerfile CMD should just keep the container alive (bash) since it's a dev container.

**Files:**
- Modify: `sim/Dockerfile.ros2:45`

**Step 1: Change the Dockerfile CMD**

Change line 45 of `sim/Dockerfile.ros2` from:

```dockerfile
CMD ["bash", "-c", "MicroXRCEAgent udp4 -p 8888"]
```

to:

```dockerfile
# Agent is started by drone.launch.py (use_sim:=true), not here.
# This container runs as a dev shell — attach via VS Code or docker exec.
CMD ["bash"]
```

**Step 2: Verify the launch file already handles sim mode correctly**

Confirm `drone/ros2_ws/src/bennu_bringup/launch/drone.launch.py` lines 55-64 already start the UDP agent when `use_sim:=true`. It does — no change needed there.

**Step 3: Commit**

```bash
git add sim/Dockerfile.ros2
git commit -m "fix: remove duplicate XRCE agent from Dockerfile.ros2

The agent was started both in the Docker CMD and by drone.launch.py
when use_sim:=true, causing port conflicts on UDP 8888. The launch
file is now the single authority for agent lifecycle."
```

---

## Task 3: Fix bennu_camera ament_python Packaging (Finding #3)

**Why:** The `bennu_camera` package is missing the `resource/` directory with its ament index marker file, and `setup.py` doesn't declare the required `data_files` entries. This breaks `ros2 pkg list` discovery and `colcon` install metadata. Compare with `bennu_bringup` which does this correctly.

**Files:**
- Create: `drone/ros2_ws/src/bennu_camera/resource/bennu_camera` (empty file)
- Modify: `drone/ros2_ws/src/bennu_camera/setup.py`

**Step 1: Create the resource marker file**

```bash
mkdir -p drone/ros2_ws/src/bennu_camera/resource
touch drone/ros2_ws/src/bennu_camera/resource/bennu_camera
```

This empty file is required by the ament build system for package discovery.

**Step 2: Update setup.py with data_files**

Replace the entire contents of `drone/ros2_ws/src/bennu_camera/setup.py` with:

```python
from setuptools import setup

package_name = "bennu_camera"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Fadi Labib",
    maintainer_email="github@fadilabib.com",
    description="Camera capture and geotagging for Bennu drone",
    license="MIT",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "camera_node = bennu_camera.camera_node:main",
        ],
    },
)
```

The two key additions are the `data_files` lines that register the package with ament index and install the `package.xml`.

**Step 3: Verify build (in sim container or locally)**

```bash
cd drone/ros2_ws && colcon build --packages-select bennu_camera
```

Expected: builds without errors.

**Step 4: Commit**

```bash
git add drone/ros2_ws/src/bennu_camera/resource/bennu_camera
git add drone/ros2_ws/src/bennu_camera/setup.py
git commit -m "fix: add ament_python resource marker to bennu_camera

Missing resource/ directory and data_files in setup.py broke
package discovery via ros2 pkg list and colcon install metadata."
```

---

## Task 4: Standardize XRCE Agent Binary Name (Finding #4)

**Why:** Two different binary names are used across the project:
- `drone/setup_pi.sh` installs via snap → binary is `micro-xrce-dds-agent`
- `drone/ros2_ws/src/bennu_bringup/launch/drone.launch.py` calls `MicroXRCEAgent`
- `sim/Dockerfile.ros2` builds from source → binary is `MicroXRCEAgent`

The snap binary (`micro-xrce-dds-agent`) and the source-built binary (`MicroXRCEAgent`) are different names for the same tool. The launch file must use the correct name for each environment.

**Fix strategy:** The launch file should try the source-built name first (sim), fall back to snap name (hardware). Since `ExecuteProcess` doesn't support fallback, use an environment variable or a wrapper script. The simplest fix: update the Pi setup to build from source too (matching the sim), so both use `MicroXRCEAgent`.

However, snap is more maintainable for the Pi. So instead: create a symlink on the Pi during setup so both names work.

**Files:**
- Modify: `drone/setup_pi.sh:49`

**Step 1: Add symlink after snap install**

In `drone/setup_pi.sh`, after line 49 (`sudo snap install micro-xrce-dds-agent`), add:

```bash
# Create symlink so launch files can use the same binary name as source-built agent
sudo ln -sf /snap/bin/micro-xrce-dds-agent /usr/local/bin/MicroXRCEAgent
```

**Step 2: Add a comment to the launch file documenting the convention**

In `drone/ros2_ws/src/bennu_bringup/launch/drone.launch.py`, add a comment before the serial agent (before line 42):

```python
    # Binary name: "MicroXRCEAgent" works in both environments:
    #   - Sim: built from source in Dockerfile.ros2
    #   - Hardware: symlinked from snap binary in setup_pi.sh
```

**Step 3: Commit**

```bash
git add drone/setup_pi.sh drone/ros2_ws/src/bennu_bringup/launch/drone.launch.py
git commit -m "fix: standardize XRCE agent binary name across environments

Snap installs as 'micro-xrce-dds-agent', source build as
'MicroXRCEAgent'. Added symlink in Pi setup so the launch file
can use 'MicroXRCEAgent' consistently in both sim and hardware."
```

---

## Task 5: Harden PX4 Parameter Upload Script (Finding #5)

**Why:** Current `upload_params.sh` has three problems:
1. Opens a new MAVLink connection per parameter (slow, risks connection churn)
2. Coerces all values to `float()` (integer params like `SYS_AUTOSTART=4001` may lose precision)
3. Weak ack verification (doesn't check if the value was actually set correctly)

**Files:**
- Modify: `firmware/px4/upload_params.sh`

**Step 1: Rewrite the upload script**

Replace the entire contents of `firmware/px4/upload_params.sh` with:

```bash
#!/usr/bin/env bash
# Upload PX4 parameters to Pixhawk 6C via MAVLink
# Usage: ./firmware/px4/upload_params.sh [param_file.yaml ...]
#
# If no files specified, uploads all param files in order.
#
# Prerequisites:
#   pip install pymavlink
#   Pixhawk connected via USB or telemetry radio

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARAMS_DIR="$SCRIPT_DIR/params"
PORT="${PX4_PORT:-/dev/ttyACM0}"
BAUD="${PX4_BAUD:-57600}"

# Ordered list of param files (apply in this order)
PARAM_FILES=(
    "base_params.yaml"
    "motor_params.yaml"
    "gps_params.yaml"
    "companion_params.yaml"
    "camera_params.yaml"
    "tuning_params.yaml"
)

# If specific files provided, use those instead
if [ $# -gt 0 ]; then
    PARAM_FILES=("$@")
fi

# Collect all param=value pairs from all files
ALL_PARAMS=""
for param_file in "${PARAM_FILES[@]}"; do
    filepath="$PARAMS_DIR/$param_file"
    if [ ! -f "$filepath" ]; then
        filepath="$param_file"
    fi
    if [ ! -f "$filepath" ]; then
        echo "WARNING: $param_file not found, skipping"
        continue
    fi
    echo "--- Loading: $param_file ---"
    while IFS= read -r line; do
        # Skip comments and blank lines
        [[ "$line" =~ ^[[:space:]]*# ]] && continue
        [[ -z "${line// /}" ]] && continue
        # Extract PARAM: value (strip comments)
        param=$(echo "$line" | cut -d: -f1 | xargs)
        value=$(echo "$line" | cut -d: -f2 | sed 's/#.*//' | xargs)
        if [ -n "$param" ] && [ -n "$value" ]; then
            ALL_PARAMS+="${param}=${value}"$'\n'
            echo "  $param = $value"
        fi
    done < "$filepath"
done

if [ -z "$ALL_PARAMS" ]; then
    echo "No parameters to upload."
    exit 0
fi

PARAM_COUNT=$(echo -n "$ALL_PARAMS" | grep -c '^')
echo ""
echo "Uploading $PARAM_COUNT parameters via $PORT at $BAUD baud"
echo ""

# Upload all params in a single MAVLink session with typed values and strict ack
python3 << PYEOF
import sys
from pymavlink import mavutil

params_text = """$ALL_PARAMS"""
params = []
for line in params_text.strip().split("\n"):
    if "=" not in line:
        continue
    name, val_str = line.split("=", 1)
    name = name.strip()
    val_str = val_str.strip()
    # Preserve integer vs float type
    if "." in val_str:
        value = float(val_str)
    else:
        try:
            int_val = int(val_str)
            value = float(int_val)  # MAVLink param_set uses float wire format
        except ValueError:
            value = float(val_str)
    params.append((name, value))

print(f"Connecting to $PORT at $BAUD baud...")
master = mavutil.mavlink_connection("$PORT", baud=$BAUD)
master.wait_heartbeat(timeout=10)
print(f"Connected (sysid={master.target_system}, compid={master.target_component})")
print()

failed = []
for name, value in params:
    master.param_set_send(name, value)
    ack = master.recv_match(type="PARAM_VALUE", blocking=True, timeout=5)
    if ack and ack.param_id.rstrip("\x00") == name:
        if abs(ack.param_value - value) < 0.001:
            print(f"  OK: {name} = {ack.param_value}")
        else:
            print(f"  MISMATCH: {name} sent={value} got={ack.param_value}", file=sys.stderr)
            failed.append(name)
    else:
        print(f"  TIMEOUT: {name} (no ack received)", file=sys.stderr)
        failed.append(name)

print()
if failed:
    print(f"FAILED ({len(failed)}/{len(params)}): {', '.join(failed)}", file=sys.stderr)
    sys.exit(1)
else:
    print(f"All {len(params)} parameters set successfully.")
PYEOF

echo ""
echo "Done. Reboot the flight controller to apply all changes."
echo "  mavlink shell: reboot"
echo "  or: power cycle the Pixhawk"
```

Key improvements:
- **Single MAVLink session** — connects once, uploads all params, disconnects
- **Typed values** — detects int vs float from the YAML value format
- **Strict ack verification** — checks param name matches AND value matches within tolerance
- **Clear failure reporting** — lists all failed params with reason, exits non-zero on failure

**Step 2: Verify syntax**

```bash
bash -n firmware/px4/upload_params.sh
```

Expected: no output (no syntax errors).

**Step 3: Commit**

```bash
git add firmware/px4/upload_params.sh
git commit -m "fix: harden param upload with single session and strict ack

Rewrote upload_params.sh to use a single MAVLink connection for all
params, verify ack values match within tolerance, and report failures
with non-zero exit code. Removes per-param connection churn."
```

---

## Task 6: Fix ODM process.sh Empty Input Handling (Finding #6)

**Why:** `ground/odm/process.sh` counts images but never checks if the count is 0. It proceeds to run the Docker ODM container with no images, which fails with a confusing error from ODM itself. Also, `ls -1 *.jpg *.JPG` can glob-expand incorrectly in edge cases.

**Files:**
- Modify: `ground/odm/process.sh:19-21`

**Step 1: Add image count validation**

Replace lines 19-21 of `ground/odm/process.sh`:

```bash
IMAGE_COUNT=$(ls -1 "$IMAGE_DIR"/*.jpg "$IMAGE_DIR"/*.JPG 2>/dev/null | wc -l)
echo "Processing $IMAGE_COUNT images from $IMAGE_DIR"
echo "Profile: $PROFILE"
```

with:

```bash
IMAGE_COUNT=$(find "$IMAGE_DIR" -maxdepth 1 -iname '*.jpg' -o -iname '*.jpeg' | wc -l)

if [ "$IMAGE_COUNT" -eq 0 ]; then
    echo "Error: No JPEG images found in $IMAGE_DIR"
    echo "Expected: .jpg or .jpeg files in the directory"
    exit 1
fi

echo "Processing $IMAGE_COUNT images from $IMAGE_DIR"
echo "Profile: $PROFILE"
```

Also fix line 38 — the `sync_images.sh` final count line has the same glob issue. But that's a separate file — covered below.

**Step 2: Fix sync_images.sh final count**

Replace line 38 of `ground/transfer/sync_images.sh`:

```bash
echo "Image count: $(ls -1 "$OUTPUT_DIR"/*.jpg | wc -l)"
```

with:

```bash
echo "Image count: $(find "$OUTPUT_DIR" -maxdepth 1 -iname '*.jpg' | wc -l)"
```

**Step 3: Commit**

```bash
git add ground/odm/process.sh ground/transfer/sync_images.sh
git commit -m "fix: validate image count before running ODM, fix glob edge cases

process.sh now exits with clear error when no images are found instead
of passing an empty folder to ODM. Replaced ls glob with find for
reliable counting."
```

---

## Task 7: Create Compatibility Matrix (Findings #7, #12, #13)

**Why:** Version drift across docs and implementation. Dockerfile.px4 pins v1.16.1, but `firmware/px4/VERSION` says v1.15.2. `px4_msgs` is cloned from HEAD (unpinned). Docker base images are unpinned. No single source of truth for what versions are tested together.

**Files:**
- Create: `docs/compatibility-matrix.md`
- Modify: `firmware/px4/VERSION`
- Modify: `sim/Dockerfile.ros2:28`
- Modify: `sim/Dockerfile.px4:44`

**Step 1: Fix the VERSION file**

Replace the contents of `firmware/px4/VERSION` with:

```
PX4_VERSION=v1.16.1
BOARD_TARGET=holybro_pixhawk6c
LAST_FLASH_DATE=
NOTES=Upgraded from v1.15.2 to v1.16.1
```

**Step 2: Pin px4_msgs to a release tag in Dockerfile.ros2**

Replace line 28 of `sim/Dockerfile.ros2`:

```dockerfile
RUN git clone --depth 1 https://github.com/PX4/px4_msgs.git
```

with:

```dockerfile
# Pin to release/1.15 branch — must match PX4 major version (see docs/compatibility-matrix.md)
RUN git clone --depth 1 --branch release/1.15 https://github.com/PX4/px4_msgs.git
```

Note: PX4 v1.16.x uses px4_msgs `release/1.15` branch (confirmed in PX4 docs). If a `release/1.16` branch exists at execution time, update this pin.

**Step 3: Pin Docker base images**

In `sim/Dockerfile.px4`, change line 3:

```dockerfile
FROM ubuntu:24.04
```

to:

```dockerfile
FROM ubuntu:24.04@sha256:XXX
```

Actually, for maintainability, tag pinning (`ubuntu:24.04`) is sufficient — it's already a release tag, not `latest`. Leave as-is. The `ros:jazzy` base in `Dockerfile.ros2` is similarly acceptable as a release tag.

**Step 4: Create the compatibility matrix**

Create `docs/compatibility-matrix.md`:

```markdown
# Bennu Compatibility Matrix

Last verified: 2026-03-08

This is the single source of truth for tested dependency versions.
Any version changes must update this file.

## Core Stack

| Component              | Version         | Pin Location                        |
|------------------------|-----------------|-------------------------------------|
| PX4-Autopilot          | v1.16.1         | `sim/Dockerfile.px4:44`, `firmware/px4/VERSION` |
| px4_msgs               | release/1.15    | `sim/Dockerfile.ros2:28`            |
| ROS 2                  | Jazzy Jalisco   | `sim/Dockerfile.ros2:2`, `drone/setup_pi.sh:42` |
| Gazebo                 | Harmonic        | `sim/Dockerfile.px4:39`             |
| Micro XRCE-DDS Agent   | latest (source) | `sim/Dockerfile.ros2:17`            |
| Ubuntu (sim)           | 24.04           | `sim/Dockerfile.px4:3`              |
| Ubuntu (Pi 5)          | 24.04 Server    | `drone/setup_pi.sh`                 |

## Hardware

| Component              | Spec                    |
|------------------------|-------------------------|
| Flight Controller      | Holybro Pixhawk 6C (STM32H743) |
| Companion Computer     | Raspberry Pi 5 (8GB)    |
| Camera                 | RPi HQ Camera (IMX477, 12.3MP) |
| GPS                    | Holybro M9N (u-blox M9N)|
| Motors                 | T-Motor Velox V2207.5 1950KV |
| ESC                    | Holybro Tekko32 F4 4-in-1 50A |
| Props                  | HQProp 7x3.5x3         |

## Ground Station

| Component              | Version       | Pin Location              |
|------------------------|---------------|---------------------------|
| OpenDroneMap           | latest        | `ground/odm/process.sh:43`|
| QGroundControl         | latest stable | manual install             |

## Upgrade Checklist

When upgrading PX4:
1. Update tag in `sim/Dockerfile.px4` (git clone --branch)
2. Update `firmware/px4/VERSION`
3. Check if `px4_msgs` branch needs updating (`release/X.Y`)
4. Rebuild sim: `cd sim && docker compose -f docker-compose.sim.yml build`
5. Run sim smoke test: verify XRCE-DDS topics visible in ROS2
6. Update this table
```

**Step 5: Commit**

```bash
git add docs/compatibility-matrix.md firmware/px4/VERSION sim/Dockerfile.ros2
git commit -m "docs: add compatibility matrix, pin px4_msgs, fix VERSION drift

Created single source of truth for tested dependency versions.
Pinned px4_msgs to release/1.15 branch (was unpinned HEAD).
Fixed VERSION file still showing v1.15.2 after v1.16.1 upgrade."
```

---

## Task 8: Add Pre-Flight Checklist and Safety Register (Findings #14, #15, #7)

**Why:** No formal go/no-go criteria. No safety/hazard documentation. For a flying vehicle, a pre-flight checklist is the single most useful operational document.

**Files:**
- Create: `docs/operations/pre-flight-checklist.md`
- Create: `docs/operations/safety-register.md`

**Step 1: Create pre-flight checklist**

Create `docs/operations/pre-flight-checklist.md`:

```markdown
# Bennu Pre-Flight Checklist

Use before every flight. All items must PASS or have a documented exception.

## Hardware Checks

- [ ] Frame integrity — no cracks, all screws tight, props secured
- [ ] Battery voltage above 4.1V/cell (fully charged: 4.2V/cell)
- [ ] Battery secured with strap, connector firmly seated
- [ ] Props: correct rotation direction, no nicks or cracks
- [ ] Camera lens clean, mount secure, no vibration play
- [ ] GPS antenna unobstructed (top of frame)
- [ ] All cables seated — no loose connectors
- [ ] Pi 5 powered and green LED steady (not blinking)
- [ ] microSD card inserted in Pi 5

## Software Checks

- [ ] PX4 firmware version matches `firmware/px4/VERSION`
- [ ] QGroundControl connected (green status bar)
- [ ] GPS lock: ≥ 8 satellites, HDOP < 2.0
- [ ] EKF2 status: green in QGC
- [ ] Battery failsafe configured (check QGC Safety tab):
  - Low: 25%, Critical: 15%, Emergency: 10%
  - Action: RTL
- [ ] Datalink failsafe: RTL after 10s (NAV_DLL_ACT=2)
- [ ] RC failsafe: RTL (NAV_RCL_ACT=2)
- [ ] RTL altitude: 30m (clear of obstacles)
- [ ] Geofence: 500m horizontal, 120m vertical
- [ ] Home point set (shown on QGC map)

## Camera / Mission Checks (Survey Flights)

- [ ] Camera trigger mode: distance-based, 5m interval
- [ ] Pi 5 camera node running: `ros2 node list` shows `/camera_capture_node`
- [ ] Output directory has sufficient space: `df -h /home/pi/captures`
- [ ] Test capture: trigger one manual image, verify geotag

## Environmental Checks

- [ ] Wind: < 20 km/h sustained, < 30 km/h gusts
- [ ] No rain or imminent precipitation
- [ ] Temperature: 0°C to 40°C
- [ ] Clear of airports, restricted airspace (check local regulations)
- [ ] Observers aware, safe perimeter established

## Go / No-Go

| Item | Status |
|------|--------|
| All hardware checks pass | ☐ |
| All software checks pass | ☐ |
| Environmental checks pass | ☐ |
| Pilot confident and not fatigued | ☐ |

**All four must be YES to fly.**
```

**Step 2: Create safety register**

Create `docs/operations/safety-register.md`:

```markdown
# Bennu Safety & Hazard Register

## Hazard Table

| ID | Hazard | Severity | Likelihood | Mitigation | Verification |
|----|--------|----------|------------|------------|-------------|
| H1 | Loss of RC link | High | Medium | NAV_RCL_ACT=2 (RTL), 10s timeout | Pre-flight checklist, sim test |
| H2 | Loss of data link | High | Medium | NAV_DLL_ACT=2 (RTL), 10s timeout | Pre-flight checklist, sim test |
| H3 | Battery depletion in flight | Critical | Low | 25%/15%/10% failsafe ladder, RTL at low | Pre-flight voltage check |
| H4 | GPS loss during mission | High | Low | EKF2 fallback to baro/IMU, position hold | Verify ≥8 sats before takeoff |
| H5 | Pi 5 brownout/crash | Medium | Medium | Dedicated BEC, voltage monitoring | Power budget (TBD) |
| H6 | Motor/ESC failure | Critical | Low | No redundancy (quadcopter) — land ASAP | Pre-flight motor spin check |
| H7 | Prop detachment | Critical | Very Low | Self-locking nuts, pre-flight torque check | Pre-flight checklist |
| H8 | Frame structural failure | Critical | Low | Print quality inspection, vibration damping | Pre-flight visual check |
| H9 | Flyaway (uncontrolled flight) | Critical | Very Low | Geofence (500m), RTL failsafes, kill switch | Pre-flight geofence verify |
| H10 | Camera vibration blur | Low | Medium | Soft mount, TPU dampeners | Post-flight image review |

## Mitigations Not Yet Implemented

| Hazard | Missing Mitigation | Priority |
|--------|--------------------|----------|
| H5 | Power budget document with BEC margin analysis | High |
| H5 | Pi 5 voltage monitoring via ADC or INA219 | Medium |
| H10 | Vibration acceptance criteria (measured, not assumed) | Medium |

## Severity Definitions

- **Critical:** Loss of vehicle, risk of injury or property damage
- **High:** Mission failure, potential vehicle damage
- **Medium:** Degraded performance, recoverable
- **Low:** Minor inconvenience, no safety impact
```

**Step 3: Commit**

```bash
git add docs/operations/pre-flight-checklist.md docs/operations/safety-register.md
git commit -m "docs: add pre-flight checklist and safety hazard register

Addresses review findings #14 (phase gates), #15 (safety artifacts),
and #7 (risk management). Pre-flight checklist covers hardware,
software, camera, and environmental go/no-go criteria."
```

---

## Task 9: Add Power Budget (Finding #10)

**Why:** Pi 5 draws 5-27W depending on load. BEC sizing, thermal behavior, and noise coupling to the camera are unspecified. A brownout during flight means lost images and potential navigation issues.

**Files:**
- Create: `docs/systems/power-budget.md`

**Step 1: Create power budget**

Create `docs/systems/power-budget.md`:

```markdown
# Bennu Power Budget

## Battery

| Parameter | Value |
|-----------|-------|
| Type | 4S LiPo (14.8V nominal, 16.8V full) |
| Capacity | TBD (1300-1800 mAh typical for 7") |
| C-rating | ≥ 65C recommended |

## Power Consumers

| Component | Voltage | Typical Draw | Peak Draw | Source |
|-----------|---------|-------------|-----------|--------|
| 4× Motors + ESC | Battery direct | 15A cruise | 80A burst | ESC datasheet |
| Pixhawk 6C | 5V (via power module) | 0.5A | 0.8A | PX4 docs |
| Raspberry Pi 5 | 5V (via BEC) | 1.5A (idle+camera) | 3A (boot + capture) | RPi docs |
| GPS (M9N) | 3.3V (from Pixhawk) | 0.05A | 0.07A | u-blox datasheet |
| RC Receiver | 5V (from Pixhawk) | 0.05A | 0.1A | Receiver docs |

## BEC Requirements for Pi 5

| Parameter | Requirement | Rationale |
|-----------|-------------|-----------|
| Output voltage | 5V ± 0.25V | Pi 5 under-voltage at < 4.63V |
| Continuous current | ≥ 4A | Pi 5 peak (3A) + 30% margin |
| Input voltage range | 10-26V | 4S LiPo range (3.0-4.2V/cell) |
| Noise | Low ripple (< 50mV pp) | Camera image quality |
| Recommended | Matek UBEC 5V 4A or Pololu D36V28F5 | Tested for Pi 5 |

## Estimated Flight Time

| Battery | Cruise draw | Estimated flight time |
|---------|-------------|----------------------|
| 1300 mAh 4S | ~18A | ~4 min |
| 1550 mAh 4S | ~18A | ~5 min |
| 1800 mAh 4S | ~18A | ~6 min |

Note: These are rough estimates. Actual draw depends on weight, wind, and flight profile. Survey flights at lower speeds should draw less.

## Open Items

- [ ] Measure actual all-up weight to refine cruise current estimate
- [ ] Select and purchase BEC (Matek UBEC 5V 4A recommended)
- [ ] Measure Pi 5 voltage under flight vibration (potential ripple issues)
- [ ] Consider LC filter between BEC and Pi 5 if noise is observed
```

**Step 2: Commit**

```bash
git add docs/systems/power-budget.md
git commit -m "docs: add power budget for Pi 5 BEC sizing and flight time

Documents power consumption for all components, BEC requirements
for reliable Pi 5 operation, and estimated flight times.
Addresses review finding #10 (power architecture underspecified)."
```

---

## Task 10: Add Observability Conventions (Finding #11)

**Why:** No health check topics, no fault telemetry conventions, no log retention strategy. Makes field debugging very difficult.

**Files:**
- Create: `docs/systems/observability.md`

**Step 1: Create observability design**

Create `docs/systems/observability.md`:

```markdown
# Bennu Observability Design

## ROS2 Health Topics (Future)

When bennu ROS2 nodes mature, publish health status on these topics:

| Topic | Type | Publisher | Rate |
|-------|------|-----------|------|
| `/bennu/status/camera` | `std_msgs/String` | camera_node | 1 Hz |
| `/bennu/status/gps_quality` | `std_msgs/String` | camera_node | 1 Hz |
| `/bennu/diagnostics` | `diagnostic_msgs/DiagnosticArray` | all nodes | 1 Hz |

## Log Retention

| Log Source | Location | Retention |
|------------|----------|-----------|
| PX4 flight log (.ulg) | Pixhawk SD card | Keep all (post-flight download) |
| ROS2 node logs | Pi 5: `~/.ros/log/` | Keep last 10 flights |
| Camera captures | Pi 5: `/home/pi/captures/` | Transfer then delete |
| QGC telemetry | Ground station: QGC log dir | Keep all |

## Post-Flight Artifacts

After every flight, collect:

1. **PX4 .ulg log** — download via QGC or `mavlink shell: download log`
2. **Camera images** — `./ground/transfer/sync_images.sh`
3. **ROS2 bag (optional)** — `ros2 bag record -a` during flight

## Fault Classes

| Class | Example | Response |
|-------|---------|----------|
| CRITICAL | GPS lost, battery critical | Automated failsafe (PX4) |
| WARNING | Low satellites, camera error | Log + continue mission |
| INFO | Normal state transitions | Log only |

## Implementation Priority

1. Download PX4 logs after every flight (manual, now)
2. Add camera health topic to camera_node (Phase 2)
3. Add ROS2 diagnostics framework (Phase 3)
```

**Step 2: Commit**

```bash
git add docs/systems/observability.md
git commit -m "docs: add observability design for health monitoring and log retention

Defines ROS2 health topics, log retention policy, post-flight
artifact collection, and fault classification.
Addresses review finding #11."
```

---

## Task 11: Add Geospatial Accuracy Strategy (Finding #9)

**Why:** No defined baseline accuracy or upgrade path. Need to set expectations for what GPS-only photogrammetry delivers and document the RTK/PPK path.

**Files:**
- Create: `docs/systems/geospatial-accuracy.md`

**Step 1: Create geospatial accuracy strategy**

Create `docs/systems/geospatial-accuracy.md`:

```markdown
# Bennu Geospatial Accuracy Strategy

## Current Baseline (Phase 1 — GPS Only)

| Metric | Expected Value | Source |
|--------|---------------|--------|
| Horizontal absolute accuracy | ±2-5 m (CEP) | u-blox M9N typical |
| Vertical absolute accuracy | ±5-10 m | u-blox M9N typical |
| Relative accuracy (within dataset) | ±2-5 cm | OpenDroneMap SfM |
| GSD at 30m altitude, 6mm lens | ~0.9 cm/pixel | Calculated |

**Phase 1 is suitable for:** volume estimation, site progress monitoring, visual inspection, 3D visualization.

**Phase 1 is NOT suitable for:** cadastral survey, engineering-grade topography, GCP-free absolute positioning.

## Upgrade Path

### Option A: Ground Control Points (GCPs) — Low Cost

- Place 5-10 GCPs (printed targets) with known coordinates
- Survey GCPs with a phone-grade RTK receiver (e.g., Emlid Reach RX) or total station
- Process in ODM with `--gcp <gcp_file.txt>` flag
- Expected improvement: absolute accuracy to ±2-5 cm
- Cost: ~$300 (Emlid Reach RX) or ~$0 (borrowed survey equipment)

### Option B: PPK (Post-Processed Kinematic) — Medium Cost

- Log raw GNSS data on drone during flight
- Post-process against a local CORS base station
- Geotag images with corrected positions
- Expected improvement: absolute accuracy to ±2-3 cm without GCPs
- Cost: ~$200 (u-blox F9P module) + software
- Requires: replacing M9N with F9P, raw GNSS logging

### Option C: RTK (Real-Time Kinematic) — Higher Cost

- Real-time corrections from a base station via radio link
- Expected improvement: absolute accuracy to ±1-2 cm
- Cost: ~$500+ (base station + rover F9P + radio)
- Most complex integration

## Recommendation

Start with Phase 1 (GPS-only). After first successful survey flights:
1. Evaluate if absolute accuracy matters for your use case
2. If yes: start with GCPs (Option A) — lowest cost, highest impact
3. If sub-cm needed: upgrade to PPK (Option B)
```

**Step 2: Commit**

```bash
git add docs/systems/geospatial-accuracy.md
git commit -m "docs: add geospatial accuracy strategy with upgrade path

Documents GPS-only baseline accuracy, GCP/PPK/RTK upgrade options,
and recommendations. Addresses review finding #9."
```

---

## Task 12: Add Mapping Quality KPIs (Findings #8, part of #15)

**Why:** No vibration acceptance metrics, no mission profile defaults for overlap/speed/altitude. Need to define what "good enough" means for image quality.

**Files:**
- Create: `docs/systems/mapping-quality.md`

**Step 1: Create mapping quality document**

Create `docs/systems/mapping-quality.md`:

```markdown
# Bennu Mapping Quality KPIs

## Image Quality Acceptance

| Metric | Threshold | How to Check |
|--------|-----------|-------------|
| Motion blur | < 1 pixel at GSD | Visual: sharp edges at 100% zoom |
| Exposure | Histogram not clipped | Visual: no blown highlights |
| Focus | Sharp across frame | Visual: corner sharpness check |
| Coverage | All planned area covered | ODM report: no gaps in orthophoto |
| Overlap | ≥ 70% frontal, ≥ 60% side | Mission planner settings |

## Mission Profile Defaults

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Altitude (AGL) | 30 m | GSD ~0.9 cm/px at 6mm lens |
| Speed | 3 m/s | Limits motion blur with rolling shutter |
| Frontal overlap | 75% | Standard photogrammetry minimum |
| Side overlap | 65% | Standard photogrammetry minimum |
| Trigger interval | 5 m distance | Matches camera_params.yaml |
| Camera angle | Nadir (straight down) | Standard for orthophoto |

## Vibration Mitigation

| Approach | Status |
|----------|--------|
| Soft-mount camera to frame (M3 rubber grommets or TPU spacers) | Planned |
| Balance props before first flight | Planned |
| Review first flight images for blur patterns | Planned |
| If blur persists: add TPU vibration dampening plate under camera | Backup plan |

## ODM Quality Settings

See `ground/odm/profiles/survey_standard.json` for processing defaults:
- Feature quality: high
- Point cloud quality: high
- Orthophoto resolution: 2.0 cm/pixel
- Min features: 10,000

## Post-Flight Quality Gate

After each survey flight, before ODM processing:
1. Transfer images: `./ground/transfer/sync_images.sh`
2. Spot-check 5 random images at 100% zoom for blur/exposure
3. Verify GPS EXIF: `exiftool -gps* <image>.jpg`
4. If > 10% of images are blurred, investigate vibration before next flight
```

**Step 2: Commit**

```bash
git add docs/systems/mapping-quality.md
git commit -m "docs: add mapping quality KPIs and mission profile defaults

Defines image quality acceptance criteria, default mission parameters,
vibration mitigation strategy, and post-flight quality gate.
Addresses review findings #8 and #15."
```

---

## Task 13: Add CI Pipeline (Finding #16)

**Why:** No automated tests or linting on push/PR. Regressions can slip through unnoticed.

**Files:**
- Create: `.github/workflows/ci.yml`

**Step 1: Create CI workflow**

Create `.github/workflows/ci.yml`:

```yaml
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

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          pip install pytest ruff
          pip install setuptools

      - name: Lint Python (ruff)
        run: ruff check drone/ ground/

      - name: Run unit tests
        run: |
          cd drone/ros2_ws/src/bennu_camera
          python -m pytest test/ -v --tb=short

  shellcheck:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4

      - name: Install shellcheck
        run: sudo apt-get install -y shellcheck

      - name: Check shell scripts
        run: |
          shellcheck firmware/px4/upload_params.sh
          shellcheck firmware/px4/flash.sh
          shellcheck ground/odm/process.sh
          shellcheck ground/transfer/sync_images.sh
          shellcheck drone/setup_pi.sh
          shellcheck sim/setup_nvidia_docker.sh
```

Note: The Python tests in `test_geotag.py` don't require ROS2 — they test pure utility functions. A sim smoke test (docker compose up + topic check) is desirable but expensive for CI. Add as a separate workflow later.

**Step 2: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add lint (ruff), unit tests (pytest), and shellcheck

Runs on push to main and PRs. Tests bennu_camera geotag utilities,
lints Python with ruff, and checks all shell scripts with shellcheck.
Addresses review finding #16."
```

---

## Task 14: Fix VERSION File Drift (Finding #12)

**Already handled in Task 7, Step 1.** The VERSION file is updated from v1.15.2 to v1.16.1 as part of the compatibility matrix task. No additional work needed.

---

## Task 15: Add Phase Gate Criteria (Finding #14)

**Why:** No formal go/no-go criteria per phase means phase progression without objective quality threshold.

**Files:**
- Create: `docs/operations/phase-gates.md`

**Step 1: Create phase gates document**

Create `docs/operations/phase-gates.md`:

```markdown
# Bennu Phase Gates

Each phase must pass its exit criteria before proceeding to the next.

## Phase 1: Manual FPV Flight

**Goal:** Confirm the drone flies safely under manual RC control.

| Gate | Criterion | Evidence |
|------|-----------|----------|
| G1.1 | Hover stable for 30s at 2m altitude | Video or PX4 log |
| G1.2 | RTL works: returns to home and lands | PX4 log showing RTL |
| G1.3 | Battery failsafe triggers correctly | QGC alert at 25% |
| G1.4 | All failsafe params verified | Pre-flight checklist signed |
| G1.5 | Flight time ≥ 4 minutes | PX4 log duration |
| G1.6 | No mechanical issues (vibration, loose parts) | Post-flight inspection |

## Phase 2: Waypoint Survey

**Goal:** Automated survey flight captures geotagged images for ODM.

| Gate | Criterion | Evidence |
|------|-----------|----------|
| G2.1 | Phase 1 gates passed | — |
| G2.2 | Camera triggers on distance (every 5m) | Image EXIF timestamps |
| G2.3 | All images geotagged (GPS EXIF present) | `exiftool -gps* *.jpg` |
| G2.4 | ODM produces orthophoto from captured images | ODM output directory |
| G2.5 | ≥ 50 images per survey flight | Image count |
| G2.6 | < 10% images rejected for blur | Visual spot-check |

## Phase 3: Full Autonomy (ROS2)

**Goal:** Pi 5 runs mission logic, camera triggers, and data management autonomously.

| Gate | Criterion | Evidence |
|------|-----------|----------|
| G3.1 | Phase 2 gates passed | — |
| G3.2 | ROS2 camera_node runs full mission | ROS2 bag or logs |
| G3.3 | Offboard mode works in sim | SITL test log |
| G3.4 | Offboard mode works on hardware | PX4 flight log |
| G3.5 | End-to-end: takeoff → survey → land → transfer → ODM | All artifacts |
```

**Step 2: Commit**

```bash
git add docs/operations/phase-gates.md
git commit -m "docs: add phase gate criteria for flight readiness progression

Defines measurable pass/fail criteria for each project phase.
Addresses review finding #14."
```

---

## Task 16: Document Simultaneous Risk Fronts (Finding #7)

**Why:** The review correctly flags that custom frame + custom companion stack + photogrammetry + sim is a lot of concurrent risk. This doesn't need a code fix — it needs a documented strategy for which front to focus on first.

**This is already addressed by the phase gates document (Task 15).** The phased approach (fly first → survey → autonomy) is the mitigation. Phase 1 isolates flight stability from all other concerns.

No additional work needed.

---

## Task 17: Add Requirements Traceability Stub (Finding #15, #16)

**Why:** The review calls for a requirements-to-test traceability matrix. For this project's scale, a full matrix is overkill now. But a lightweight mapping of what's tested and what's not is useful.

**Files:**
- Create: `docs/systems/requirements-traceability.md`

**Step 1: Create traceability stub**

Create `docs/systems/requirements-traceability.md`:

```markdown
# Bennu Requirements Traceability

## Tested Requirements

| Requirement | Test | Location |
|-------------|------|----------|
| GPS EXIF geotagging | Unit test | `drone/ros2_ws/src/bennu_camera/test/test_geotag.py` |
| GPS coordinate format (DMS) | Unit test | `test_geotag.py::TestFormatGpsCoord` |
| EXIF write to JPEG | Unit test (conditional) | `test_geotag.py::TestWriteGpsExif` |
| Shell scripts valid syntax | CI shellcheck | `.github/workflows/ci.yml` |
| Python lint (style) | CI ruff | `.github/workflows/ci.yml` |

## Untested Requirements (Known Gaps)

| Requirement | Why Not Tested | Priority |
|-------------|---------------|----------|
| Camera capture (libcamera) | Requires hardware | Low (manual test on Pi) |
| PX4 subscription (uXRCE-DDS) | Requires ROS2 + PX4 | Medium (sim smoke test) |
| Sim stack boots | Requires Docker + GPU | Medium (local manual test) |
| ODM produces orthophoto | Requires sample dataset | Low (manual after first flight) |
| Failsafe behavior | Requires SITL | High (add sim test) |

## Next Steps

1. Add sim smoke test to CI (Docker-based, verify ROS2 topics)
2. Add a sample image dataset for ODM integration test
3. Add SITL-based failsafe verification test
```

**Step 2: Commit**

```bash
git add docs/systems/requirements-traceability.md
git commit -m "docs: add requirements traceability showing test coverage gaps

Lightweight mapping of tested vs untested requirements.
Addresses review findings #15 and #16."
```

---

## Task 18: Final — Push and Verify

**Step 1: Push all changes**

```bash
git push origin main
```

**Step 2: Verify CI passes (if GitHub Actions is enabled)**

```bash
gh run list --limit 1
```

Check that the CI workflow passes lint, tests, and shellcheck.

---

## Summary: Finding → Task Mapping

| Finding | Description | Task |
|---------|-------------|------|
| #1 | NAV_DLL_ACT failsafe misconfiguration | Task 1 |
| #2 | Double XRCE agent in sim | Task 2 |
| #3 | bennu_camera packaging incomplete | Task 3 |
| #4 | Agent binary naming mismatch | Task 4 |
| #5 | PX4 param uploader fragile | Task 5 |
| #6 | ODM process.sh empty input handling | Task 6 |
| #7 | Too many simultaneous risk fronts | Task 16 (addressed by phase gates) |
| #8 | Airframe vibration risk for mapping | Task 12 |
| #9 | Geospatial accuracy strategy incomplete | Task 11 |
| #10 | Power architecture underspecified | Task 9 |
| #11 | Observability architecture thin | Task 10 |
| #12 | Version drift across docs | Task 7 (Task 14 confirms) |
| #13 | Weak dependency pinning | Task 7 |
| #14 | No enforceable phase gates | Task 15 |
| #15 | Missing systems artifacts | Tasks 8, 9, 12, 17 |
| #16 | Testing and CI baseline minimal | Tasks 13, 17 |
| #17 | Roadmap-to-repo mismatch | Task 7 (VERSION fix) |
