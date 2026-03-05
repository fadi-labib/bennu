"""Tests for CameraNode backend factory logic."""
import pytest

from bennu_camera.backends import PlaceholderBackend, LibcameraBackend


BACKENDS = {
    "libcamera": LibcameraBackend,
    "placeholder": PlaceholderBackend,
}


def _create_backend(name: str):
    """Replicate camera_node.py factory logic (avoids rclpy dependency)."""
    if name not in BACKENDS:
        valid = ", ".join(sorted(BACKENDS.keys()))
        raise ValueError(
            f"Unknown camera backend: {name} (valid: {valid})"
        )
    return BACKENDS[name]()


def test_backend_factory_placeholder():
    """'placeholder' key maps to PlaceholderBackend."""
    backend = _create_backend("placeholder")
    assert isinstance(backend, PlaceholderBackend)
    assert backend.name == "placeholder"


def test_backend_factory_libcamera():
    """'libcamera' key maps to LibcameraBackend (production default)."""
    backend = _create_backend("libcamera")
    assert isinstance(backend, LibcameraBackend)
    assert backend.name == "libcamera"


def test_backend_factory_invalid():
    """Unknown backend name raises ValueError listing valid options."""
    with pytest.raises(ValueError, match="Unknown camera backend: nonexistent") as exc_info:
        _create_backend("nonexistent")
    error_msg = str(exc_info.value)
    assert "libcamera" in error_msg
    assert "placeholder" in error_msg
