# Bennu — DIY Photogrammetry Drone

## Project Overview
3D-printed 7" quadcopter for outdoor photogrammetry using PX4 + ROS2 + OpenDroneMap.

## Tech Stack
- **Flight Controller:** PX4 v1.16+ on Holybro Pixhawk 6C
- **Companion Computer:** Raspberry Pi 4 (4GB), Ubuntu 24.04, ROS2 Jazzy
- **PX4-ROS2 Bridge:** uXRCE-DDS (not MAVROS)
- **Camera:** Raspberry Pi HQ Camera (IMX477) + 6mm CS-mount lens
- **Ground Station:** QGroundControl + WebODM (Docker)
- **Language:** Python (ROS2 nodes), Bash (scripts)

## Repo Structure
- `drone/` — code that runs onboard the Pi 4
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
- Start sim (one command): `cd sim && make sim` — containers + QGC + auto-fly + shell
- Start sim (headless): `cd sim && make dev`
- Start sim (Gazebo GUI): `cd sim && make dev-debug`
- Launch QGC only: `cd sim && make qgc`
- Run unit tests: `cd sim && make test`
- Run SIL tests: `cd sim && make test-smoke`
- Stop sim: `cd sim && make clean`

## Workflow Rules
- Commit and push after every task
- When a plan is completed: convert it to an ADR, design document, and/or mkdocs page, then delete the plan file — completed plans should not linger

## AI Coding Assistants Policy
Adapted from the [Linux kernel coding assistants policy](https://github.com/torvalds/linux/blob/master/Documentation/process/coding-assistants.rst).

- **Human responsibility:** The human submitter reviews all AI-generated code, ensures correctness, and takes full responsibility for the contribution.
- **No fake authorship:** AI tools must NOT be listed as commit author or co-author. Only humans author commits.
- **Attribution:** When AI tools contribute to development, use an `Assisted-by` trailer in the commit message:
  ```
  Assisted-by: Claude:claude-opus-4-6
  ```
- **Licensing:** All contributions must be compatible with Apache-2.0.

## Design Doc
See `docs/plans/2026-03-08-drone-platform-readiness-design.md`
