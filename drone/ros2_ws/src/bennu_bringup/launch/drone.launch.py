"""Launch file for Bennu drone companion computer.

Starts:
  1. Micro XRCE-DDS agent (PX4 bridge)
  2. Camera capture node
"""
from launch import LaunchDescription
from launch.actions import ExecuteProcess, DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
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

    # Start Micro XRCE-DDS agent
    dds_agent = ExecuteProcess(
        cmd=[
            "micro-xrce-dds-agent",
            "serial",
            "--dev", LaunchConfiguration("serial_port"),
            "-b", LaunchConfiguration("baud_rate"),
        ],
        name="uxrce_dds_agent",
        output="screen",
    )

    # Start camera capture node
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
        output_dir_arg,
        serial_port_arg,
        baud_rate_arg,
        dds_agent,
        camera_node,
    ])
