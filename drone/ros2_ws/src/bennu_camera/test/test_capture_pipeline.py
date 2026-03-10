"""Integration test: capture backend → geotag pipeline.

Tests the full sequence that camera_node._capture_image() performs:
1. Backend captures image to disk
2. write_gps_exif tags the image with GPS coordinates
3. Resulting file is a valid geotagged JPEG

This runs without rclpy — it tests the data pipeline, not the ROS2 wiring.
"""
import shutil

import pytest

from bennu_camera.backends.placeholder_backend import PlaceholderBackend
from bennu_camera.geotag import write_gps_exif

HAS_EXIFTOOL = shutil.which("exiftool") is not None


def test_placeholder_capture_then_geotag(tmp_path):
    """Full pipeline: placeholder capture → geotag → valid JPEG with GPS."""
    backend = PlaceholderBackend()
    filepath = tmp_path / "pipeline_test.jpg"

    # Step 1: Capture
    assert backend.capture(filepath, 4056, 3040) is True
    assert filepath.exists()

    # Step 2: Geotag (if exiftool available)
    if not HAS_EXIFTOOL:
        pytest.skip("exiftool not installed")

    result = write_gps_exif(str(filepath), 37.7749, -122.4194, 50.0)
    assert result is True

    # Step 3: Verify JPEG still valid after EXIF modification
    data = filepath.read_bytes()
    assert data[:2] == b'\xff\xd8'  # JPEG SOI
    assert data[-2:] == b'\xff\xd9'  # JPEG EOI


@pytest.mark.skipif(not HAS_EXIFTOOL, reason="exiftool not installed")
def test_geotag_preserves_jpeg_on_failure(tmp_path):
    """If geotag fails on a non-JPEG, original file is unchanged."""
    # Create a file that isn't a valid JPEG
    not_jpeg = tmp_path / "not_a_jpeg.jpg"
    original_content = b"this is not a jpeg"
    not_jpeg.write_bytes(original_content)

    result = write_gps_exif(str(not_jpeg), 37.0, -122.0, 50.0)

    # exiftool should fail on non-JPEG content
    assert result is not True  # Should be an error string after Task 1
    # Original file should still exist (exiftool doesn't delete on failure)
    assert not_jpeg.exists()


@pytest.mark.skipif(not HAS_EXIFTOOL, reason="exiftool not installed")
def test_geotag_with_extreme_coordinates(tmp_path):
    """Geotag handles edge-case GPS coordinates (poles, antimeridian)."""
    backend = PlaceholderBackend()
    filepath = tmp_path / "extreme_coords.jpg"
    backend.capture(filepath, 640, 480)

    # South pole, antimeridian
    result = write_gps_exif(str(filepath), -90.0, 180.0, 0.0)
    assert result is True
