# ADR-005: ROS2 OSS Package Adoption Strategy

## Status

Accepted

## Context

Bennu currently has two custom ROS2 packages (`bennu_camera`, `bennu_bringup`) with minimal external dependencies beyond `px4_msgs`, `rclpy`, and `sensor_msgs`. As the project evolves through the platform-readiness phases, we need to decide which OSS packages to adopt versus building custom, and in what order.

We evaluated ~25 packages across 9 categories: PX4 integration, camera/image pipeline, Gazebo bridging, GPS/localization, recording/debugging, testing, diagnostics, autonomy frameworks, and reference projects.

Key constraints:

- **Jazzy compatibility required** — all adopted packages must have ROS2 Jazzy releases.
- **Headless CI** — packages must work without GPU or X11 in GitHub Actions.
- **Python-first** — Bennu nodes are Python; C++-only packages are deferred unless wrappable.
- **PX4 uXRCE-DDS is the primary bridge** — packages that assume MAVROS are not suitable.
- **Event-triggered capture** — Bennu captures images on PX4 camera trigger events, not continuous streaming.

## Decision

Adopt OSS packages in four tiers, aligned with project phases:

### Tier 1 — Immediate (supports current SITL and camera refactor work)

| Package | Purpose |
|---|---|
| `ros_gz_bridge` | Bridge Gazebo Harmonic camera sensors into ROS2 for `camera_backend:=rendered` |
| `ros_gz_image` | GPU-accelerated image format conversion between Gazebo and ROS2 |
| `launch_testing_ros2` | Launch-level integration tests for `drone.launch.py` and `bennu_bringup` |
| `diagnostic_updater` | Node health reporting (capture rate, GPS staleness, disk space, backend status) |

These are installed via `apt` in `Dockerfile.ros2`:

```
ros-jazzy-ros-gz-bridge
ros-jazzy-ros-gz-image
ros-jazzy-launch-testing-ros2
ros-jazzy-diagnostic-updater
```

### Tier 2 — Recording & Debugging (supports artifact-based test strategy)

| Package | Purpose |
|---|---|
| `rosbag2_storage_mcap` | MCAP format rosbag recording for SITL runs, replay backend, and debugging |
| `foxglove_bridge` | WebSocket bridge for browser-based visualization without X11/GPU |

### Tier 3 — Camera Pipeline Maturity (supports real hardware path)

| Package | Purpose |
|---|---|
| `image_transport` | Bandwidth-efficient image pub/sub with compression plugins |
| `compressed_image_transport` | JPEG/PNG compression for rosbag recording and WiFi preview |
| `camera_info_manager` | Loads and serves lens calibration YAML files alongside image topics |
| `camera_calibration` | Checkerboard-based intrinsic calibration for IMX477 + 6mm lens |
| `image_pipeline` | Image rectification using calibration data |

### Tier 4 — Evaluate in Phase 3+ (autonomy)

| Package | Trigger |
|---|---|
| `px4_ros2_msg_translation_node` | When PX4 firmware and px4_msgs versions diverge |
| `px4-ros2-interface-lib` | When mission execution moves from MAVSDK into ROS2 nodes |
| `robot_localization` | When external sensors (optical flow, VIO) are added beyond PX4's EKF |
| `Aerostack2` | When scope grows to multi-vehicle operations |
| `apriltag_detector` | When landing-pad or calibration ground-truth testing is needed |

### Not Adopted

| Package | Reason |
|---|---|
| `px4_ros_com` | Vestigial since PX4 v1.14+. uXRCE-DDS replaces it entirely. |
| `v4l2_camera` | Pi camera modules need libcamera, not V4L2. Raw Bayer output only via V4L2. |
| `MAVROS` | Bennu's architecture uses uXRCE-DDS as the primary PX4 bridge ([ADR-004](004-uxrce-dds-over-mavros.md)). MAVROS adds a MAVLink translation layer. |
| `camera_ros` | Designed for continuous streaming, not event-triggered capture. Monitor for future hybrid use (preview/calibration). |
| `Nav2` | Fundamentally a 2D ground-robot stack. 3D drone navigation is a stretch goal, not production-ready. PX4's built-in mission mode is more practical. |

## Consequences

**Positive:**

- Standard ROS2 interfaces improve interoperability with community tools (Foxglove, rosbag2, image_pipeline).
- Reduced custom code — `ros_gz_bridge` replaces custom Gazebo-to-ROS2 bridge code for the rendered backend.
- `diagnostic_updater` gives system health visibility at low integration cost (~15 lines per node).
- `launch_testing_ros2` fills the test gap between unit tests and full SITL scenario tests.
- Tiered adoption prevents premature complexity while keeping a clear upgrade path.

**Negative:**

- Docker image size increases with each tier of `apt` packages.
- Version pinning overhead — must track Jazzy release compatibility across packages.
- `ros_gz_image` may not work in headless CI without GPU; may need to fall back to `ros_gz_bridge` with software rendering.

**Neutral:**

- No photogrammetry-specific ROS2 package exists. The photogrammetry pipeline remains post-processing (OpenDroneMap). ROS2's role is data acquisition only, which Bennu's architecture already handles correctly.
- MAVSDK remains the external mission runner for SITL tests. The PX4 ROS2 Interface Library is deferred until mission execution moves into ROS2 nodes.
