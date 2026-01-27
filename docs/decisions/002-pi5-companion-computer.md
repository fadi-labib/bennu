# ADR-002: Raspberry Pi 5 as Companion Computer

## Status

Accepted

## Context

Need an onboard computer for camera control, GPS geotagging, and ROS2 node
execution. The companion computer sits between the flight controller (PX4) and
the camera, handling intelligence tasks that don't belong on the FC.

Requirements:
- Run ROS2 Jazzy (Ubuntu 24.04)
- Interface with Pi HQ Camera via CSI
- Communicate with Pixhawk via UART (uXRCE-DDS)
- Light enough for a 7" quad (~900g AUW target)
- Affordable ($80-100)

Alternatives considered:
- **Jetson Nano/Orin Nano** — More compute, but heavier, more expensive ($200+),
  higher power draw. Overkill for camera + DDS — would only be needed for
  onboard SLAM or computer vision (Phase 3 maybe).
- **Orange Pi 5** — Cheaper, but less community support for ROS2 and libcamera.

## Decision

Use **Raspberry Pi 5 (8GB)** running Ubuntu 24.04 with ROS2 Jazzy.

## Consequences

**Positive:**

- **Best ROS2 support** — Ubuntu 24.04 + Jazzy are first-class on Pi 5.
- **Native CSI camera interface** — libcamera works out of the box with Pi HQ Camera.
- **Low weight** — ~45g board weight, fits the AUW budget.
- **Affordable** — $80 for 8GB model.
- **Massive community** — easy to find help, libraries, and examples.
- **GPIO UART** — Direct serial connection to Pixhawk TELEM2 at 921600 baud.

**Negative:**

- **WiFi range ~30m** — Not usable for in-flight communication. Image transfer
  is post-flight only (land, connect, rsync).
- **No GPU** — Cannot run onboard computer vision. If Phase 3 needs SLAM or
  obstacle avoidance, may need Jetson upgrade.
- **SD card reliability** — Potential for corruption in power-loss scenarios.
  Mitigated by graceful shutdown via PX4 battery warnings.

**Neutral:**

- 5-12W power draw is manageable via BEC from drone battery.
- Phase 3 autonomous features may require hardware upgrade.
