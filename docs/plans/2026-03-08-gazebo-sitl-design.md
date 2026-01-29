# Gazebo SITL Simulation — Design

**Status:** Implemented (8 tasks merged to main)

**Goal:** Run the full Bennu software stack (PX4 + ROS2 + camera node) in simulation on the dev machine using Docker, so we can test waypoint missions, camera triggers, and geotagging without hardware.

**Dev machine:** Ubuntu 24.04, x86_64, no ROS2/Gazebo installed natively.

---

## Architecture

```
Docker Compose (sim/docker-compose.sim.yml)
├── px4-sitl        — PX4 firmware + Gazebo Harmonic (GUI via X11)
├── ros2-dev        — ROS2 Jazzy + bennu packages + uXRCE-DDS agent
└── (host)          — QGroundControl connects via UDP to px4-sitl

VS Code .devcontainer attaches to ros2-dev container
```

### Communication Flow

```
PX4 SITL (container)
  │
  ├── UDP :14540 ──► QGroundControl (host)
  │
  └── uXRCE-DDS over UDP ──► Micro XRCE-DDS Agent (ros2-dev container)
                                    │
                                    ├── /fmu/out/vehicle_global_position
                                    ├── /fmu/out/camera_trigger
                                    └── bennu_camera node subscribes
```

## Key Decisions

- **ROS2 Jazzy** everywhere (dev + Pi 5 on Ubuntu 24.04) — replaces Humble
- **Gazebo Harmonic** — LTS release paired with Jazzy
- **Docker Compose** for sim orchestration + VS Code devcontainer for IDE integration
- PX4 ↔ ROS2 communication via **UDP** in sim (not serial like on real hardware)
- QGroundControl runs **natively on host**, connects to PX4 SITL via UDP
- X11 forwarding for Gazebo GUI (`DISPLAY` env + `/tmp/.X11-unix` volume)

## Phased Approach

### Phase 1: PX4 SITL + QGroundControl

- `px4-sitl` container runs PX4 SITL with Gazebo Harmonic, generic quad X model
- Exposes UDP ports for QGroundControl on host
- Validate: takeoff, hover, waypoint missions, camera triggers, RTL, failsafes
- No ROS2 nodes — just the sim flying

### Phase 2: Full Stack

- `ros2-dev` container runs Micro XRCE-DDS agent connecting to `px4-sitl` over UDP
- `bennu_camera` node receives camera triggers, writes mock geotagged images
- `bennu_bringup` launch file works in sim (UDP transport instead of serial)
- Test the full capture → geotag → transfer pipeline

## Files

### New Files

| File | Purpose |
|------|---------|
| `sim/docker-compose.sim.yml` | Orchestrates PX4 SITL + ROS2 containers |
| `sim/Dockerfile.px4` | PX4 SITL + Gazebo Harmonic image |
| `sim/Dockerfile.ros2` | ROS2 Jazzy + bennu workspace image |
| `sim/README.md` | Sim setup and usage instructions |
| `.devcontainer/devcontainer.json` | VS Code devcontainer config |

### Modified Files

| File | Change |
|------|--------|
| `drone/setup_pi.sh` | Humble → Jazzy, Ubuntu 22.04 → 24.04 |
| `CLAUDE.md` | Update tech stack to Jazzy |
| `drone/ros2_ws/src/bennu_camera/bennu_camera/camera_node.py` | Add sim mode (placeholder images when no libcamera) |
| `drone/ros2_ws/src/bennu_bringup/launch/drone.launch.py` | Add `use_sim` launch argument for UDP transport |
| `drone/ros2_ws/src/*/package.xml` | No change needed (rclpy/px4_msgs are version-agnostic) |

## Sim Mode in camera_node

When `libcamera-still` is not available (simulation), the camera node:
1. Receives trigger from PX4 as normal
2. Creates a placeholder JPEG (solid color or test pattern)
3. Writes GPS EXIF from the simulated position
4. Logs normally — the full pipeline runs without a real camera

## Docker Details

### px4-sitl container
- Base: Ubuntu 24.04
- Installs: PX4-Autopilot (built for SITL), Gazebo Harmonic
- Entrypoint: `make px4_sitl gz_x500` (standard quad)
- Ports: 14540 (QGC), 8888 (uXRCE-DDS UDP)
- X11 for Gazebo GUI

### ros2-dev container
- Base: `ros:jazzy` official image
- Installs: Micro XRCE-DDS agent, px4_msgs, bennu packages
- Mounts: `drone/ros2_ws/src` as volume (live editing)
- Devcontainer: VS Code extensions for Python, ROS2, XML
