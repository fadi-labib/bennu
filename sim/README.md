# Bennu SITL Simulation

Run the full Bennu software stack in simulation using Docker.

## Prerequisites

- Docker and Docker Compose
- QGroundControl installed on host
- X11 display (for Gazebo GUI)

## Quick Start

### 1. Allow X11 access for Docker

    xhost +local:docker

### 2. Build and start the simulation

    cd sim
    docker compose -f docker-compose.sim.yml up --build

### 3. Connect QGroundControl

Open QGroundControl — it auto-connects to PX4 SITL on `udp://localhost:14540`.

### 4. (Optional) Open a shell in the ROS2 container

    docker exec -it bennu-ros2-dev bash
    ros2 topic list

## Architecture

    ┌──────────────────────┐     ┌──────────────────────┐
    │  px4-sitl container  │     │  ros2-dev container  │
    │                      │     │                      │
    │  PX4 Firmware (SITL) │◄───►│  uXRCE-DDS Agent     │
    │  Gazebo Harmonic     │UDP  │  bennu_camera node   │
    │  x500 quad model     │8888 │  bennu_bringup       │
    └──────┬───────────────┘     └──────────────────────┘
           │ UDP 14540
    ┌──────▼───────────────┐
    │  Host                │
    │  QGroundControl      │
    └──────────────────────┘

## Phase 1: Fly the sim

Plan waypoint missions in QGC, test takeoff/landing/RTL.

## Phase 2: Test ROS2 nodes

    docker exec -it bennu-ros2-dev bash
    source /ros2_ws/install/setup.bash
    ros2 launch bennu_bringup drone.launch.py use_sim:=true

## Stopping

    docker compose -f docker-compose.sim.yml down
