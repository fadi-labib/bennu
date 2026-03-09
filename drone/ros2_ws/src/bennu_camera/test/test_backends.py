"""Tests for camera capture backends."""
import subprocess
from pathlib import Path
from unittest.mock import patch

from bennu_camera.backends.placeholder_backend import PlaceholderBackend
from bennu_camera.backends.libcamera_backend import LibcameraBackend


def test_placeholder_creates_valid_jpeg(tmp_path):
    """PlaceholderBackend creates a file starting with JPEG magic bytes."""
    backend = PlaceholderBackend()
    filepath = tmp_path / "test.jpg"
    result = backend.capture(filepath, 4056, 3040)

    assert result is True
    assert filepath.exists()
    data = filepath.read_bytes()
    assert data[:2] == b'\xff\xd8'  # JPEG SOI marker
    assert data[-2:] == b'\xff\xd9'  # JPEG EOI marker


def test_placeholder_name():
    """PlaceholderBackend identifies itself as 'placeholder'."""
    backend = PlaceholderBackend()
    assert backend.name == "placeholder"


def test_libcamera_returns_false_when_not_found(tmp_path):
    """LibcameraBackend returns False when libcamera-still is not found."""
    backend = LibcameraBackend()
    with patch(
        "bennu_camera.backends.libcamera_backend.subprocess.run",
        side_effect=FileNotFoundError("libcamera-still"),
    ):
        result = backend.capture(tmp_path / "test.jpg", 4056, 3040)
    assert result is False


def test_libcamera_returns_false_on_process_error(tmp_path):
    """LibcameraBackend returns False when libcamera-still exits non-zero."""
    backend = LibcameraBackend()
    with patch(
        "bennu_camera.backends.libcamera_backend.subprocess.run",
        side_effect=subprocess.CalledProcessError(1, "libcamera-still"),
    ):
        result = backend.capture(tmp_path / "test.jpg", 4056, 3040)
    assert result is False


def test_libcamera_returns_false_on_timeout(tmp_path):
    """LibcameraBackend returns False when libcamera-still times out."""
    backend = LibcameraBackend()
    with patch(
        "bennu_camera.backends.libcamera_backend.subprocess.run",
        side_effect=subprocess.TimeoutExpired("libcamera-still", 10),
    ):
        result = backend.capture(tmp_path / "test.jpg", 4056, 3040)
    assert result is False
