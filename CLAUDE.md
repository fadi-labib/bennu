# Bennu — DIY Photogrammetry Drone

## Project Overview
3D-printed 7" quadcopter for outdoor photogrammetry using PX4 + ROS2 + OpenDroneMap.

## Tech Stack
- **Flight Controller:** PX4 v1.16+ on Holybro Pixhawk 6C
- **Companion Computer:** Raspberry Pi 5 (8GB), Ubuntu 24.04, ROS2 Jazzy
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
- Start sim: `cd sim && docker compose -f docker-compose.sim.yml up`

## Design Doc
See `docs/plans/2026-03-08-drone-photogrammetry-design.md`
