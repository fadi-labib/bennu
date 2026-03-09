# ROS2 Ecosystem

Evaluated open-source ROS2 packages for Bennu's photogrammetry drone stack (PX4 v1.16+, ROS2 Jazzy, Raspberry Pi 5, uXRCE-DDS). Packages are assessed for Jazzy compatibility, fit with Bennu's architecture, and maintenance status.

See [ADR-005](../decisions/005-ros2-oss-package-adoption.md) for the adoption decision and phased rollout.

## Adoption Summary

| Package | Category | Status | Phase |
|---|---|---|---|
| `px4_msgs` | PX4 Integration | **Adopted** | Current |
| `ros_gz_bridge` | Gazebo Bridge | **Planned** | Tier 1 |
| `ros_gz_image` | Gazebo Bridge | **Planned** | Tier 1 |
| `launch_testing_ros2` | Testing | **Planned** | Tier 1 |
| `diagnostic_updater` | Diagnostics | **Planned** | Tier 1 |
| `rosbag2_storage_mcap` | Recording | **Planned** | Tier 2 |
| `foxglove_bridge` | Debugging | **Planned** | Tier 2 |
| `image_transport` | Camera Pipeline | **Planned** | Tier 3 |
| `compressed_image_transport` | Camera Pipeline | **Planned** | Tier 3 |
| `camera_info_manager` | Camera Pipeline | **Planned** | Tier 3 |
| `camera_calibration` | Camera Pipeline | **Planned** | Tier 3 |
| `image_pipeline` | Camera Pipeline | **Planned** | Tier 3 |
| `px4_ros2_msg_translation_node` | PX4 Integration | **Evaluate Later** | Phase 3 |
| `px4-ros2-interface-lib` | PX4 Integration | **Evaluate Later** | Phase 3 |
| `robot_localization` | Localization | **Evaluate Later** | Phase 3 |
| `Aerostack2` | Autonomy | **Evaluate Later** | Phase 3+ |
| `apriltag_detector` | Testing | **Evaluate Later** | Phase 3+ |
| `camera_ros` | Camera Driver | **Monitor** | — |
| `gps_umd` | GPS | **Monitor** | — |
| `px4_ros_com` | PX4 Integration | **Not Recommended** | — |
| `v4l2_camera` | Camera Driver | **Not Recommended** | — |
| `MAVROS` | PX4 Integration | **Not Recommended** | — |

---

## PX4-ROS2 Integration

### px4_msgs

- **Repo:** [PX4/px4_msgs](https://github.com/PX4/px4_msgs)
- **What:** ROS2 message definitions matching PX4's internal uORB messages. Every ROS2 node that communicates with PX4 over uXRCE-DDS needs these types (`VehicleCommand`, `SensorGps`, `VehicleOdometry`, `BatteryStatus`, etc.).
- **Jazzy:** Yes. Auto-exported from PX4 main/release branches. Service message translation requires Jazzy or later.
- **Fit:** Essential. Already cloned in `Dockerfile.ros2` and used by `bennu_camera`.
- **Maintained:** Yes, by the PX4 project. Updated with every release.

### px4_ros2_msg_translation_node

- **Repo:** Part of [Auterion/px4-ros2-interface-lib](https://github.com/Auterion/px4-ros2-interface-lib)
- **Docs:** [PX4 Message Translation Node](https://docs.px4.io/main/en/ros2/px4_ros2_msg_translation_node.html)
- **What:** Starting with PX4 v1.16, ROS2 applications may use a different version of `px4_msgs` than what PX4 was built with. This node dynamically converts messages between versions using topic name versioning.
- **Jazzy:** Yes.
- **Fit:** Important when PX4 firmware updates independently of the ROS2 workspace. Not urgent while development tracks a single PX4 version.
- **Maintained:** Yes, by Auterion/PX4.

### px4-ros2-interface-lib

- **Repo:** [Auterion/px4-ros2-interface-lib](https://github.com/Auterion/px4-ros2-interface-lib)
- **Docs:** [PX4 ROS 2 Interface Library](https://docs.px4.io/main/en/ros2/px4_ros2_interface_lib)
- **What:** C++ library for creating custom flight modes in ROS2 that register with PX4 and appear as native modes in QGroundControl. Provides typed setpoint interfaces (`MulticopterGotoSetpointType`), telemetry wrappers, integrated failsafe/arming checks, and mode lifecycle management.
- **Jazzy:** Yes.
- **Fit:** High value for Phase 3 autonomy. A "PhotoSurvey" flight mode could appear in QGC. However, it is C++ only — Bennu uses Python nodes. Would need a Python wrapper or serve as architectural inspiration.
- **Maintained:** Yes, under active development.

### px4_ros_com — Not Recommended

- **Repo:** [PX4/px4_ros_com](https://github.com/PX4/px4_ros_com)
- **What:** Historically provided the ROS2/PX4 bridge. As of PX4 v1.14+, it is no longer required for communication — uXRCE-DDS handles that directly. Now serves only as example code.
- **Fit:** Reference only. Do not depend on it as infrastructure.
- **Maintained:** Minimally.

---

## Camera & Image Pipeline

### camera_ros

- **Repo:** [christianrauch/camera_ros](https://github.com/christianrauch/camera_ros)
- **Docs:** [camera_ros on ROS Index](https://index.ros.org/p/camera_ros/) | [Jazzy docs](https://docs.ros.org/en/jazzy/p/camera_ros/)
- **What:** ROS2 node that interfaces with cameras through libcamera. Publishes `sensor_msgs/Image` and `CameraInfo`. Provides a service to set camera parameters (exposure, gain) at runtime.
- **Jazzy:** Yes, available as `ros-jazzy-camera-ros`.
- **Fit:** Could replace Bennu's custom `LibcameraBackend` subprocess calls with a proper ROS2 image publisher. **Caveat:** The bloomed version uses upstream libcamera, which may lack full IMX477 support. For complete Pi camera module support, build against the [Raspberry Pi fork of libcamera](https://github.com/raspberrypi/libcamera).
- **Trade-off:** `camera_ros` is designed for continuous streaming. Bennu's architecture is event-triggered (capture on PX4 camera trigger). A hybrid approach could use `camera_ros` for preview/calibration and keep the subprocess call for high-res survey captures.
- **Maintained:** Yes, by Christian Rauch.

### v4l2_camera — Not Recommended

- **Repo:** [boldhearts/ros2_v4l2_camera](https://gitlab.com/boldhearts/ros2_v4l2_camera)
- **What:** ROS2 camera driver using Video4Linux2.
- **Fit:** Not suitable for the IMX477. Pi camera modules use the Broadcom Unicam V4L2 driver, which provides raw Bayer images only. The libcamera-based `camera_ros` is the correct choice for Pi cameras. Could be useful for a future USB camera addition.
- **Maintained:** Yes.

### image_pipeline

- **Docs:** [image_pipeline overview](https://docs.ros.org/en/kilted/p/image_pipeline/)
- **What:** Stack of ROS2 packages for processing raw camera images: rectification (removing lens distortion), stereo processing, depth image handling, and point cloud generation.
- **Jazzy:** Yes.
- **Fit:** The `image_proc` node handles image rectification using camera calibration data — essential for photogrammetry where lens distortion must be corrected. Relevant when Bennu publishes `sensor_msgs/Image` rather than writing files directly.
- **Maintained:** Yes, by ros-perception.

### camera_calibration

- **Docs:** [camera_calibration Jazzy](https://docs.ros.org/en/ros2_packages/jazzy/api/camera_calibration/doc/index.html)
- **What:** Interactive camera calibration tool using a checkerboard pattern. Outputs intrinsic parameters and distortion coefficients as a `CameraInfo` YAML file.
- **Jazzy:** Yes.
- **Fit:** Run once with the IMX477 + 6mm lens to generate calibration data. Store in `config/camera/`. OpenDroneMap can use this for better reconstruction.
- **Maintained:** Yes, part of image_pipeline.

### camera_info_manager

- **Docs:** [camera_info_manager Jazzy](https://docs.ros.org/en/ros2_packages/jazzy/api/camera_info_manager/)
- **What:** Manages `CameraInfo` messages for camera drivers. Loads calibration YAML files and publishes them alongside image topics.
- **Jazzy:** Yes.
- **Fit:** Pairs with `camera_calibration` — once calibration is done, this package loads and serves the calibration data. Useful when Bennu adopts standard image transport.
- **Maintained:** Yes.

### image_transport + compressed_image_transport

- **Docs:** [image_transport Jazzy](https://docs.ros.org/en/ros2_packages/jazzy/api/image_transport/)
- **What:** Transparent pub/sub for images in compressed formats. Plugins include `compressed_image_transport` (JPEG/PNG), `theora_image_transport` (video stream), and `ffmpeg_image_transport` (H.264/H.265).
- **Jazzy:** Yes. All plugins released for Jazzy as of February 2025.
- **Fit:** Useful for bandwidth-limited scenarios: WiFi image preview during development, compressed rosbag recording (~10x size reduction). Not needed until camera node publishes `sensor_msgs/Image`.
- **Maintained:** Yes.

### libcamera_ros_driver (CTU-MRS)

- **Repo:** [ctu-mrs/libcamera_ros_driver](https://github.com/ctu-mrs/libcamera_ros_driver)
- **What:** Fork of `camera_ros` from the Czech Technical University's Multi-Robot Systems group, tailored for their drone platforms.
- **Fit:** Worth monitoring as an alternative if you encounter issues with mainline `camera_ros`.

---

## Gazebo-ROS2 Bridge

### ros_gz_bridge

- **Docs:** [ros_gz_bridge Jazzy](https://docs.ros.org/en/ros2_packages/jazzy/api/ros_gz_bridge/)
- **Source:** [gazebosim/ros_gz](https://github.com/gazebosim/ros_gz)
- **What:** Bidirectional bridge between Gazebo Harmonic topics and ROS2 topics. Configured via YAML file specifying topic mappings and message type conversions. Supports sensor data (images, IMU, GPS, lidar) and control inputs.
- **Jazzy:** Yes. Gazebo Harmonic is the [paired Gazebo release](https://gazebosim.org/docs/harmonic/ros_installation) for ROS2 Jazzy.
- **Fit:** Directly enables Bennu's planned `camera_backend:=rendered` mode. Instead of custom bridge code, a YAML config maps the Gazebo camera sensor topic to a ROS2 `sensor_msgs/Image` topic that the `RenderedBackend` subscribes to.
- **Maintained:** Yes, by the Gazebo project.

### ros_gz_image

- **Docs:** [ros_gz_image Jazzy](https://docs.ros.org/en/jazzy/p/ros_gz_image/__README.html)
- **What:** GPU-accelerated image format conversion between Gazebo and ROS2. Handles pixel format differences efficiently.
- **Jazzy:** Yes.
- **Fit:** Complements `ros_gz_bridge` for image-heavy workloads. Note: if CI runs headless without GPU, `ros_gz_bridge` alone with software rendering may suffice. Test in your GitHub Actions runner.
- **Maintained:** Yes, part of ros_gz.

---

## GPS & Localization

### gps_umd (gps_msgs, gpsd_client, gps_tools)

- **Repo:** [swri-robotics/gps_umd](https://github.com/swri-robotics/gps_umd)
- **Docs:** [gps_msgs on ROS Index](https://index.ros.org/p/gps_msgs/)
- **What:** Three packages: `gps_msgs` (extended GPS message types beyond `sensor_msgs/NavSatFix`), `gpsd_client` (ROS2 interface to gpsd daemon), `gps_tools` (utilities). `GPSFix` message has more fields than `NavSatFix` (track, speed, DOP values).
- **Jazzy:** Yes, released for Jazzy.
- **Fit:** PX4 already provides GPS data via uXRCE-DDS (`SensorGps` uORB message), so `gpsd_client` is unnecessary. `gps_msgs` could be useful for richer geotagging metadata (DOP values for quality assessment).
- **Maintained:** Yes, by SwRI.

### sensor_msgs/NavSatFix (standard)

- **Repo:** [ros2/common_interfaces](https://github.com/ros2/common_interfaces/blob/master/sensor_msgs/msg/NavSatFix.msg)
- **What:** The standard ROS2 message for GNSS fixes. Contains latitude, longitude, altitude, covariance, and fix status.
- **Fit:** If you need interoperability with standard ROS2 tools (robot_localization, Nav2), write a small translator node that converts PX4's `SensorGps` to `NavSatFix`.

### robot_localization

- **Repo:** [robot_localization on ROS Index](https://index.ros.org/p/robot_localization/)
- **Docs:** [Sensor Fusion with ROS 2 Jazzy](https://automaticaddison.com/sensor-fusion-and-robot-localization-using-ros-2-jazzy/)
- **What:** EKF/UKF sensor fusion nodes plus `navsat_transform_node` for GPS→local Cartesian conversion. Common architecture: two EKF instances (odometry+IMU, plus GPS fusion).
- **Jazzy:** Yes.
- **Fit:** Useful for Phase 3 if you need precision position estimates beyond PX4's internal EKF. For photogrammetry geotagging, PX4's own GPS data is sufficient. Relevant if you add external sensors (optical flow, VIO).
- **Maintained:** Yes.

---

## Recording & Debugging

### rosbag2_storage_mcap

- **Docs:** [rosbag2_storage_mcap Jazzy](https://docs.ros.org/en/jazzy/p/rosbag2_storage_mcap/index.html)
- **What:** MCAP storage backend for rosbag2. MCAP is the modern rosbag format — better compression, faster seeking, and directly viewable in Foxglove Studio.
- **Jazzy:** Yes.
- **Fit:** Record SITL runs for replay and debugging. Supports Bennu's artifact-based test strategy — recorded bags can be replayed through the `camera_backend:=replay` path. MCAP is the recommended format over SQLite3.
- **Maintained:** Yes, by Foxglove.

### foxglove_bridge

- **Docs:** [foxglove_bridge Jazzy](https://docs.ros.org/en/jazzy/p/foxglove_bridge/__README.html)
- **What:** WebSocket bridge that connects Foxglove Studio to a live ROS2 system. Allows real-time visualization of topics, TF trees, images, and diagnostics in a browser — no X11 or GPU required.
- **Jazzy:** Yes.
- **Fit:** Replaces the need for `rqt` or `rviz2` (which require X11/GPU). Excellent for debugging sim runs from the host machine. Works with the diagnostics stack for system health dashboards.
- **Maintained:** Yes, by Foxglove.

---

## Testing

### launch_testing_ros2

- **Docs:** [launch_testing_ros2 Jazzy](https://docs.ros.org/en/jazzy/p/launch_testing_ros/index.html)
- **What:** Framework for launch-level integration tests. Start a launch file, wait for nodes to come up, run assertions against topics and services, then tear down. Tests run as pytest fixtures.
- **Jazzy:** Yes.
- **Fit:** Fills the gap between Bennu's unit tests (pytest) and SITL scenario tests (MAVSDK). Test that `drone.launch.py` brings up the right nodes with correct parameters. Zero architecture impact — only adds test infrastructure.
- **Maintained:** Yes, part of the ROS2 launch framework.

---

## Diagnostics

### diagnostic_updater + diagnostic_aggregator

- **Docs:** [diagnostic_updater Jazzy](https://docs.ros.org/en/jazzy/p/diagnostic_updater/) | [Practical Guide](https://foxglove.dev/blog/a-practical-guide-to-using-ros-diagnostics)
- **What:** Standardized framework for monitoring node health. `diagnostic_updater` lets nodes publish status (OK/WARN/ERROR) with key-value pairs. `diagnostic_aggregator` groups and summarizes diagnostics from all nodes.
- **Jazzy:** Yes.
- **Fit:** Add to `bennu_camera` to report: capture rate, backend status, GPS staleness, disk space, DDS bridge health. ~15 lines of Python to integrate. Artifact-based assertions can check diagnostics. View in Foxglove.
- **Maintained:** Yes.

---

## Autonomy Frameworks

### Aerostack2

- **Repo:** [aerostack2/aerostack2](https://github.com/aerostack2/aerostack2)
- **What:** Comprehensive ROS2 framework for autonomous multi-aerial-robot systems. Plugin-based backends for different autopilots (including PX4), behavior trees for mission planning, task delegation. Supports heterogeneous fleets.
- **Jazzy:** Active development; check repo for latest distro support.
- **Fit:** Most feature-complete ROS2 drone autonomy framework. Could replace custom mission planning code. Overkill for a single-drone photogrammetry project at current scope. Best used as a reference architecture.
- **Maintained:** Yes, by Universidad Politécnica de Madrid.

### Nav2 GPS Waypoint Following

- **Docs:** [Nav2 GPS Navigation Tutorial](https://docs.nav2.org/tutorials/docs/navigation2_with_gps.html)
- **What:** Nav2's waypoint follower has a `/follow_gps_waypoints` action server that accepts GPS coordinates, converts to Cartesian via `robot_localization`, and executes sequentially.
- **Jazzy:** Yes. GPS waypoint following works on Jazzy and Rolling.
- **Fit:** The GPS waypoint concept is relevant, but Nav2 is a 2D ground-robot stack. 3D drone navigation is a stated stretch goal but not production-ready. PX4's built-in mission mode or custom offboard logic is more practical for survey missions.
- **Maintained:** Yes, by Open Navigation LLC.

### apriltag_detector

- **Docs:** [apriltag_detector Rolling](https://docs.ros.org/en/ros2_packages/rolling/api/apriltag_detector/)
- **What:** Detects AprilTag fiducial markers in camera images. Provides pose estimation relative to known tag geometry.
- **Jazzy:** Available on Rolling; check Jazzy availability.
- **Fit:** Useful for landing-pad detection in simulation, calibration target ground-truth, and camera/pose verification. Nice-to-have, not blocking.

---

## Reference Projects

Open-source projects with similar architecture to Bennu. Study for design patterns, not as dependencies.

### Marnonel6/ROS2_offboard_drone_control

- **Repo:** [github.com/Marnonel6/ROS2_offboard_drone_control](https://github.com/Marnonel6/ROS2_offboard_drone_control)
- **Project page:** [marnonel6.github.io](https://marnonel6.github.io/projects/0-autonomous-px4-drone)
- **What:** Complete autonomous drone with ROS2 offboard control on Pixhawk 6X + Raspberry Pi 4B, communicating via uXRCE-DDS over serial. Implements RRT path planning and waypoint following. Physical build with real hardware.
- **Why it matters:** Closest architectural match to Bennu. Same stack: Pixhawk + Pi + PX4 + ROS2 + uXRCE-DDS serial. Study node architecture, launch file organization, and DDS configuration. Differences: Pi 4B (not 5), Humble (not Jazzy), C++ (not Python).

### JacopoPan/aerial-autonomy-stack

- **Repo:** [github.com/JacopoPan/aerial-autonomy-stack](https://github.com/JacopoPan/aerial-autonomy-stack)
- **Paper:** [arxiv.org/html/2602.07264v1](https://arxiv.org/html/2602.07264v1)
- **What:** Multi-drone PX4/ArduPilot ROS2 framework with YOLO, LiDAR, Dockerized Gym simulation, and JetPack deployment. Supports 10x faster-than-real-time SITL simulation, synchronous stepping, and Jetson-in-the-loop testing. v0.1.0 released 2026.
- **Why it matters:** The Dockerized simulation architecture and faster-than-real-time SITL could accelerate Bennu's test cycles. The autopilot-agnostic ROS2 action interface is well designed. Targets perception-based autonomy rather than photogrammetry.

### ARK-Electronics/ROS2_PX4_Offboard_Example

- **Repo:** [github.com/ARK-Electronics/ROS2_PX4_Offboard_Example](https://github.com/ARK-Electronics/ROS2_PX4_Offboard_Example)
- **What:** Beginner-friendly example of PX4 velocity setpoint control with ROS2 teleop. Keyboard control of drone velocity in offboard mode.
- **Why it matters:** Clean reference for the offboard control handshake in Python/ROS2: arming, mode switching, setpoint streaming.

### SathanBERNARD/PX4-ROS2-Gazebo-Drone-Simulation-Template

- **Repo:** [github.com/SathanBERNARD/PX4-ROS2-Gazebo-Drone-Simulation-Template](https://github.com/SathanBERNARD/PX4-ROS2-Gazebo-Drone-Simulation-Template)
- **What:** Docker-based simulation template for a camera-equipped quadcopter. PX4 SITL + Gazebo Harmonic + ROS2. Designed for mission planning and computer vision development.
- **Why it matters:** Compare with Bennu's `sim/` stack. Good reference for Docker Compose patterns and camera simulation in Gazebo.

### ParsaKhaledi/px4_sim_ros2

- **Repo:** [github.com/ParsaKhaledi/px4_sim_ros2](https://github.com/ParsaKhaledi/px4_sim_ros2)
- **What:** Drone simulation with ROS2, PX4, Nav2, and Gazebo Harmonic. Uses PX4 v1.15.4 in Docker.
- **Why it matters:** Demonstrates Nav2 integration with PX4 drones in simulation — relevant if Bennu explores GPS waypoint following.

### OS-RFODG (Open-source ROS2 Framework for Outdoor UAV Dataset Generation)

- **Paper:** [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2590123025026829)
- **What:** Integrates ROS2 with PX4 + Gazebo + QGroundControl for collecting synchronized multi-sensor UAV data (LiDAR, GPS, IMU, camera, barometer). Can generate Digital Surface Models via UAV photogrammetry. Published 2025.
- **Why it matters:** The architecture for synchronized sensor data collection is directly relevant to Bennu's data acquisition pipeline. Research framework, not a reusable package.

---

## Further Reading

- [PX4 ROS 2 User Guide](https://docs.px4.io/main/en/ros2/user_guide) — Official PX4-ROS2 integration documentation
- [uXRCE-DDS Bridge](https://docs.px4.io/main/en/middleware/uxrce_dds) — How PX4 exposes uORB topics as ROS2 topics
- [Gazebo Harmonic ROS 2 Integration](https://gazebosim.org/docs/harmonic/ros2_integration/) — Gazebo-ROS2 bridge setup and topic mapping
- [Gazebo Jazzy/Harmonic Compatibility](https://gazebosim.org/docs/harmonic/ros_installation) — Supported ROS2/Gazebo version pairs
- [ROS-Aerial Community](https://ros-aerial.github.io/aerial_robotic_landscape/) — Community landscape of ROS2 aerial robotics
- [Aerial Robotics Landscape](https://ros-aerial.github.io/aerial_robotic_landscape/aerial_autonomy_stacks/) — Survey of autonomy stacks
- [Dronecode at ROSCon 2025](https://dronecode.org/dronecode-at-roscon-2025-expanding-open-collaboration-between-px4-and-ros-2/) — PX4-ROS2 roadmap
- [Raspberry Pi Companion with Pixhawk](https://docs.px4.io/main/en/companion_computer/pixhawk_rpi) — PX4 setup for Pi companion
- [PX4 Offboard Control Example](https://docs.px4.io/main/en/ros2/offboard_control) — Official offboard control tutorial
- [Piexif Geotagging Tutorial](https://hatarilabs.com/ih-en/how-to-geolocate-drone-imagery-from-a-csv-table-with-python-and-piexif-tutorial) — EXIF GPS metadata with Python
