"""
Bennu Camera Node — captures geotagged images triggered by PX4.

Subscribes to PX4 camera trigger events via uXRCE-DDS,
captures images using configurable backends, and writes GPS EXIF data.
"""
import os
from datetime import UTC, datetime
from pathlib import Path

import rclpy
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy

from bennu_camera.backends import create_backend
from bennu_camera.geotag import write_gps_exif


class CameraNode(Node):
    """ROS2 node that captures geotagged images on PX4 camera trigger."""

    def __init__(self):
        super().__init__("camera_capture_node")

        # Parameters
        self.declare_parameter("output_dir", "/home/pi/captures")
        self.declare_parameter("image_width", 4056)
        self.declare_parameter("image_height", 3040)
        self.declare_parameter("camera_backend", "libcamera")
        self.declare_parameter("timer_interval", 5.0)

        self.output_dir = self.get_parameter("output_dir").value
        self.width = self.get_parameter("image_width").value
        self.height = self.get_parameter("image_height").value

        backend_name = self.get_parameter("camera_backend").value
        self._backend = create_backend(backend_name)
        self.get_logger().info(f"Camera backend: {self._backend.name}")
        if not self._backend.is_available():
            self.get_logger().warning(
                f"Backend '{self._backend.name}' is not available in this environment"
            )

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
            from px4_msgs.msg import CameraTrigger, VehicleGlobalPosition

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
            # Fallback: capture on timer — used in sim mode and when running without PX4
            interval = self.get_parameter("timer_interval").value
            if interval <= 0.0:
                raise ValueError(
                    f"timer_interval must be > 0, got {interval}"
                )
            self.create_timer(interval, self._on_timer_capture)

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
        """Capture image using the configured backend."""
        self._capture_count += 1
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        filename = f"bennu_{timestamp}_{self._capture_count:04d}.jpg"
        filepath = os.path.join(self.output_dir, filename)

        success = self._backend.capture(Path(filepath), self.width, self.height)
        if not success:
            self.get_logger().error(
                f"Capture #{self._capture_count} failed via {self._backend.name} "
                f"(target: {filepath}, {self.width}x{self.height})"
            )
            return

        # Write GPS EXIF
        if self._lat != 0.0 or self._lon != 0.0:
            result = write_gps_exif(filepath, self._lat, self._lon, self._alt)
            if result is True:
                self.get_logger().info(f"Saved: {filename} (geotagged)")
            else:
                self.get_logger().error(f"Saved: {filename} (UNGEOTAGGED — geotag failed: {result})")
        else:
            self.get_logger().warn(f"Saved: {filename} (no GPS fix)")


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
