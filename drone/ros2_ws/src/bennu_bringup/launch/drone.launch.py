"""Launch file for Bennu drone companion computer.

Starts:
  1. Micro XRCE-DDS agent (PX4 bridge)
  2. Camera capture node

Supports both real hardware (serial) and simulation (UDP).
"""
from launch import LaunchDescription
from launch.actions import ExecuteProcess, DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration
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

    dds_agent_binary_arg = DeclareLaunchArgument(
        "dds_agent_binary",
        default_value="MicroXRCEAgent",
        description="XRCE-DDS agent binary name (MicroXRCEAgent or micro_ros_agent)",
    )

    camera_backend_arg = DeclareLaunchArgument(
        "camera_backend",
        default_value="libcamera",
        description="Camera capture backend (libcamera, placeholder)",
    )

    # DDS agent for real hardware (serial)
    dds_agent_serial = ExecuteProcess(
        cmd=[
            LaunchConfiguration("dds_agent_binary"),
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
            LaunchConfiguration("dds_agent_binary"),
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
            {"camera_backend": LaunchConfiguration("camera_backend")},
        ],
        output="screen",
    )

    return LaunchDescription([
        use_sim_arg,
        output_dir_arg,
        serial_port_arg,
        baud_rate_arg,
        dds_agent_binary_arg,
        camera_backend_arg,
        dds_agent_serial,
        dds_agent_udp,
        camera_node,
    ])
