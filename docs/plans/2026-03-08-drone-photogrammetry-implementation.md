# Bennu Drone Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a 3D-printed 7" quadcopter with PX4 + ROS2 that captures geotagged aerial photos for 3D reconstruction via OpenDroneMap.

**Architecture:** PX4 on Pixhawk 6C handles flight control. Raspberry Pi 5 runs ROS2 Humble with uXRCE-DDS for camera capture and geotagging. Ground station PC runs QGroundControl for mission planning and WebODM for photogrammetry processing. All config and code lives in a monorepo split by deployment target (drone/ vs ground/).

**Tech Stack:** PX4 v1.15+, ROS2 Humble, Python, libcamera, uXRCE-DDS, WebODM/OpenDroneMap, Docker, CF-PETG 3D printing

---

## Phase 1: Foundation — Repo, Config, and Frame

### Task 1: Initialize Git Repo and Directory Structure

**Type:** Software
**Files:**
- Create: `.gitignore`
- Create: `CLAUDE.md`
- Create: directory tree (all empty dirs with `.gitkeep`)

**Step 1: Initialize git repo**

```bash
cd /home/fadi/projects/bennu
git init
```

**Step 2: Create .gitignore**

```gitignore
# Build artifacts
drone/ros2_ws/build/
drone/ros2_ws/install/
drone/ros2_ws/log/
ground/ros2_ground_ws/build/
ground/ros2_ground_ws/install/
ground/ros2_ground_ws/log/

# Python
__pycache__/
*.pyc
*.pyo
*.egg-info/
.venv/

# Images captured during flights (too large for git)
ground/odm/datasets/
ground/odm/results/

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/

# Secrets
*.env
```

**Step 3: Create CLAUDE.md**

```markdown
# Bennu — DIY Photogrammetry Drone

## Project Overview
3D-printed 7" quadcopter for outdoor photogrammetry using PX4 + ROS2 + OpenDroneMap.

## Tech Stack
- **Flight Controller:** PX4 v1.15+ on Holybro Pixhawk 6C
- **Companion Computer:** Raspberry Pi 5 (8GB), Ubuntu 22.04, ROS2 Humble
- **PX4-ROS2 Bridge:** uXRCE-DDS (not MAVROS)
- **Camera:** Raspberry Pi HQ Camera (IMX477) + 6mm CS-mount lens
- **Ground Station:** QGroundControl + WebODM (Docker)
- **Language:** Python (ROS2 nodes), Bash (scripts)

## Repo Structure
- `drone/` — code that runs onboard the Pi 5
- `ground/` — code that runs on the ground station PC
- `firmware/` — PX4 parameter files and flash scripts
- `frame/` — 3D print files (STL/STEP)
- `config/` — shared config (camera calibration, network)
- `docs/` — build guides, wiring diagrams, plans

## ROS2 Conventions
- Package names: `bennu_*`
- Use `rclpy` (Python) for all nodes
- Launch files in `bennu_bringup`
- Node names: descriptive lowercase (e.g., `camera_capture_node`)

## Key Commands
- Build ROS2: `cd drone/ros2_ws && colcon build`
- Start WebODM: `cd ground/odm && docker compose up -d`
- Flash PX4 params: `./firmware/px4/upload_params.sh`
- Transfer images: `./ground/transfer/sync_images.sh`

## Design Doc
See `docs/plans/2026-03-08-drone-photogrammetry-design.md`
```

**Step 4: Create directory structure**

```bash
mkdir -p drone/ros2_ws/src
mkdir -p ground/odm/profiles
mkdir -p ground/transfer
mkdir -p ground/analysis
mkdir -p ground/ros2_ground_ws/src
mkdir -p frame/stl
mkdir -p frame/step
mkdir -p firmware/px4/params
mkdir -p firmware/mixer
mkdir -p config/camera_calibration
mkdir -p config/network
mkdir -p docs/plans
mkdir -p docs/wiring
mkdir -p docs/build-guide

# Add .gitkeep to empty dirs
find . -type d -empty -not -path './.git/*' -exec touch {}/.gitkeep \;
```

**Step 5: Move existing design doc**

The design doc already exists at `docs/plans/2026-03-08-drone-photogrammetry-design.md` — no action needed.

**Step 6: Commit**

```bash
git add -A
git commit -m "feat: initialize bennu repo with project structure and docs"
```

---

### Task 2: PX4 Base Parameter Files

**Type:** Software (firmware config)
**Files:**
- Create: `firmware/px4/params/base_params.yaml`
- Create: `firmware/px4/params/motor_params.yaml`
- Create: `firmware/px4/params/gps_params.yaml`
- Create: `firmware/px4/params/companion_params.yaml`
- Create: `firmware/px4/params/camera_params.yaml`
- Create: `firmware/px4/params/tuning_params.yaml`
- Create: `firmware/px4/VERSION`

**Step 1: Create base_params.yaml**

```yaml
# Base PX4 parameters for Bennu 7" quadcopter
# Apply first, before other param files
# Ref: https://docs.px4.io/main/en/config/

# Airframe: Generic Quadcopter X
SYS_AUTOSTART: 4001

# EKF2 configuration
EKF2_AID_MASK: 1          # GPS only
EKF2_HGT_REF: 1           # GPS height reference
EKF2_GPS_V_NOISE: 0.5
EKF2_GPS_P_NOISE: 0.5
EKF2_BARO_NOISE: 3.5

# Failsafes
COM_DL_LOSS_T: 10          # Data link loss timeout (seconds)
NAV_DLL_ACT: 0             # Data link loss action: return to launch
NAV_RCL_ACT: 2             # RC loss action: return to launch
COM_RCL_EXCEPT: 0          # No RC loss exceptions
RTL_RETURN_ALT: 30         # RTL altitude (meters)
RTL_DESCEND_ALT: 10        # RTL descend altitude
RTL_LAND_DELAY: 5          # Delay before landing at RTL (seconds)

# Battery failsafe
BAT_LOW_THR: 0.25          # Low battery warning at 25%
BAT_CRIT_THR: 0.15         # Critical at 15%
BAT_EMERGEN_THR: 0.10      # Emergency at 10%
COM_LOW_BAT_ACT: 2         # Low battery action: return to launch

# General
COM_ARM_WO_GPS: 0          # Require GPS to arm
COM_ARM_EKF_POS: 0.5       # EKF position error threshold for arming
```

**Step 2: Create motor_params.yaml**

```yaml
# Motor and ESC configuration for Bennu
# Motors: T-Motor Velox V2207.5 1950KV
# ESC: Holybro Tekko32 F4 4-in-1 50A
# Props: HQProp 7x3.5x3

# DShot protocol
DSHOT_CONFIG: 600           # DShot600

# Motor ordering (PX4 standard quad X)
# Motor 1: Front Right (CCW)
# Motor 2: Rear Left (CCW)
# Motor 3: Front Left (CW)
# Motor 4: Rear Right (CW)

# Idle throttle
MOT_ORDERING: 0            # PX4 default ordering
THR_MDL_FAC: 0.3           # Thrust model factor (tune after first flights)

# PWM limits (if using PWM instead of DShot)
PWM_MAIN_MIN: 1000
PWM_MAIN_MAX: 2000
```

**Step 3: Create gps_params.yaml**

```yaml
# GPS configuration for Bennu
# Module: Holybro M9N (u-blox M9N) with built-in compass

# GPS
GPS_1_CONFIG: 201           # GPS on UART port (GPS1)
GPS_1_PROTOCOL: 1           # u-blox protocol
GPS_1_GNSS: 7               # GPS + GLONASS + Galileo

# Compass (built into M9N)
CAL_MAG0_EN: 1              # Enable internal compass
CAL_MAG1_EN: 1              # Enable external compass (GPS module)
CAL_MAG_PRIME: 1            # Use external compass as primary
EKF2_MAG_TYPE: 1            # Automatic magnetometer selection

# Geofence (safety)
GF_ACTION: 1                # Geofence action: warning
GF_MAX_HOR_DIST: 500        # Max horizontal distance (meters)
GF_MAX_VER_DIST: 120        # Max vertical distance (meters)
```

**Step 4: Create companion_params.yaml**

```yaml
# Companion computer (Pi 5) connection via TELEM2
# Protocol: uXRCE-DDS over serial

# TELEM2 port config
MAV_1_CONFIG: 102            # TELEM2
SER_TEL2_BAUD: 921600        # 921600 baud for uXRCE-DDS
MAV_1_MODE: 2                # Onboard mode

# uXRCE-DDS client
UXRCE_DDS_CFG: 102           # Enable uXRCE-DDS on TELEM2
UXRCE_DDS_AG_IP: 0           # Not used for serial
```

**Step 5: Create camera_params.yaml**

```yaml
# Camera trigger configuration for Bennu
# Camera: Raspberry Pi HQ Camera triggered via companion computer

# Camera trigger
TRIG_INTERFACE: 3            # MAVLink trigger (sends to companion)
TRIG_MODE: 4                 # Distance-based trigger
TRIG_DIST: 5.0               # Trigger every 5 meters (adjust per mission)
TRIG_ACT_TIME: 0.5           # Trigger activation time (seconds)
TRIG_MIN_INTERVA: 1.0        # Minimum interval between triggers (seconds)

# Camera feedback
CAM_CAP_FBACK: 1             # Enable capture feedback
```

**Step 6: Create tuning_params.yaml**

```yaml
# PID tuning parameters for Bennu
# WARNING: These are STARTING VALUES. Must be tuned after maiden flight.
# Use PX4 autotune (MC_AT_START) or manual tuning.

# Rate controller (inner loop)
MC_ROLLRATE_P: 0.15
MC_ROLLRATE_I: 0.2
MC_ROLLRATE_D: 0.003
MC_PITCHRATE_P: 0.15
MC_PITCHRATE_I: 0.2
MC_PITCHRATE_D: 0.003
MC_YAWRATE_P: 0.2
MC_YAWRATE_I: 0.1
MC_YAWRATE_D: 0.0

# Attitude controller (outer loop)
MC_ROLL_P: 6.5
MC_PITCH_P: 6.5
MC_YAW_P: 2.8

# Position controller
MPC_XY_P: 0.95
MPC_Z_P: 1.0
MPC_XY_VEL_P_ACC: 1.8
MPC_Z_VEL_P_ACC: 4.0

# Speed limits (conservative for survey)
MPC_XY_CRUISE: 5.0           # Cruise speed 5 m/s (good for photogrammetry)
MPC_XY_VEL_MAX: 8.0          # Max horizontal speed
MPC_Z_VEL_MAX_UP: 3.0        # Max ascent speed
MPC_Z_VEL_MAX_DN: 1.5        # Max descent speed
MPC_TILTMAX_AIR: 35          # Max tilt angle (degrees)

# Autotune (enable for first tuning session)
MC_AT_START: 0                # Set to 1 to start autotune in flight
```

**Step 7: Create VERSION file**

```
PX4_VERSION=v1.15.2
BOARD_TARGET=holybro_pixhawk6c
LAST_FLASH_DATE=
NOTES=Initial setup, not yet flashed
```

**Step 8: Commit**

```bash
git add firmware/
git commit -m "feat: add PX4 parameter files for Pixhawk 6C configuration"
```

---

### Task 3: PX4 Flash and Upload Scripts

**Type:** Software
**Files:**
- Create: `firmware/px4/flash.sh`
- Create: `firmware/px4/upload_params.sh`

**Step 1: Create flash.sh**

```bash
#!/usr/bin/env bash
# Flash PX4 firmware to Holybro Pixhawk 6C
# Usage: ./firmware/px4/flash.sh [firmware_file.px4]
#
# If no firmware file provided, downloads the latest stable release
# for the holybro_pixhawk6c target.
#
# Prerequisites:
#   pip install pyserial
#   PX4-Autopilot repo cloned (for px_uploader.py) OR use QGroundControl

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION_FILE="$SCRIPT_DIR/VERSION"
BOARD="holybro_pixhawk6c"

# Read target version
PX4_VERSION=$(grep PX4_VERSION "$VERSION_FILE" | cut -d= -f2)

FIRMWARE_FILE="${1:-}"

if [ -z "$FIRMWARE_FILE" ]; then
    echo "Downloading PX4 $PX4_VERSION for $BOARD..."
    FIRMWARE_FILE="/tmp/px4_${BOARD}_${PX4_VERSION}.px4"
    curl -L -o "$FIRMWARE_FILE" \
        "https://github.com/PX4/PX4-Autopilot/releases/download/${PX4_VERSION}/${BOARD}.px4"
    echo "Downloaded to $FIRMWARE_FILE"
fi

echo ""
echo "=== Flash Instructions ==="
echo ""
echo "Option A: QGroundControl (recommended for first-time)"
echo "  1. Open QGroundControl"
echo "  2. Go to Vehicle Setup > Firmware"
echo "  3. Connect Pixhawk via USB"
echo "  4. Select PX4 Flight Stack > $PX4_VERSION"
echo "  5. Wait for flash to complete"
echo ""
echo "Option B: Command line (px_uploader.py)"
echo "  1. Connect Pixhawk via USB"
echo "  2. Run: python3 px_uploader.py --port /dev/ttyACM0 $FIRMWARE_FILE"
echo ""
echo "After flashing, update $VERSION_FILE with the flash date."
```

**Step 2: Create upload_params.sh**

```bash
#!/usr/bin/env bash
# Upload PX4 parameters to Pixhawk 6C via MAVLink
# Usage: ./firmware/px4/upload_params.sh [param_file.yaml ...]
#
# If no files specified, uploads all param files in order.
#
# Prerequisites:
#   pip install pymavlink mavsdk
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

echo "Uploading PX4 parameters via $PORT at $BAUD baud"
echo ""

for param_file in "${PARAM_FILES[@]}"; do
    filepath="$PARAMS_DIR/$param_file"
    if [ ! -f "$filepath" ]; then
        filepath="$param_file"  # Try as absolute/relative path
    fi

    if [ ! -f "$filepath" ]; then
        echo "WARNING: $param_file not found, skipping"
        continue
    fi

    echo "--- Applying: $param_file ---"

    # Parse YAML and set each parameter via mavlink shell
    # Format: PARAM_NAME: value  or  PARAM_NAME: value  # comment
    grep -v '^#' "$filepath" | grep -v '^$' | while IFS=': ' read -r param value rest; do
        # Strip trailing comments
        value=$(echo "$value" | sed 's/#.*//' | xargs)
        if [ -n "$param" ] && [ -n "$value" ]; then
            echo "  SET $param = $value"
            # Using mavlink shell via pymavlink
            python3 -c "
import sys
from pymavlink import mavutil
master = mavutil.mavlink_connection('$PORT', baud=$BAUD)
master.wait_heartbeat()
master.param_set_send('$param', float('$value'))
ack = master.recv_match(type='PARAM_VALUE', blocking=True, timeout=5)
if ack:
    print(f'    OK: {ack.param_id} = {ack.param_value}')
else:
    print(f'    TIMEOUT: $param', file=sys.stderr)
" 2>&1 || echo "    FAILED: $param"
        fi
    done
    echo ""
done

echo "Done. Reboot the flight controller to apply all changes."
echo "  mavlink shell: reboot"
echo "  or: power cycle the Pixhawk"
```

**Step 3: Make scripts executable and commit**

```bash
chmod +x firmware/px4/flash.sh firmware/px4/upload_params.sh
git add firmware/
git commit -m "feat: add PX4 flash and parameter upload scripts"
```

---

### Task 4: 3D Frame Documentation

**Type:** Hardware documentation
**Files:**
- Create: `frame/README.md`
- Create: `docs/build-guide/01-frame-assembly.md`

**Step 1: Create frame/README.md**

```markdown
# Bennu Drone Frame — 7" Quadcopter

## Specifications

- **Prop size:** 7 inch (HQProp 7x3.5x3)
- **Motor-to-motor diagonal:** ~300mm
- **Material:** CF-PETG (carbon fiber reinforced PETG)
- **Arms:** 10mm OD carbon fiber tubes (NOT 3D printed)
- **Fits print bed:** 235×235mm (AnkerMake M5C)

## Design Approach

The frame is a hybrid design:
- **3D-printed body** (center plates, motor mounts, canopy, camera mount, GPS mast base)
- **Carbon fiber tube arms** (10mm OD, ~5mm wall) for strength and vibration damping

## Parts List (printed)

| Part | Qty | Est. Print Time | Notes |
|------|-----|----------------|-------|
| Bottom plate | 1 | ~3h | Battery mount, ESC mount |
| Top plate | 1 | ~2h | Pi 5 mount (M2.5 holes), FC mount |
| Motor mount | 4 | ~30min each | Press-fit onto CF tubes |
| Arm clamp | 4 | ~20min each | Secures CF tubes to body |
| GPS mast base | 1 | ~30min | Holds 12mm CF tube vertical |
| Camera mount | 1 | ~1h | Bottom-mount, 15° forward tilt |
| Canopy | 1 | ~2h | Protects FC + Pi + wiring |
| Landing legs | 4 | ~20min each | Simple clip-on legs |

## Non-printed Parts

| Part | Qty | Notes |
|------|-----|-------|
| CF tube 10mm OD × 200mm | 4 | Drone arms |
| CF tube 12mm OD × 150mm | 1 | GPS mast |
| M3×8 button head screws | 20 | Frame assembly |
| M3 press-fit inserts | 20 | Heat-set into prints |
| M2.5×6 screws | 4 | Pi 5 mounting |
| M2.5 standoffs 10mm | 4 | FC vibration mount |
| Vibration dampening balls | 4 | FC soft mount |

## Print Settings

- **Material:** CF-PETG (e.g., Polymaker PolyLite CF-PETG)
- **Nozzle:** 0.4mm hardened steel (CF wears brass nozzles)
- **Layer height:** 0.2mm
- **Perimeters:** 3-4
- **Infill:** 30-40% gyroid
- **Bed temp:** 80°C
- **Nozzle temp:** 240-250°C

## CAD Files

- `step/` — Editable STEP files (open in FreeCAD or Fusion 360)
- `stl/` — Print-ready STL files
```

**Step 2: Create docs/build-guide/01-frame-assembly.md**

```markdown
# Build Guide — Step 1: Frame Assembly

## Prerequisites

- All frame parts 3D printed (see frame/README.md)
- Carbon fiber tubes cut to length
- M3 heat-set inserts installed in printed parts
- Tools: hex drivers, soldering iron (for heat-set inserts), CA glue

## Assembly Order

### 1. Install Heat-Set Inserts

Install M3 heat-set inserts into all screw holes on the bottom plate, top plate,
and arm clamps. Use a soldering iron at 220°C, press straight in.

### 2. Assemble Arms

1. Slide CF tube arms through the bottom plate channels
2. Attach arm clamps on both sides of each arm
3. Tighten M3 screws — snug, not overtight (CF cracks)
4. Attach motor mounts to the ends of each arm

### 3. Mount ESC

1. Place 4-in-1 ESC on bottom plate
2. Secure with M3 screws or double-sided tape
3. Route motor wires through arm channels

### 4. Mount Flight Controller

1. Attach vibration dampening balls to M2.5 standoffs
2. Secure FC mount standoffs to top plate
3. Place Pixhawk 6C on standoffs, secure with rubber grommets
4. Arrow on FC pointing forward

### 5. GPS Mast

1. Insert 12mm CF tube into GPS mast base
2. Secure with set screw or CA glue
3. Mount M9N GPS module on top with double-sided tape
4. Route GPS cable down the mast, secure with zip ties

### 6. Camera Mount

1. Attach camera mount bracket to bottom plate (15° forward tilt)
2. Pi HQ Camera module mounts with M2 screws
3. Route CSI ribbon cable up through the frame to Pi location

### 7. Stack Top Plate

1. Place top plate over standoffs
2. Secure with M3 screws
3. Pi 5 mounts on top plate with M2.5 standoffs

### 8. Landing Gear

1. Clip landing legs onto bottom plate corners
2. Verify clearance for camera underneath

## Weight Target

| Component | Weight |
|-----------|--------|
| Frame (printed + CF) | ~180g |
| Motors (×4) | ~120g |
| ESC 4-in-1 | ~30g |
| Pixhawk 6C | ~40g |
| GPS M9N | ~25g |
| Pi 5 + camera | ~100g |
| Battery 4S 2200mAh | ~220g |
| Wiring, props, misc | ~80g |
| **Total AUW** | **~795g** |

Target AUW under 900g for good flight efficiency on 7" props.
```

**Step 3: Commit**

```bash
git add frame/ docs/build-guide/
git commit -m "feat: add frame specs, print settings, and assembly guide"
```

---

## Phase 1 Continued: Hardware Build (Non-Software Tasks)

### Task 5: Order Parts and Print Frame

**Type:** Hardware (manual — not automatable)

**Checklist:**

- [ ] Order: Holybro Pixhawk 6C kit (includes PM02, buzzer, safety switch)
- [ ] Order: Holybro Tekko32 F4 4-in-1 50A ESC
- [ ] Order: T-Motor Velox V2207.5 1950KV × 4
- [ ] Order: HQProp 7×3.5×3 tri-blade × 8 (spares)
- [ ] Order: Holybro M9N GPS
- [ ] Order: ELRS 900MHz receiver + antenna
- [ ] Order: RadioMaster TX16S (if needed) + ELRS TX module
- [ ] Order: Holybro SiK Radio V3 telemetry pair
- [ ] Order: 4S 2200mAh LiPo × 2
- [ ] Order: LiPo charger (if needed)
- [ ] Order: XT60 connectors, silicone wire (14AWG, 18AWG), JST-GH connectors
- [ ] Order: 10mm OD CF tubes × 4 (200mm) + 12mm × 1 (150mm)
- [ ] Order: M3 heat-set inserts × 20, M3×8 screws, M2.5 hardware
- [ ] Order: CF-PETG filament (e.g., Polymaker)
- [ ] Order: Hardened steel 0.4mm nozzle for AnkerMake M5C
- [ ] Order: Raspberry Pi 5 (8GB) + 64GB microSD
- [ ] Order: Pi HQ Camera + 6mm CS-mount lens
- [ ] Order: BEC 5V 3A (Matek or Pololu)
- [ ] Print: All frame parts per frame/README.md
- [ ] Install: Heat-set inserts
- [ ] Cut: CF tubes to length

---

### Task 6: Wiring Diagram

**Type:** Documentation
**Files:**
- Create: `docs/wiring/wiring-diagram.md`

**Step 1: Create wiring-diagram.md**

```markdown
# Bennu Wiring Diagram

## Power Distribution

```
Battery (4S LiPo, XT60)
  │
  ├──► PM02 Power Module ──► Pixhawk 6C (POWER1 port)
  │         │
  │         └──► Voltage + Current sense to FC
  │
  ├──► ESC 4-in-1 (battery pads)
  │         │
  │         ├──► Motor 1 (Front Right)
  │         ├──► Motor 2 (Rear Left)
  │         ├──► Motor 3 (Front Left)
  │         └──► Motor 4 (Rear Right)
  │
  └──► BEC 5V 3A ──► Raspberry Pi 5 (GPIO 5V + GND pins 2,4,6)
```

## Signal Connections

```
Pixhawk 6C
  │
  ├── MAIN OUT 1-4 ──► ESC signal pads (DShot600)
  │
  ├── GPS1 (UART) ──► Holybro M9N GPS (JST-GH cable)
  │
  ├── TELEM1 ──► SiK Radio V3 (telemetry to ground station)
  │
  ├── TELEM2 ──► Raspberry Pi 5 UART
  │                TX (FC) ──► RX (Pi GPIO 15 / pin 10)
  │                RX (FC) ──► TX (Pi GPIO 14 / pin 8)
  │                GND ──► GND (Pi pin 6)
  │                (DO NOT connect 5V from TELEM2 — Pi powered by BEC)
  │
  ├── RC IN ──► ELRS 900MHz receiver (SBUS/CRSF)
  │
  └── I2C ──► (reserved for future sensors)

Raspberry Pi 5
  │
  ├── CSI connector ──► Pi HQ Camera (ribbon cable)
  │
  ├── GPIO 14/15 (UART) ──► Pixhawk TELEM2 (see above)
  │
  ├── USB-A ──► (optional: USB WiFi dongle for longer range)
  │
  └── microSD ──► 64GB card (image storage)
```

## Important Notes

1. **Cross-wire UART:** FC TX → Pi RX, FC RX → Pi TX
2. **Do NOT power Pi from TELEM2** — use dedicated BEC for clean 5V
3. **GPS mast height:** Mount GPS 10+ cm above electronics to reduce magnetic interference
4. **Motor direction:** Verify motor spin direction matches PX4 quad X layout before props on
5. **ESC signal ground:** Ensure ESC signal ground is common with FC ground
```

**Step 2: Commit**

```bash
git add docs/wiring/
git commit -m "feat: add wiring diagram for all electrical connections"
```

---

### Task 7: Assemble and Flash (Hardware + Software)

**Type:** Hardware + Software (manual steps with software verification)

**Step 1: Physical assembly**

Follow `docs/build-guide/01-frame-assembly.md` — assemble frame, solder ESC, mount motors, wire everything per `docs/wiring/wiring-diagram.md`.

**Step 2: Flash PX4 via QGroundControl**

1. Install QGroundControl on PC
2. Connect Pixhawk 6C via USB
3. QGC auto-detects and prompts for firmware
4. Select PX4 Pro Stable → flash
5. Update `firmware/px4/VERSION` with flash date

**Step 3: Upload parameters**

```bash
./firmware/px4/upload_params.sh
```

Or manually in QGC: Vehicle Setup → Parameters → Import from file.

**Step 4: Calibrate sensors in QGC**

1. Accelerometer calibration (6 orientations)
2. Gyroscope calibration
3. Magnetometer calibration (rotate drone)
4. Radio calibration (bind RC, calibrate sticks)
5. ESC calibration
6. Level horizon calibration

**Step 5: Motor test**

In QGC: Vehicle Setup → Motors → test each motor individually (NO PROPS).
Verify correct spin direction per PX4 quad X layout.

**Step 6: Maiden flight checklist**

- [ ] Props OFF — arm and verify motor spin
- [ ] Props ON — outdoor, open area, no wind
- [ ] Take off in Stabilize mode, hover at 2m
- [ ] Test roll, pitch, yaw response
- [ ] Test Position mode (GPS lock required)
- [ ] Test RTL (Return to Launch)
- [ ] Land, review flight log in QGC
- [ ] Run PX4 autotune if needed (set `MC_AT_START: 1`)
- [ ] Update `firmware/px4/params/tuning_params.yaml` with tuned PIDs
- [ ] Commit updated params

**Step 7: Commit tuned params**

```bash
git add firmware/px4/params/tuning_params.yaml firmware/px4/VERSION
git commit -m "feat: update PID tuning params after maiden flight"
```

---

## Phase 2: Survey — Camera + Waypoints + ODM

### Task 8: Pi 5 Base Setup Script

**Type:** Software
**Files:**
- Create: `drone/setup_pi.sh`

**Step 1: Create setup_pi.sh**

```bash
#!/usr/bin/env bash
# Set up Raspberry Pi 5 for Bennu drone companion computer
# Run on a fresh Ubuntu 22.04 Server install on the Pi 5
#
# Prerequisites:
#   - Ubuntu 22.04 Server flashed to microSD
#   - Pi 5 connected to internet via Ethernet or WiFi
#   - SSH access configured
#
# Usage: ssh pi@<ip> 'bash -s' < drone/setup_pi.sh

set -euo pipefail

echo "=== Bennu Pi 5 Setup ==="

# Update system
sudo apt update && sudo apt upgrade -y

# Install base dependencies
sudo apt install -y \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    htop \
    libcamera-apps \
    libcamera-dev \
    python3-libcamera \
    python3-picamera2 \
    exiftool

# Install ROS 2 Humble
echo "=== Installing ROS 2 Humble ==="
sudo apt install -y software-properties-common
sudo add-apt-repository universe -y
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
    -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
    | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
sudo apt update
sudo apt install -y ros-humble-ros-base ros-dev-tools

# Source ROS 2 in bashrc
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc

# Install Micro XRCE-DDS Agent
echo "=== Installing Micro XRCE-DDS Agent ==="
sudo snap install micro-xrce-dds-agent

# Enable UART for PX4 communication
echo "=== Configuring UART ==="
# Disable serial console on UART (needed for PX4 comms)
sudo systemctl disable serial-getty@ttyAMA0.service 2>/dev/null || true
# Add user to dialout group for UART access
sudo usermod -aG dialout $USER

# Create workspace directory
mkdir -p ~/bennu_ws/src

echo ""
echo "=== Setup Complete ==="
echo "Reboot required: sudo reboot"
echo "After reboot, verify:"
echo "  ros2 --version"
echo "  libcamera-hello --list-cameras"
echo "  micro-xrce-dds-agent --version"
```

**Step 2: Make executable and commit**

```bash
chmod +x drone/setup_pi.sh
git add drone/setup_pi.sh
git commit -m "feat: add Pi 5 setup script with ROS2 Humble and dependencies"
```

---

### Task 9: ROS2 Camera Capture Package — bennu_camera

**Type:** Software
**Files:**
- Create: `drone/ros2_ws/src/bennu_camera/package.xml`
- Create: `drone/ros2_ws/src/bennu_camera/setup.py`
- Create: `drone/ros2_ws/src/bennu_camera/setup.cfg`
- Create: `drone/ros2_ws/src/bennu_camera/bennu_camera/__init__.py`
- Create: `drone/ros2_ws/src/bennu_camera/bennu_camera/camera_node.py`
- Create: `drone/ros2_ws/src/bennu_camera/test/test_geotag.py`

**Step 1: Create package.xml**

```xml
<?xml version="1.0"?>
<package format="3">
  <name>bennu_camera</name>
  <version>0.1.0</version>
  <description>Camera capture and geotagging for Bennu drone</description>
  <maintainer email="you@example.com">Bennu</maintainer>
  <license>MIT</license>

  <buildtool_depend>ament_python</buildtool_depend>

  <exec_depend>rclpy</exec_depend>
  <exec_depend>std_msgs</exec_depend>
  <exec_depend>sensor_msgs</exec_depend>
  <exec_depend>px4_msgs</exec_depend>

  <test_depend>ament_copyright</test_depend>
  <test_depend>ament_pep257</test_depend>
  <test_depend>python3-pytest</test_depend>
</package>
```

**Step 2: Create setup.py**

```python
from setuptools import setup

package_name = "bennu_camera"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Bennu",
    maintainer_email="you@example.com",
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

**Step 3: Create setup.cfg**

```ini
[develop]
script_dir=$base/lib/bennu_camera

[install]
install_scripts=$base/lib/bennu_camera
```

**Step 4: Create __init__.py**

```python
```

**Step 5: Write the test first (test_geotag.py)**

```python
"""Tests for geotagging utility functions."""
import os
import tempfile
import pytest

from bennu_camera.camera_node import write_gps_exif, format_gps_coord


class TestFormatGpsCoord:
    def test_positive_latitude(self):
        # 37.7749° N
        degrees, minutes, seconds, ref = format_gps_coord(37.7749, is_lat=True)
        assert ref == "N"
        assert degrees == 37
        assert minutes == 46
        assert 29.0 < seconds < 30.0

    def test_negative_latitude(self):
        # -33.8688° S
        degrees, minutes, seconds, ref = format_gps_coord(-33.8688, is_lat=True)
        assert ref == "S"
        assert degrees == 33

    def test_positive_longitude(self):
        # 122.4194° W is negative, but 2.3522° E is positive
        degrees, minutes, seconds, ref = format_gps_coord(2.3522, is_lat=False)
        assert ref == "E"
        assert degrees == 2

    def test_negative_longitude(self):
        degrees, minutes, seconds, ref = format_gps_coord(-122.4194, is_lat=False)
        assert ref == "W"
        assert degrees == 122

    def test_zero(self):
        degrees, minutes, seconds, ref = format_gps_coord(0.0, is_lat=True)
        assert degrees == 0
        assert minutes == 0
        assert ref == "N"


class TestWriteGpsExif:
    def test_writes_exif_to_jpeg(self):
        """Create a minimal JPEG, write GPS EXIF, verify it was written."""
        # Create a minimal valid JPEG (1x1 pixel)
        import struct
        # Minimal JPEG: SOI + APP0 + DQT + SOF0 + DHT + SOS + image data + EOI
        # For testing, we'll create a temp file and check exiftool output
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            # Minimal JPEG file (1x1 white pixel)
            f.write(bytes([
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
                0x00, 0x7B, 0x40, 0x1B, 0xFF, 0xD9
            ]))
            temp_path = f.name

        try:
            result = write_gps_exif(temp_path, 37.7749, -122.4194, 50.0)
            assert result is True

            # Verify with exiftool if available
            import subprocess
            try:
                output = subprocess.check_output(
                    ["exiftool", "-GPSLatitude", "-GPSLongitude", "-n", temp_path],
                    text=True
                )
                assert "37.77" in output
                assert "122.41" in output
            except FileNotFoundError:
                # exiftool not installed, skip verification
                pass
        finally:
            os.unlink(temp_path)
```

**Step 6: Run test to verify it fails**

```bash
cd drone/ros2_ws/src/bennu_camera
python3 -m pytest test/test_geotag.py -v
```

Expected: FAIL — `ImportError: cannot import name 'write_gps_exif' from 'bennu_camera.camera_node'`

**Step 7: Implement camera_node.py**

```python
"""
Bennu Camera Node — captures geotagged images triggered by PX4.

Subscribes to PX4 camera trigger events via uXRCE-DDS,
captures images using libcamera, and writes GPS EXIF data.
"""
import os
import subprocess
import time
from datetime import datetime
from typing import Tuple

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy


def format_gps_coord(
    decimal_degrees: float, is_lat: bool
) -> Tuple[int, int, float, str]:
    """Convert decimal degrees to (degrees, minutes, seconds, ref)."""
    if is_lat:
        ref = "N" if decimal_degrees >= 0 else "S"
    else:
        ref = "E" if decimal_degrees >= 0 else "W"

    decimal_degrees = abs(decimal_degrees)
    degrees = int(decimal_degrees)
    minutes_float = (decimal_degrees - degrees) * 60
    minutes = int(minutes_float)
    seconds = (minutes_float - minutes) * 60

    return degrees, minutes, seconds, ref


def write_gps_exif(
    image_path: str, lat: float, lon: float, alt: float
) -> bool:
    """Write GPS coordinates into JPEG EXIF data using exiftool."""
    try:
        subprocess.run(
            [
                "exiftool",
                "-overwrite_original",
                f"-GPSLatitude={lat}",
                f"-GPSLongitude={lon}",
                f"-GPSAltitude={alt}",
                f"-GPSLatitudeRef={'N' if lat >= 0 else 'S'}",
                f"-GPSLongitudeRef={'E' if lon >= 0 else 'W'}",
                "-GPSAltitudeRef=0",
                image_path,
            ],
            check=True,
            capture_output=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


class CameraNode(Node):
    """ROS2 node that captures geotagged images on PX4 camera trigger."""

    def __init__(self):
        super().__init__("camera_capture_node")

        # Parameters
        self.declare_parameter("output_dir", "/home/pi/captures")
        self.declare_parameter("image_width", 4056)
        self.declare_parameter("image_height", 3040)

        self.output_dir = self.get_parameter("output_dir").value
        self.width = self.get_parameter("image_width").value
        self.height = self.get_parameter("image_height").value

        os.makedirs(self.output_dir, exist_ok=True)

        # Latest GPS position (updated continuously)
        self._lat = 0.0
        self._lon = 0.0
        self._alt = 0.0

        # QoS for PX4 topics
        qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=5,
        )

        # Subscribe to PX4 vehicle GPS position
        try:
            from px4_msgs.msg import VehicleGlobalPosition, CameraTrigger

            self.create_subscription(
                VehicleGlobalPosition,
                "/fmu/out/vehicle_global_position",
                self._on_gps,
                qos,
            )

            self.create_subscription(
                CameraTrigger,
                "/fmu/out/camera_trigger",
                self._on_trigger,
                qos,
            )
            self.get_logger().info("Subscribed to PX4 topics via uXRCE-DDS")
        except ImportError:
            self.get_logger().warn(
                "px4_msgs not found — running in standalone timer mode"
            )
            # Fallback: capture on timer (for testing without PX4)
            self.create_timer(5.0, self._on_timer_capture)

        self._capture_count = 0
        self.get_logger().info(
            f"Camera node started. Output: {self.output_dir}"
        )

    def _on_gps(self, msg):
        """Update latest GPS position from PX4."""
        self._lat = msg.lat
        self._lon = msg.lon
        self._alt = msg.alt

    def _on_trigger(self, msg):
        """PX4 camera trigger event — capture and geotag."""
        self.get_logger().info(
            f"Trigger #{msg.seq} at ({self._lat:.6f}, {self._lon:.6f}, {self._alt:.1f}m)"
        )
        self._capture_image()

    def _on_timer_capture(self):
        """Fallback timer-based capture for testing."""
        self._capture_image()

    def _capture_image(self):
        """Capture image with libcamera and write GPS EXIF."""
        self._capture_count += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bennu_{timestamp}_{self._capture_count:04d}.jpg"
        filepath = os.path.join(self.output_dir, filename)

        try:
            subprocess.run(
                [
                    "libcamera-still",
                    "-o", filepath,
                    "--width", str(self.width),
                    "--height", str(self.height),
                    "--nopreview",
                    "-t", "1",  # minimal timeout
                ],
                check=True,
                capture_output=True,
                timeout=10,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            self.get_logger().error(f"Capture failed: {e}")
            return

        # Write GPS EXIF
        if self._lat != 0.0 or self._lon != 0.0:
            success = write_gps_exif(filepath, self._lat, self._lon, self._alt)
            if success:
                self.get_logger().info(f"Saved: {filename} (geotagged)")
            else:
                self.get_logger().warn(f"Saved: {filename} (geotag failed)")
        else:
            self.get_logger().warn(f"Saved: {filename} (no GPS fix)")


def main(args=None):
    rclpy.init(args=args)
    node = CameraNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
```

**Step 8: Run tests**

```bash
cd drone/ros2_ws/src/bennu_camera
python3 -m pytest test/test_geotag.py -v
```

Expected: PASS (at least the format_gps_coord tests; write_gps_exif depends on exiftool)

**Step 9: Commit**

```bash
git add drone/ros2_ws/src/bennu_camera/
git commit -m "feat: add bennu_camera ROS2 package with geotagged capture"
```

---

### Task 10: ROS2 Bringup Package — bennu_bringup

**Type:** Software
**Files:**
- Create: `drone/ros2_ws/src/bennu_bringup/package.xml`
- Create: `drone/ros2_ws/src/bennu_bringup/setup.py`
- Create: `drone/ros2_ws/src/bennu_bringup/setup.cfg`
- Create: `drone/ros2_ws/src/bennu_bringup/bennu_bringup/__init__.py`
- Create: `drone/ros2_ws/src/bennu_bringup/launch/drone.launch.py`
- Create: `drone/ros2_ws/src/bennu_bringup/config/camera_params.yaml`

**Step 1: Create package.xml**

```xml
<?xml version="1.0"?>
<package format="3">
  <name>bennu_bringup</name>
  <version>0.1.0</version>
  <description>Launch files and config for Bennu drone</description>
  <maintainer email="you@example.com">Bennu</maintainer>
  <license>MIT</license>

  <buildtool_depend>ament_python</buildtool_depend>

  <exec_depend>rclpy</exec_depend>
  <exec_depend>bennu_camera</exec_depend>
  <exec_depend>launch</exec_depend>
  <exec_depend>launch_ros</exec_depend>
</package>
```

**Step 2: Create setup.py**

```python
import os
from glob import glob
from setuptools import setup

package_name = "bennu_bringup"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.py")),
        (os.path.join("share", package_name, "config"), glob("config/*.yaml")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Bennu",
    maintainer_email="you@example.com",
    description="Launch files and config for Bennu drone",
    license="MIT",
    entry_points={},
)
```

**Step 3: Create setup.cfg**

```ini
[develop]
script_dir=$base/lib/bennu_bringup

[install]
install_scripts=$base/lib/bennu_bringup
```

**Step 4: Create __init__.py and resource marker**

```bash
mkdir -p drone/ros2_ws/src/bennu_bringup/resource
touch drone/ros2_ws/src/bennu_bringup/resource/bennu_bringup
```

```python
# bennu_bringup/__init__.py
```

**Step 5: Create launch/drone.launch.py**

```python
"""Launch file for Bennu drone companion computer.

Starts:
  1. Micro XRCE-DDS agent (PX4 bridge)
  2. Camera capture node
"""
from launch import LaunchDescription
from launch.actions import ExecuteProcess, DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    output_dir_arg = DeclareLaunchArgument(
        "output_dir",
        default_value="/home/pi/captures",
        description="Directory to save captured images",
    )

    serial_port_arg = DeclareLaunchArgument(
        "serial_port",
        default_value="/dev/ttyAMA0",
        description="Serial port for PX4 uXRCE-DDS connection",
    )

    baud_rate_arg = DeclareLaunchArgument(
        "baud_rate",
        default_value="921600",
        description="Baud rate for PX4 serial connection",
    )

    # Start Micro XRCE-DDS agent
    dds_agent = ExecuteProcess(
        cmd=[
            "micro-xrce-dds-agent",
            "serial",
            "--dev", LaunchConfiguration("serial_port"),
            "-b", LaunchConfiguration("baud_rate"),
        ],
        name="uxrce_dds_agent",
        output="screen",
    )

    # Start camera capture node
    camera_node = Node(
        package="bennu_camera",
        executable="camera_node",
        name="camera_capture_node",
        parameters=[
            {"output_dir": LaunchConfiguration("output_dir")},
            {"image_width": 4056},
            {"image_height": 3040},
        ],
        output="screen",
    )

    return LaunchDescription([
        output_dir_arg,
        serial_port_arg,
        baud_rate_arg,
        dds_agent,
        camera_node,
    ])
```

**Step 6: Create config/camera_params.yaml**

```yaml
camera_capture_node:
  ros__parameters:
    output_dir: "/home/pi/captures"
    image_width: 4056
    image_height: 3040
```

**Step 7: Commit**

```bash
git add drone/ros2_ws/src/bennu_bringup/
git commit -m "feat: add bennu_bringup package with launch file and config"
```

---

### Task 11: Ground Station — WebODM Setup

**Type:** Software
**Files:**
- Create: `ground/odm/docker-compose.yml`
- Create: `ground/odm/process.sh`
- Create: `ground/odm/profiles/survey_standard.json`

**Step 1: Create docker-compose.yml**

```yaml
# WebODM — web interface for OpenDroneMap
# Usage: docker compose up -d
# Access: http://localhost:8000
version: "3"

services:
  webapp:
    image: opendronemap/webodm_webapp:latest
    ports:
      - "8000:8000"
    volumes:
      - webodm_data:/webodm/app/media
    depends_on:
      - db
      - worker
    restart: unless-stopped

  db:
    image: opendronemap/webodm_db:latest
    volumes:
      - webodm_db:/var/lib/postgresql/data
    restart: unless-stopped

  worker:
    image: opendronemap/nodeodm:latest
    ports:
      - "3000:3000"
    restart: unless-stopped

volumes:
  webodm_data:
  webodm_db:
```

**Step 2: Create process.sh**

```bash
#!/usr/bin/env bash
# Process a folder of geotagged images through OpenDroneMap (CLI)
# Usage: ./ground/odm/process.sh <image_folder> [profile]
#
# Outputs: orthophoto, DSM, 3D mesh, point cloud in <image_folder>/odm_output/

set -euo pipefail

IMAGE_DIR="${1:?Usage: process.sh <image_folder> [profile]}"
PROFILE="${2:-survey_standard}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROFILE_FILE="$SCRIPT_DIR/profiles/${PROFILE}.json"

if [ ! -d "$IMAGE_DIR" ]; then
    echo "Error: $IMAGE_DIR is not a directory"
    exit 1
fi

IMAGE_COUNT=$(ls -1 "$IMAGE_DIR"/*.jpg "$IMAGE_DIR"/*.JPG 2>/dev/null | wc -l)
echo "Processing $IMAGE_COUNT images from $IMAGE_DIR"
echo "Profile: $PROFILE"

# Read ODM options from profile
ODM_OPTIONS=""
if [ -f "$PROFILE_FILE" ]; then
    # Parse JSON options into CLI flags
    ODM_OPTIONS=$(python3 -c "
import json, sys
with open('$PROFILE_FILE') as f:
    opts = json.load(f)
for k, v in opts.items():
    if isinstance(v, bool):
        if v: print(f'--{k}', end=' ')
    else:
        print(f'--{k} {v}', end=' ')
")
fi

echo "ODM options: $ODM_OPTIONS"
echo ""

# Run ODM via Docker
docker run -ti --rm \
    -v "$IMAGE_DIR":/datasets/project \
    opendronemap/odm \
    --project-path /datasets \
    $ODM_OPTIONS

echo ""
echo "=== Processing Complete ==="
echo "Outputs in: $IMAGE_DIR/odm_output/"
echo "  - odm_orthophoto/    Orthophoto (.tif)"
echo "  - odm_dem/           Digital Surface Model (.tif)"
echo "  - odm_texturing/     Textured 3D mesh (.obj)"
echo "  - odm_georeferencing/ Georeferenced point cloud (.laz)"
```

**Step 3: Create profiles/survey_standard.json**

```json
{
    "dsm": true,
    "dtm": true,
    "orthophoto-resolution": 2.0,
    "feature-quality": "high",
    "pc-quality": "high",
    "mesh-octree-depth": 11,
    "min-num-features": 10000,
    "matcher-neighbors": 8,
    "use-3dmesh": true
}
```

**Step 4: Make executable and commit**

```bash
chmod +x ground/odm/process.sh
git add ground/odm/
git commit -m "feat: add WebODM docker-compose and ODM processing pipeline"
```

---

### Task 12: Image Transfer Script

**Type:** Software
**Files:**
- Create: `ground/transfer/sync_images.sh`

**Step 1: Create sync_images.sh**

```bash
#!/usr/bin/env bash
# Sync captured images from Pi 5 to ground station
# Usage: ./ground/transfer/sync_images.sh [pi_host] [output_dir]
#
# Prerequisites:
#   - Pi 5 connected to same network (WiFi or USB ethernet)
#   - SSH key configured for passwordless access

set -euo pipefail

PI_HOST="${1:-pi@bennu.local}"
PI_CAPTURE_DIR="/home/pi/captures"
OUTPUT_DIR="${2:-$(pwd)/captures_$(date +%Y%m%d_%H%M%S)}"

echo "=== Syncing images from $PI_HOST ==="

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Count images on Pi
echo "Checking images on drone..."
IMAGE_COUNT=$(ssh "$PI_HOST" "ls -1 $PI_CAPTURE_DIR/*.jpg 2>/dev/null | wc -l")
echo "Found $IMAGE_COUNT images"

if [ "$IMAGE_COUNT" -eq 0 ]; then
    echo "No images to transfer."
    exit 0
fi

# Transfer with rsync (resume-capable, shows progress)
rsync -avz --progress \
    "$PI_HOST:$PI_CAPTURE_DIR/*.jpg" \
    "$OUTPUT_DIR/"

echo ""
echo "=== Transfer Complete ==="
echo "Images saved to: $OUTPUT_DIR"
echo "Image count: $(ls -1 "$OUTPUT_DIR"/*.jpg | wc -l)"
echo ""
echo "Next step: Process with ODM"
echo "  ./ground/odm/process.sh $OUTPUT_DIR"
```

**Step 2: Make executable and commit**

```bash
chmod +x ground/transfer/sync_images.sh
git add ground/transfer/
git commit -m "feat: add image transfer script from drone Pi to ground station"
```

---

### Task 13: Model Inspection Script

**Type:** Software
**Files:**
- Create: `ground/analysis/inspect_model.py`
- Create: `ground/analysis/requirements.txt`

**Step 1: Create requirements.txt**

```
open3d>=0.17.0
numpy
```

**Step 2: Create inspect_model.py**

```python
#!/usr/bin/env python3
"""
Inspect ODM output: load point cloud, print stats, optionally visualize.

Usage:
    python3 ground/analysis/inspect_model.py <odm_output_dir>
    python3 ground/analysis/inspect_model.py <odm_output_dir> --visualize
"""
import argparse
import os
import sys


def find_output_files(odm_dir: str) -> dict:
    """Find ODM output files in the given directory."""
    files = {}

    # Point cloud
    for ext in [".laz", ".las", ".ply"]:
        for root, _, filenames in os.walk(odm_dir):
            for f in filenames:
                if f.endswith(ext):
                    files.setdefault("pointcloud", []).append(
                        os.path.join(root, f)
                    )

    # Mesh
    for root, _, filenames in os.walk(odm_dir):
        for f in filenames:
            if f.endswith(".obj"):
                files.setdefault("mesh", []).append(os.path.join(root, f))

    # Orthophoto
    for root, _, filenames in os.walk(odm_dir):
        for f in filenames:
            if f.endswith(".tif") and "orthophoto" in root:
                files.setdefault("orthophoto", []).append(
                    os.path.join(root, f)
                )

    # DSM/DTM
    for root, _, filenames in os.walk(odm_dir):
        for f in filenames:
            if f.endswith(".tif") and "dem" in root:
                files.setdefault("dem", []).append(os.path.join(root, f))

    return files


def inspect_pointcloud(filepath: str, visualize: bool = False):
    """Load and inspect a point cloud file."""
    try:
        import open3d as o3d
    except ImportError:
        print("  open3d not installed. Install: pip install open3d")
        return

    print(f"\n  Loading: {filepath}")
    pcd = o3d.io.read_point_cloud(filepath)

    points = len(pcd.points)
    bbox = pcd.get_axis_aligned_bounding_box()
    extent = bbox.get_extent()

    print(f"  Points: {points:,}")
    print(f"  Bounding box: {extent[0]:.1f} x {extent[1]:.1f} x {extent[2]:.1f} m")
    print(f"  Has colors: {pcd.has_colors()}")
    print(f"  Has normals: {pcd.has_normals()}")

    if visualize:
        print("  Opening 3D viewer...")
        o3d.visualization.draw_geometries([pcd])


def main():
    parser = argparse.ArgumentParser(description="Inspect ODM output")
    parser.add_argument("odm_dir", help="Path to ODM output directory")
    parser.add_argument(
        "--visualize", action="store_true", help="Open 3D viewer"
    )
    args = parser.parse_args()

    if not os.path.isdir(args.odm_dir):
        print(f"Error: {args.odm_dir} not found")
        sys.exit(1)

    print(f"=== Inspecting ODM Output: {args.odm_dir} ===")

    files = find_output_files(args.odm_dir)

    if not files:
        print("No ODM output files found.")
        sys.exit(1)

    for category, paths in files.items():
        print(f"\n{category.upper()}:")
        for p in paths:
            size_mb = os.path.getsize(p) / (1024 * 1024)
            print(f"  {os.path.basename(p)} ({size_mb:.1f} MB)")

            if category == "pointcloud" and p.endswith(".ply"):
                inspect_pointcloud(p, args.visualize)


if __name__ == "__main__":
    main()
```

**Step 3: Commit**

```bash
git add ground/analysis/
git commit -m "feat: add ODM output inspection and visualization script"
```

---

## Summary Checklist

| Task | Type | Phase | Description |
|------|------|-------|-------------|
| 1 | Software | Setup | Git repo + directory structure + CLAUDE.md |
| 2 | Software | 1 | PX4 parameter files (base, motors, GPS, companion, camera, tuning) |
| 3 | Software | 1 | Flash + param upload scripts |
| 4 | Docs | 1 | Frame README + assembly build guide |
| 5 | Hardware | 1 | Order parts + print frame (manual) |
| 6 | Docs | 1 | Wiring diagram |
| 7 | Hardware | 1 | Assemble, flash, calibrate, maiden flight (manual) |
| 8 | Software | 2 | Pi 5 setup script (Ubuntu, ROS2, uXRCE-DDS) |
| 9 | Software | 2 | bennu_camera ROS2 package (capture + geotag) |
| 10 | Software | 2 | bennu_bringup ROS2 package (launch files) |
| 11 | Software | 2 | WebODM Docker setup + processing scripts |
| 12 | Software | 2 | Image transfer script (Pi → PC) |
| 13 | Software | 2 | ODM output inspection + visualization |

Phase 3 (Autonomy) tasks are deferred — will be planned after Phase 2 is validated.
