# Gazebo SITL Simulation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Run PX4 SITL + Gazebo Harmonic + ROS2 Jazzy in Docker containers so we can test the full Bennu software stack (camera triggers, geotagging, waypoint missions) without hardware.

**Architecture:** Docker Compose orchestrates two containers: `px4-sitl` (PX4 firmware + Gazebo Harmonic simulation) and `ros2-dev` (ROS2 Jazzy + uXRCE-DDS agent + bennu packages). QGroundControl runs on the host. VS Code devcontainer attaches to `ros2-dev` for IDE access.

**Tech Stack:** PX4 v1.15+, Gazebo Harmonic, ROS2 Jazzy, Docker Compose, uXRCE-DDS, Python

---

## Phase 1: PX4 SITL + Gazebo in Docker

### Task 1: Update Project to ROS2 Jazzy

**Type:** Software
**Files:**
- Modify: `CLAUDE.md`
- Modify: `drone/setup_pi.sh`

**Step 1: Update CLAUDE.md**

Change all references from Humble to Jazzy and Ubuntu 22.04 to 24.04:

```
- **Companion Computer:** Raspberry Pi 5 (8GB), Ubuntu 24.04, ROS2 Jazzy
```

And in Key Commands, add:

```
- Start sim: `cd sim && docker compose up`
```

**Step 2: Update drone/setup_pi.sh**

Replace all `humble` references with `jazzy` and `22.04` with `24.04` in comments:

- Line comment: "Run on a fresh Ubuntu 24.04 Server install on the Pi 5"
- ROS2 install: `ros-jazzy-ros-base ros-dev-tools` instead of `ros-humble-ros-base`
- Bashrc source: `source /opt/ros/jazzy/setup.bash`

**Step 3: Commit and push**

```bash
git add CLAUDE.md drone/setup_pi.sh
git commit -m "refactor: update project from ROS2 Humble to Jazzy"
git push
```

---

### Task 2: Create PX4 SITL Dockerfile

**Type:** Software
**Files:**
- Create: `sim/Dockerfile.px4`

**Step 1: Create sim/ directory**

```bash
mkdir -p sim
```

**Step 2: Create Dockerfile.px4**

```dockerfile
# PX4 SITL + Gazebo Harmonic
# Builds PX4-Autopilot for SITL and runs with Gazebo simulation
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Base dependencies
RUN apt-get update && apt-get install -y \
    git \
    cmake \
    build-essential \
    python3 \
    python3-pip \
    python3-jinja2 \
    python3-empy \
    python3-jsonschema \
    python3-numpy \
    python3-toml \
    python3-packaging \
    python3-yaml \
    python3-requests \
    python3-setuptools \
    python3-cerberus \
    python3-coverage \
    python3-pyulog \
    ninja-build \
    curl \
    wget \
    lsb-release \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Gazebo Harmonic
RUN curl -fsSL https://packages.osrfoundation.org/gazebo.gpg \
    -o /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" \
    | tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null \
    && apt-get update \
    && apt-get install -y gz-harmonic \
    && rm -rf /var/lib/apt/lists/*

# Clone PX4-Autopilot
WORKDIR /opt
RUN git clone --depth 1 --branch v1.15.2 \
    https://github.com/PX4/PX4-Autopilot.git px4 \
    && cd px4 \
    && git submodule update --init --recursive --depth 1

# Build PX4 SITL
WORKDIR /opt/px4
RUN make px4_sitl_default

# Environment
ENV GZ_SIM_RESOURCE_PATH=/opt/px4/Tools/simulation/gz/models:/opt/px4/Tools/simulation/gz/worlds
ENV PX4_SYS_AUTOSTART=4001
ENV PX4_GZ_MODEL=x500
ENV PX4_GZ_MODEL_POSE="0,0,0.1,0,0,0"

# Expose ports
# 14540: QGroundControl MAVLink
# 14580: offboard API
# 8888: uXRCE-DDS
EXPOSE 14540/udp 14580/udp 8888/udp

# Entrypoint: run PX4 SITL with Gazebo
CMD ["bash", "-c", "make px4_sitl gz_x500"]
```

**Step 3: Commit and push**

```bash
git add sim/Dockerfile.px4
git commit -m "feat: add PX4 SITL + Gazebo Harmonic Dockerfile"
git push
```

---

### Task 3: Create ROS2 Dev Dockerfile

**Type:** Software
**Files:**
- Create: `sim/Dockerfile.ros2`

**Step 1: Create Dockerfile.ros2**

```dockerfile
# ROS2 Jazzy + Micro XRCE-DDS Agent + bennu workspace
FROM ros:jazzy

ENV DEBIAN_FRONTEND=noninteractive

# Install additional dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-vcstool \
    exiftool \
    && rm -rf /var/lib/apt/lists/*

# Install Micro XRCE-DDS Agent from source
WORKDIR /opt
RUN git clone --depth 1 https://github.com/eProsima/Micro-XRCE-DDS-Agent.git \
    && cd Micro-XRCE-DDS-Agent \
    && mkdir build && cd build \
    && cmake .. \
    && make -j$(nproc) \
    && make install \
    && ldconfig \
    && rm -rf /opt/Micro-XRCE-DDS-Agent

# Create workspace and clone px4_msgs
WORKDIR /ros2_ws/src
RUN git clone --depth 1 https://github.com/PX4/px4_msgs.git

# Copy bennu packages (will be overridden by volume mount in dev)
COPY drone/ros2_ws/src/bennu_camera /ros2_ws/src/bennu_camera
COPY drone/ros2_ws/src/bennu_bringup /ros2_ws/src/bennu_bringup

# Build workspace
WORKDIR /ros2_ws
RUN . /opt/ros/jazzy/setup.sh \
    && colcon build --symlink-install

# Source workspace in bashrc
RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc \
    && echo "source /ros2_ws/install/setup.bash" >> /root/.bashrc

WORKDIR /ros2_ws

CMD ["bash", "-c", "MicroXRCEAgent udp4 -p 8888"]
```

**Step 2: Create .dockerignore for sim context**

```bash
# sim/.dockerignore is not needed — we use context from project root
```

**Step 3: Commit and push**

```bash
git add sim/Dockerfile.ros2
git commit -m "feat: add ROS2 Jazzy dev container Dockerfile"
git push
```

---

### Task 4: Create Docker Compose and README

**Type:** Software
**Files:**
- Create: `sim/docker-compose.sim.yml`
- Create: `sim/README.md`

**Step 1: Create docker-compose.sim.yml**

```yaml
# Bennu SITL Simulation Stack
# Usage: cd sim && docker compose -f docker-compose.sim.yml up
#
# Starts PX4 SITL with Gazebo Harmonic and ROS2 Jazzy with uXRCE-DDS.
# Connect QGroundControl on host to localhost:14540.

services:
  px4-sitl:
    build:
      context: ..
      dockerfile: sim/Dockerfile.px4
    container_name: bennu-px4-sitl
    environment:
      - DISPLAY=${DISPLAY}
      - QT_QPA_PLATFORM=xcb
      - PX4_SYS_AUTOSTART=4001
      - PX4_GZ_MODEL=x500
    volumes:
      - /tmp/.X11-unix:/tmp/.X11-unix:rw
    ports:
      - "14540:14540/udp"
      - "14580:14580/udp"
    networks:
      - bennu-sim

  ros2-dev:
    build:
      context: ..
      dockerfile: sim/Dockerfile.ros2
    container_name: bennu-ros2-dev
    environment:
      - DISPLAY=${DISPLAY}
      - QT_QPA_PLATFORM=xcb
    volumes:
      - /tmp/.X11-unix:/tmp/.X11-unix:rw
      - ../drone/ros2_ws/src:/ros2_ws/src/bennu:rw
    depends_on:
      - px4-sitl
    networks:
      - bennu-sim
    stdin_open: true
    tty: true

networks:
  bennu-sim:
    driver: bridge
```

**Step 2: Create sim/README.md**

```markdown
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
```

**Step 3: Commit and push**

```bash
git add sim/
git commit -m "feat: add Docker Compose sim stack and README"
git push
```

---

### Task 5: Create VS Code Devcontainer

**Type:** Software
**Files:**
- Create: `.devcontainer/devcontainer.json`

**Step 1: Create .devcontainer/devcontainer.json**

```json
{
    "name": "Bennu ROS2 Dev",
    "dockerComposeFile": ["../sim/docker-compose.sim.yml"],
    "service": "ros2-dev",
    "workspaceFolder": "/ros2_ws",
    "customizations": {
        "vscode": {
            "extensions": [
                "ms-python.python",
                "ms-python.vscode-pylance",
                "ms-iot.vscode-ros",
                "redhat.vscode-xml",
                "redhat.vscode-yaml"
            ],
            "settings": {
                "python.analysis.extraPaths": [
                    "/opt/ros/jazzy/lib/python3.12/dist-packages",
                    "/ros2_ws/install/bennu_camera/lib/python3.12/dist-packages",
                    "/ros2_ws/install/px4_msgs/lib/python3.12/dist-packages"
                ]
            }
        }
    },
    "remoteUser": "root"
}
```

**Step 2: Commit and push**

```bash
git add .devcontainer/
git commit -m "feat: add VS Code devcontainer for ROS2 sim environment"
git push
```

---

## Phase 2: Wire ROS2 Nodes into Sim

### Task 6: Add Sim Mode to camera_node

**Type:** Software
**Files:**
- Modify: `drone/ros2_ws/src/bennu_camera/bennu_camera/camera_node.py`

**Step 1: Update _capture_image to handle missing libcamera**

Replace the `_capture_image` method. When `libcamera-still` is not found (simulation), create a placeholder JPEG instead:

```python
def _capture_image(self):
    """Capture image with libcamera, or create placeholder in sim."""
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
                "-t", "1",
            ],
            check=True,
            capture_output=True,
            timeout=10,
        )
    except FileNotFoundError:
        # Sim mode: create a minimal placeholder JPEG
        self._write_placeholder_jpeg(filepath)
        self.get_logger().info("Sim mode: created placeholder image")
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

def _write_placeholder_jpeg(self, filepath: str):
    """Write a minimal valid JPEG file as a placeholder in simulation."""
    # Minimal 1x1 JPEG
    data = bytes([
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
        0x00, 0x7B, 0x40, 0x1B, 0xFF, 0xD9,
    ])
    with open(filepath, "wb") as f:
        f.write(data)
```

**Step 2: Commit and push**

```bash
git add drone/ros2_ws/src/bennu_camera/
git commit -m "feat: add sim mode to camera_node for placeholder images"
git push
```

---

### Task 7: Add Sim Launch Arguments to Bringup

**Type:** Software
**Files:**
- Modify: `drone/ros2_ws/src/bennu_bringup/launch/drone.launch.py`

**Step 1: Add use_sim argument and conditional DDS transport**

Update the launch file to support both real hardware (serial) and simulation (UDP):

```python
"""Launch file for Bennu drone companion computer.

Starts:
  1. Micro XRCE-DDS agent (PX4 bridge)
  2. Camera capture node

Supports both real hardware (serial) and simulation (UDP).
"""
from launch import LaunchDescription
from launch.actions import ExecuteProcess, DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node


def generate_launch_description():
    use_sim_arg = DeclareLaunchArgument(
        "use_sim",
        default_value="false",
        description="Use simulation mode (UDP instead of serial)",
    )

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

    # DDS agent for real hardware (serial)
    dds_agent_serial = ExecuteProcess(
        cmd=[
            "MicroXRCEAgent",
            "serial",
            "--dev", LaunchConfiguration("serial_port"),
            "-b", LaunchConfiguration("baud_rate"),
        ],
        name="uxrce_dds_agent",
        output="screen",
        condition=UnlessCondition(LaunchConfiguration("use_sim")),
    )

    # DDS agent for simulation (UDP)
    dds_agent_udp = ExecuteProcess(
        cmd=[
            "MicroXRCEAgent",
            "udp4",
            "-p", "8888",
        ],
        name="uxrce_dds_agent",
        output="screen",
        condition=IfCondition(LaunchConfiguration("use_sim")),
    )

    # Camera capture node
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
        use_sim_arg,
        output_dir_arg,
        serial_port_arg,
        baud_rate_arg,
        dds_agent_serial,
        dds_agent_udp,
        camera_node,
    ])
```

**Step 2: Commit and push**

```bash
git add drone/ros2_ws/src/bennu_bringup/
git commit -m "feat: add use_sim launch argument for UDP transport in simulation"
git push
```

---

### Task 8: Update Memory and Documentation

**Type:** Documentation
**Files:**
- Modify: auto-memory MEMORY.md
- Verify: design doc references are consistent

**Step 1: Update MEMORY.md**

Update tech stack to reflect Jazzy and sim setup:
- ROS2 Humble → ROS2 Jazzy
- Ubuntu 22.04 → Ubuntu 24.04
- Add sim/ to repo structure
- Update implementation status

**Step 2: Commit and push**

```bash
git add CLAUDE.md
git commit -m "docs: update documentation for ROS2 Jazzy and sim setup"
git push
```

---

## Summary Checklist

| Task | Type | Phase | Description |
|------|------|-------|-------------|
| 1 | Refactor | Setup | Update project from Humble to Jazzy |
| 2 | Software | 1 | PX4 SITL + Gazebo Harmonic Dockerfile |
| 3 | Software | 1 | ROS2 Jazzy dev container Dockerfile |
| 4 | Software | 1 | Docker Compose + sim README |
| 5 | Software | 1 | VS Code devcontainer |
| 6 | Software | 2 | Sim mode in camera_node (placeholder images) |
| 7 | Software | 2 | Sim launch arguments in bringup |
| 8 | Docs | 2 | Update memory and documentation |
