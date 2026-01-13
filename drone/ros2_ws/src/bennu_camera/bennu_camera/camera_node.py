"""
Bennu Camera Node — captures geotagged images triggered by PX4.

Subscribes to PX4 camera trigger events via uXRCE-DDS,
captures images using libcamera, and writes GPS EXIF data.
"""
import os
import subprocess
from datetime import datetime

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from bennu_camera.geotag import write_gps_exif


class CameraNode(Node):
    """ROS2 node that captures geotagged images on PX4 camera trigger."""

    def __init__(self):
        super().__init__("camera_capture_node")

        # Parameters
        self.declare_parameter("output_dir", "/home/pi/captures")
        self.declare_parameter("image_width", 4056)
        self.declare_parameter("image_height", 3040)

        self.output_dir = self.get_parameter("output_dir").value
        self.width = self.get_parameter("image_width").value
        self.height = self.get_parameter("image_height").value

        os.makedirs(self.output_dir, exist_ok=True)

        # Latest GPS position (updated continuously)
        self._lat = 0.0
        self._lon = 0.0
        self._alt = 0.0

        # QoS for PX4 topics
        qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=5,
        )

        # Subscribe to PX4 vehicle GPS position
        try:
            from px4_msgs.msg import VehicleGlobalPosition, CameraTrigger

            self.create_subscription(
                VehicleGlobalPosition,
                "/fmu/out/vehicle_global_position",
                self._on_gps,
                qos,
            )

            self.create_subscription(
                CameraTrigger,
                "/fmu/out/camera_trigger",
                self._on_trigger,
                qos,
            )
            self.get_logger().info("Subscribed to PX4 topics via uXRCE-DDS")
        except ImportError:
            self.get_logger().warn(
                "px4_msgs not found — running in standalone timer mode"
            )
            # Fallback: capture on timer (for testing without PX4)
            self.create_timer(5.0, self._on_timer_capture)

        self._capture_count = 0
        self.get_logger().info(
            f"Camera node started. Output: {self.output_dir}"
        )

    def _on_gps(self, msg):
        """Update latest GPS position from PX4."""
        self._lat = msg.lat
        self._lon = msg.lon
        self._alt = msg.alt

    def _on_trigger(self, msg):
        """PX4 camera trigger event — capture and geotag."""
        self.get_logger().info(
            f"Trigger #{msg.seq} at ({self._lat:.6f}, {self._lon:.6f}, {self._alt:.1f}m)"
        )
        self._capture_image()

    def _on_timer_capture(self):
        """Fallback timer-based capture for testing."""
        self._capture_image()

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


def main(args=None):
    rclpy.init(args=args)
    node = CameraNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
