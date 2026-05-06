# Build Checklist

Track your build progress step by step. Check off items as you complete them.

## Phase A: Parts Procurement

### Core Electronics

- [ ] Holybro Pixhawk 6C (with PM02 power module)
- [ ] Holybro Tekko32 F4 4-in-1 50A ESC
- [ ] T-Motor Velox V2207.5 1950KV x4
- [ ] HQProp 7x3.5x3 tri-blade x4 (+ spares)
- [ ] Holybro M9N GPS (u-blox M9N, built-in compass)
- [ ] RC Receiver (TBS Crossfire Nano or ELRS 900MHz)
- [ ] RC Transmitter (if not owned)
- [ ] 4S 2200–3000mAh LiPo x2
- [ ] LiPo charger (if not owned)
- [ ] Holybro SiK Radio V3 (433 or 915MHz, pair)

### Companion Computer

- [ ] Raspberry Pi 5 (8GB)
- [ ] 64GB+ microSD card (or NVMe HAT + SSD)
- [ ] BEC 5V 3A (Matek UBEC or Pololu 5V step-down)

### Camera

- [ ] Raspberry Pi HQ Camera (IMX477)
- [ ] 6mm CS-mount lens

### Frame Materials

- [ ] CF-PETG filament 1kg (e.g., Polymaker PolyLite CF-PETG)
- [ ] Hardened steel 0.4mm nozzle (CF wears brass)
- [ ] Carbon fiber tube 10mm OD x 200mm x4 (arms)
- [ ] Carbon fiber tube 12mm OD x 150mm x1 (GPS mast)
- [ ] M3x8 button head screws x20
- [ ] M3 heat-set inserts x20
- [ ] M2.5x6 screws x4 (Pi 5 mount)
- [ ] M2.5 standoffs 10mm x4 (FC mount)
- [ ] Vibration dampening balls x4 (FC soft mount)

### Wiring & Connectors

- [ ] XT60 connectors (if not included with ESC/PM02)
- [ ] 14-16 AWG silicone wire (battery to PM02)
- [ ] JST-GH connectors or pre-made cables (TELEM2 to Pi UART)
- [ ] Heat shrink tubing assortment
- [ ] Zip ties

---

## Phase B: 3D Printing (~12h total)

- [ ] Bottom plate (~3h)
- [ ] Top plate (~2h)
- [ ] Motor mounts x4 (~30min each, ~2h total)
- [ ] Arm clamps x4 (~20min each, ~1.5h total)
- [ ] GPS mast base (~30min)
- [ ] Camera mount (~1h)
- [ ] Canopy (~2h)
- [ ] Landing legs x4 (~20min each, ~1.5h total)
- [ ] Test-fit all parts before assembly

---

## Phase C: Frame Assembly

- [ ] Install M3 heat-set inserts in all printed parts (soldering iron at 220°C)
- [ ] Slide CF tube arms through bottom plate channels
- [ ] Attach arm clamps on both sides, tighten M3 screws (snug, not overtight)
- [ ] Press-fit motor mounts onto arm ends
- [ ] Mount motors to motor mounts (M3 screws, mind rotation direction)
- [ ] Attach landing legs

---

## Phase D: Electronics Installation

### ESC & Motors

- [ ] Mount Tekko32 4-in-1 ESC on bottom plate
- [ ] Solder motor wires to ESC (correct rotation: M1 FR-CCW, M2 RL-CCW, M3 FL-CW, M4 RR-CW)
- [ ] Route motor wires cleanly along arms
- [ ] Connect ESC signal cable to Pixhawk MAIN OUT 1-4

### Flight Controller

- [ ] Attach vibration dampening balls to M2.5 standoffs
- [ ] Mount standoffs to top plate
- [ ] Place Pixhawk 6C on standoffs (arrow pointing forward)
- [ ] Connect PM02 power cable to Pixhawk POWER1
- [ ] Connect PM02 XT60 to ESC power input

### GPS

- [ ] Insert GPS mast CF tube into mast base
- [ ] Secure with set screw or CA glue
- [ ] Mount M9N GPS on mast top (arrow forward)
- [ ] Route GPS cable to Pixhawk GPS1 port

### RC & Telemetry

- [ ] Mount RC receiver (away from ESC/motors for signal quality)
- [ ] Connect RC receiver to Pixhawk RC IN
- [ ] Mount SiK radio (antenna orientation matters)
- [ ] Connect SiK radio to Pixhawk TELEM1

### Companion Computer

- [ ] Mount Pi 5 to top plate with M2.5 screws
- [ ] Connect BEC 5V output to Pi 5 (via GPIO 5V/GND or USB-C)
- [ ] Connect BEC input to battery voltage (tap from PM02 or ESC pad)
- [ ] Wire TELEM2 TX → Pi GPIO 15 (RX), TELEM2 RX → Pi GPIO 14 (TX)
- [ ] Connect Pi HQ Camera via CSI ribbon cable

### Power

- [ ] Wire PM02 battery input (XT60)
- [ ] Wire BEC input to battery voltage
- [ ] Verify no short circuits (multimeter continuity check)
- [ ] Plug in battery briefly — verify Pixhawk boots, Pi boots, no smoke

---

## Phase E: Software Setup

### Pi 5

- [ ] Flash Ubuntu 24.04 Server to microSD/NVMe
- [ ] Boot and configure WiFi + SSH
- [ ] Install ROS2 Jazzy (`sudo apt install ros-jazzy-ros-base`)
- [ ] Enable UART for uXRCE-DDS (`/boot/firmware/config.txt`)
- [ ] Clone bennu repo and install packages
- [ ] Install Micro XRCE-DDS Agent
- [ ] Test `MicroXRCEAgent serial --dev /dev/ttyAMA0 -b 921600`

### PX4

- [ ] Flash PX4 v1.16.1 via QGroundControl
- [ ] Upload base params: `./firmware/px4/upload_params.sh`
- [ ] Calibrate accelerometer (QGC)
- [ ] Calibrate gyroscope (QGC)
- [ ] Calibrate compass (QGC — rotate drone in all axes)
- [ ] Calibrate radio (QGC — move all sticks)
- [ ] Verify GPS lock (outdoors, wait for 3D fix)
- [ ] Configure TELEM2 for uXRCE-DDS:
    - `UXRCE_DDS_CFG: TELEM2`
    - `SER_TEL2_BAUD: 921600`

### Integration Test (props OFF)

- [ ] Power on full system (battery)
- [ ] Verify uXRCE-DDS bridge: Pi sees PX4 topics (`ros2 topic list`)
- [ ] Verify GPS data on Pi: `ros2 topic echo /fmu/out/vehicle_gps_position`
- [ ] Verify camera capture: `libcamera-still -o test.jpg`
- [ ] Run bennu camera node: `ros2 run bennu_camera camera_node`

---

## Phase F: First Flight

### Pre-flight (props ON, outdoors, open area)

- [ ] Attach props (correct rotation per motor)
- [ ] Verify motor spin direction (QGC motor test, one at a time, low throttle)
- [ ] Battery fully charged
- [ ] GPS 3D fix acquired
- [ ] Failsafes configured (RTL on RC loss, RTL on data link loss)
- [ ] QGroundControl connected via telemetry

### First Hover

- [ ] Arm in Stabilized mode
- [ ] Gentle throttle up — hover at 1–2m
- [ ] Check stability (no oscillations, no toilet-bowling)
- [ ] If unstable: land immediately, check prop direction and motor order
- [ ] Land, disarm

### First Position Hold

- [ ] Switch to Position mode (requires GPS lock)
- [ ] Hover at 5m — verify GPS hold (should stay in place hands-off)
- [ ] Test RTL: flip RTL switch — drone should return and land

### First Survey Flight

- [ ] Plan a small grid (50x50m) using GridPlanner or QGC
- [ ] Upload mission
- [ ] Fly in Auto mode
- [ ] Verify images captured
- [ ] Download bundle, validate with E2E test
