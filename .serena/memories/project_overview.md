# Bennu Project Overview

DIY 3D-printed 7" quadcopter drone for outdoor photogrammetry using PX4 + ROS2 + OpenDroneMap.

## Tech Stack
- **Flight Controller:** PX4 v1.16+ on Holybro Pixhawk 6C
- **Companion Computer:** Raspberry Pi 5 (8GB), Ubuntu 24.04, ROS2 Jazzy
- **PX4-ROS2 Bridge:** uXRCE-DDS (NOT MAVROS)
- **Camera:** Raspberry Pi HQ Camera (IMX477) + 6mm CS-mount lens
- **Ground Station:** QGroundControl + WebODM (Docker)
- **Language:** Python (ROS2 nodes), Bash (scripts)
- **Simulation:** PX4 SITL + Gazebo Harmonic in Docker

## Repo Structure
- `drone/ros2_ws/src/` — ROS2 packages (bennu_camera, bennu_bringup)
- `ground/` — ground station code (WebODM, transfer, analysis)
- `firmware/` — PX4 param files + upload scripts
- `sim/` — Docker simulation stack (Compose files, Makefile, Dockerfiles)
- `frame/` — 3D print files (STL/STEP)
- `config/` — shared config (camera calibration, network)
- `docs/` — MkDocs Material documentation site
- `tests/` — cross-package tests
- `contract/` — mission bundle contract schemas

## Key Python Packages
- `bennu_camera` — Camera capture node with pluggable backends (libcamera, placeholder)
- `bennu_bringup` — Launch files for drone startup
