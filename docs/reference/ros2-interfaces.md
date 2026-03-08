# ROS2 Interfaces

Topics, parameters, and launch arguments for Bennu's ROS2 packages.

## Packages

| Package | Description |
|---|---|
| `bennu_camera` | Camera capture + geotagging node |
| `bennu_bringup` | Launch files + configuration |

## Subscribed Topics

| Topic | Message Type | Description |
|---|---|---|
| `/fmu/out/vehicle_global_position` | `px4_msgs/VehicleGlobalPosition` | GPS latitude, longitude, altitude from PX4 |
| `/fmu/out/camera_trigger` | `px4_msgs/CameraTrigger` | Camera trigger event from PX4 distance-based trigger |

## Node Parameters (camera_capture_node)

| Parameter | Default | Description |
|---|---|---|
| `output_dir` | `/home/pi/captures` | Directory for captured images |
| `image_width` | `4056` | Capture width in pixels |
| `image_height` | `3040` | Capture height in pixels |

## Launch Arguments (drone.launch.py)

| Argument | Default | Description |
|---|---|---|
| `use_sim` | `false` | Use simulation mode (UDP transport) |
| `output_dir` | `/home/pi/captures` | Image output directory |
| `serial_port` | `/dev/ttyAMA0` | Serial port for uXRCE-DDS |
| `baud_rate` | `921600` | UART baud rate |
