# Bennu — DIY 3D-Printed Photogrammetry Drone

**Date:** 2026-03-08
**Status:** Approved

## Overview

Bennu is a lightweight, 3D-printed 7" quadcopter drone for outdoor site survey and photogrammetry. It captures geotagged aerial images and reconstructs 3D maps using OpenDroneMap. Built on PX4 + ROS2 for a production-grade path to full autonomy.

## Constraints

- **Mission profile:** Outdoor site survey (GPS-based navigation)
- **3D printer:** AnkerMake M5C, 235×235mm bed
- **Budget:** $800+ (premium DIY, excluding transmitter and printer)
- **Builder experience:** Computer engineer, comfortable with electronics, new to drones
- **Processing:** Offboard (PC/server) using OpenDroneMap

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GROUND STATION (PC)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ QGroundControl│  │  WebODM /    │  │  ROS2 Ground      │  │
│  │ (Mission Plan)│  │  OpenDroneMap│  │  Station (future)  │  │
│  └──────┬───────┘  └──────┬───────┘  └───────┬───────────┘  │
│         │ MAVLink         │ Images           │ ROS2 DDS     │
└─────────┼─────────────────┼──────────────────┼──────────────┘
          │ Radio           │ WiFi/SD          │ WiFi
          ▼                 │                  │
┌─────────────────────────────────────────────────────────────┐
│                        DRONE                                 │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐     │
│  │         Companion Computer (Raspberry Pi 5)          │     │
│  │  ┌───────────┐  ┌────────────┐  ┌────────────────┐  │     │
│  │  │ ROS2 Nodes│  │ Camera     │  │ uXRCE-DDS     │  │     │
│  │  │ (Phase 3) │  │ Capture    │  │ Agent          │  │     │
│  │  └───────────┘  └─────┬──────┘  └───────┬────────┘  │     │
│  └────────────────────────┼─────────────────┼───────────┘     │
│                           │ CSI             │ Serial/UART     │
│                           ▼                 ▼                 │
│  ┌──────────┐    ┌──────────────────────────────────┐        │
│  │ Pi HQ    │    │   Flight Controller (Pixhawk 6C) │        │
│  │ Camera   │    │   PX4 Autopilot v1.15+            │        │
│  └──────────┘    │   ┌─────┐ ┌─────┐ ┌──────────┐  │        │
│                  │   │ GPS │ │ IMU │ │ RC Recv  │  │        │
│                  │   └─────┘ └─────┘ └──────────┘  │        │
│                  └──────────────┬─────────────────────┘        │
│                                │ DShot                        │
│                    ┌───────────┼───────────┐                  │
│                    ▼           ▼           ▼                  │
│                 ┌─────┐    ┌─────┐    ┌─────┐    ┌─────┐     │
│                 │ESC+M│    │ESC+M│    │ESC+M│    │ESC+M│     │
│                 └─────┘    └─────┘    └─────┘    └─────┘     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐      │
│  │          3D-Printed Frame (7", CF-PETG)             │      │
│  │          Modular: Body + 4 Arms + Camera Mount     │      │
│  └────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Key Decisions

- **PX4** handles all flight-critical tasks (stabilization, GPS nav, failsafes)
- **Raspberry Pi 5** handles camera, geotagging, and future ROS2 autonomy
- **uXRCE-DDS** provides native ROS2-PX4 communication (no MAVROS bridge)
- **Separation of concerns:** flight safety on FC, intelligence on companion
- **Phased deployment:** Pi 5 optional for phases 1-2, required for phase 3

## Hardware BOM

### Flight Controller & Core Electronics (~$350-400)

| Component | Part | Rationale | Est. Price |
|-----------|------|-----------|------------|
| Flight Controller | Holybro Pixhawk 6C | STM32H743, dual IMU, PX4 reference board. TELEM2 port for companion computer UART. | $110-150 |
| ESC | Holybro Tekko32 F4 4-in-1 50A | Clean wiring, BLHeli_32, DShot600 | $60-80 |
| Motors | T-Motor Velox V2207.5 1950KV (×4) | Efficient at 7", well-proven | $50-60 |
| Props | HQProp 7×3.5×3 tri-blade (×4+ spares) | Good thrust/efficiency at survey speed | $15 |
| GPS | Holybro M9N (u-blox M9N) | PX4-native, good accuracy, built-in compass | $40-50 |
| RC Receiver | TBS Crossfire Nano RX or ELRS 900MHz | Long range (>10km), low latency | $25-40 |
| Battery | 4S 2200-3000mAh LiPo (×2) | ~15-20 min flight time per battery | $50-70 |
| Power Module | Holybro PM02 (with Pixhawk kit) | Current/voltage sensing for PX4 | included |
| Telemetry | Holybro SiK Radio V3 (433/915MHz pair) | MAVLink telemetry to QGroundControl | $40-50 |

### Camera System (~$70)

| Component | Part | Rationale | Est. Price |
|-----------|------|-----------|------------|
| Camera | Raspberry Pi HQ Camera (IMX477) | 12.3MP, interchangeable CS-mount lenses, ~35g module. Driven by Pi 5 via libcamera. | $50 |
| Lens | 6mm CS-mount lens | ~40mm equiv, ~2cm/pixel GSD at 50-80m altitude, good survey coverage | $20 |

### Companion Computer (~$100)

| Component | Part | Rationale | Est. Price |
|-----------|------|-----------|------------|
| Computer | Raspberry Pi 5 (8GB) | ROS2 Humble, uXRCE-DDS agent, libcamera, 45g, 5-12W | $80 |
| Storage | 64GB+ microSD or NVMe HAT | Store captured images during flight | $15-30 |
| Power | BEC 5V 3A (from battery) | Powers Pi from drone battery | $5-10 |

### 3D-Printed Frame

| Aspect | Details |
|--------|---------|
| Base design | Custom, adapted from open-source 7" LR frames. CF tube arms (6-10mm OD) recommended for strength. |
| Material | CF-PETG (carbon fiber reinforced PETG) for stiffness and heat resistance |
| Modularity | Central body + 4 detachable arms + canopy + GPS mast + camera mount. Each piece fits 235×235mm bed. |
| Mounting | Vibration-dampened FC mount, Pi 5 top plate mount (M2.5), GPS mast (30mm CF tube), bottom camera tilt mount |
| Print settings | 3-4 perimeters, 30-40% gyroid infill, 0.2mm layer height |

### Estimated Total: ~$650-850 (without RC transmitter)

## Software Stack

### Flight Controller (Pixhawk 6C)

- **PX4 Autopilot v1.15+** with uXRCE-DDS client (built-in)
- EKF2 state estimation
- Navigator module for waypoint execution
- Camera trigger module (distance-based via `TRIG_MODE` and `TRIG_DIST` params)

### Companion Computer (Raspberry Pi 5)

- **Ubuntu 22.04 Server** (best tested with ROS2 Humble)
- **ROS 2 Humble Hawksbill** (LTS)
  - `micro_xrce_dds_agent` — PX4 bridge over serial (TELEM2, 921600 baud)
  - `px4_msgs` — PX4 message definitions for ROS2
  - `bennu_camera` — camera capture + geotagging node
  - `bennu_mission` — mission logic (Phase 3)
  - `bennu_bringup` — launch files

### Ground Station (PC)

- **QGroundControl 4.3+** — mission planning, survey grid patterns, telemetry
- **WebODM / OpenDroneMap** — 3D reconstruction from geotagged images
- **CloudCompare / MeshLab** — 3D model visualization

### PX4-ROS2 Communication

```
Pi 5 UART TX/RX  ←→  Pixhawk 6C TELEM2 TX/RX (cross-wired)

PX4 params:
  MAV_1_CONFIG = TELEM2
  SER_TEL2_BAUD = 921600

Pi 5:
  MicroXRCEAgent serial --dev /dev/ttyAMA0 -b 921600
```

## Photogrammetry Pipeline

```
1. Plan survey grid in QGroundControl (overlap 75-80% front, 65-70% side)
2. Drone flies waypoint mission, PX4 triggers camera at distance intervals
3. Pi 5 captures images via libcamera, writes GPS EXIF from PX4 trigger events
4. Post-flight: transfer images from Pi SD card to ground station
5. Process in WebODM/ODM:
   - Feature detection (SIFT/SuperPoint)
   - Feature matching
   - Structure from Motion (SfM)
   - Dense point cloud (MVS)
   - Mesh generation + texture mapping
   - Orthophoto + DSM generation
6. Output: point cloud (.ply), 3D mesh (.obj), orthophoto (.tif), DSM (.tif)
```

## Repository Structure

```
bennu/
├── drone/                         # ── ONBOARD (runs on Pi 5) ──
│   └── ros2_ws/
│       └── src/
│           ├── bennu_camera/      # Camera capture + geotag ROS2 package
│           ├── bennu_mission/     # Mission logic ROS2 package (Phase 3)
│           └── bennu_bringup/     # Launch files + config
│
├── ground/                        # ── GROUND STATION (runs on your PC) ──
│   ├── odm/
│   │   ├── process.sh             # Run WebODM/ODM on captured images
│   │   ├── docker-compose.yml     # WebODM container setup
│   │   └── profiles/              # ODM processing profiles (resolution, quality)
│   ├── transfer/
│   │   └── sync_images.sh         # Pull images from Pi over WiFi/SSH
│   ├── analysis/
│   │   └── inspect_model.py       # Load + inspect output point clouds/meshes
│   └── ros2_ground_ws/            # (Phase 3) Ground ROS2 workspace
│       └── src/
│           └── bennu_ground/      # Ground station ROS2 nodes (telemetry UI, mission upload)
│
├── frame/                         # ── HARDWARE ──
│   ├── stl/                       # Print-ready STL files
│   ├── step/                      # Editable STEP/F3D source
│   └── README.md                  # Print settings + assembly guide
│
├── firmware/                       # ── FLIGHT CONTROLLER ──
│   ├── px4/
│   │   ├── params/
│   │   │   ├── base_params.yaml   # Base PX4 parameters (frame type, EKF2, failsafes)
│   │   │   ├── motor_params.yaml  # Motor mixing, PWM/DShot config
│   │   │   ├── gps_params.yaml    # GPS, compass, EKF2 fusion settings
│   │   │   ├── camera_params.yaml # Camera trigger mode, distance, output pin
│   │   │   ├── companion_params.yaml # TELEM2 baud, MAV_1_CONFIG, uXRCE-DDS
│   │   │   └── tuning_params.yaml # PID gains (updated after test flights)
│   │   ├── flash.sh               # Script to flash PX4 firmware to Pixhawk 6C
│   │   ├── upload_params.sh       # Push params to FC via QGC CLI or MAVLink
│   │   └── VERSION                # Tracks which PX4 release is flashed
│   └── mixer/
│       └── bennu_quad.mix         # Custom motor mixer (if needed)
│
├── config/                        # ── SHARED CONFIG ──
│   ├── camera_calibration/        # Lens distortion coefficients for ODM
│   └── network/
│       └── pi_wifi.conf           # Pi 5 WiFi config for image transfer
│
├── docs/
│   ├── plans/                     # Design + implementation plans
│   ├── wiring/                    # Wiring diagrams
│   └── build-guide/               # Step-by-step build instructions
│
└── CLAUDE.md
```

## Phased Delivery

### Phase 1: Fly (Manual FPV)

- Build 3D-printed frame
- Wire FC + ESCs + motors + GPS + RC receiver
- Flash PX4, configure, tune PIDs
- Maiden flight, manual RC control
- Validate flight stability and endurance

### Phase 2: Survey (Waypoint + Camera)

- Add Pi 5 companion computer + Pi HQ Camera
- Set up uXRCE-DDS serial link between Pi and Pixhawk
- Implement camera capture node (ROS2)
- Configure PX4 camera trigger (distance-based)
- Plan and execute waypoint survey missions via QGroundControl
- Geotagging pipeline: PX4 trigger events → EXIF GPS data
- Process images through WebODM → 3D reconstruction
- Validate reconstruction quality

### Phase 3: Autonomy (Future)

- ROS2 autonomous coverage planner node
- Auto-generate survey grid from area boundary polygon
- Live telemetry + mission status via ROS2 ground station
- Potential: onboard SLAM preview, obstacle avoidance (may require Jetson upgrade)

## Open Source Projects Used

| Project | Role | URL |
|---------|------|-----|
| PX4 Autopilot | Flight firmware | https://github.com/PX4/PX4-Autopilot |
| px4_msgs | ROS2 message defs | https://github.com/PX4/px4_msgs |
| px4_ros_com | ROS2 examples | https://github.com/PX4/px4_ros_com |
| Micro-XRCE-DDS-Agent | PX4-ROS2 bridge | https://github.com/eProsima/Micro-XRCE-DDS-Agent |
| OpenDroneMap | Photogrammetry | https://github.com/OpenDroneMap/ODM |
| WebODM | ODM web interface | https://github.com/OpenDroneMap/WebODM |
| QGroundControl | Ground station | https://github.com/mavlink/qgroundcontrol |
