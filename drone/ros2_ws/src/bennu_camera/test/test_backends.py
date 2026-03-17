"""Tests for camera capture backends."""
import subprocess
from unittest.mock import patch

from bennu_camera.backends import create_backend
from bennu_camera.backends.libcamera_backend import LibcameraBackend
from bennu_camera.backends.placeholder_backend import PlaceholderBackend


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


def test_placeholder_ignores_dimensions(tmp_path):
    """PlaceholderBackend produces identical output regardless of requested dimensions.

    This is by design — simulation doesn't need real-resolution images.
    Changing this behavior would break sim performance assumptions.
    """
    backend = PlaceholderBackend()
    small = tmp_path / "small.jpg"
    large = tmp_path / "large.jpg"
    backend.capture(small, 640, 480)
    backend.capture(large, 4056, 3040)

    assert small.read_bytes() == large.read_bytes()


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


def test_placeholder_creates_nested_directories(tmp_path):
    """PlaceholderBackend creates intermediate directories when they don't exist."""
    backend = PlaceholderBackend()
    filepath = tmp_path / "a" / "b" / "c" / "test.jpg"
    result = backend.capture(filepath, 4056, 3040)
    assert result is True
    assert filepath.exists()


def test_libcamera_is_available_checks_binary():
    """LibcameraBackend.is_available() checks for libcamera-still on PATH."""
    backend = LibcameraBackend()
    with patch(
        "bennu_camera.backends.libcamera_backend.shutil.which",
        return_value=None,
    ):
        assert backend.is_available() is False

    with patch(
        "bennu_camera.backends.libcamera_backend.shutil.which",
        return_value="/usr/bin/libcamera-still",
    ):
        assert backend.is_available() is True


def test_placeholder_is_always_available():
    """PlaceholderBackend is always available (no external deps)."""
    backend = PlaceholderBackend()
    assert backend.is_available() is True


def test_create_backend_factory():
    """create_backend() returns correct backend instances."""
    assert isinstance(create_backend("placeholder"), PlaceholderBackend)
    assert isinstance(create_backend("libcamera"), LibcameraBackend)
