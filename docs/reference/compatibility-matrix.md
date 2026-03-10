# Compatibility Matrix

Pinned versions of all major components in the Bennu stack. These versions are tested together.

## Current Matrix

| Component | Version | Pin Location | Notes |
|-----------|---------|-------------|-------|
| PX4 Autopilot | v1.16.1 | `sim/Dockerfile.px4` | Pinned tag |
| ROS2 | Jazzy Jalisco | `sim/Dockerfile.ros2` (ros:jazzy) | Ubuntu 24.04 |
| px4_msgs | v1.16.1 tag | `sim/Dockerfile.ros2` | Must match PX4 version exactly |
| Micro-XRCE-DDS Agent | latest (from source) | `sim/Dockerfile.ros2` | Built from eProsima repo |
| Gazebo | Harmonic | `sim/Dockerfile.px4` | SITL only |
| Python | 3.12 | Ubuntu 24.04 default | System Python |
| Ubuntu | 24.04 LTS | Both Dockerfiles | Pi 5 and Docker base |
| PyNaCl | >=1.5,<2 | `sim/Dockerfile.ros2` | Ed25519 signing |
| jsonschema | >=4,<5 | `sim/Dockerfile.ros2` | Contract validation |
| MAVSDK | >=2,<3 | `sim/Dockerfile.ros2` | Mission execution |

## Upgrade Policy

- **PX4 + px4_msgs:** Upgrade together. Test SITL before deploying to hardware.
- **ROS2:** Track Ubuntu LTS releases. Next: ROS2 K-Turtle with Ubuntu 26.04.
- **XRCE-DDS:** Rebuild from source when upgrading ROS2.
- **Python packages:** Pin major versions, allow minor updates.

## Known Incompatibilities

- px4_msgs version must exactly match PX4 version — mismatched message definitions cause silent deserialization errors.
- Gazebo Garden (previous gen) is not compatible with PX4 v1.16 SITL model paths.
