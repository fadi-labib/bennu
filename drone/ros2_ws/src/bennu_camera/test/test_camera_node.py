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
        raise ValueError(f"Unknown camera backend: {name}")
    return BACKENDS[name]()


def test_backend_factory_placeholder():
    """'placeholder' key maps to PlaceholderBackend."""
    backend = _create_backend("placeholder")
    assert isinstance(backend, PlaceholderBackend)
    assert backend.name == "placeholder"


def test_backend_factory_invalid():
    """Unknown backend name raises ValueError."""
    with pytest.raises(ValueError, match="Unknown camera backend"):
        _create_backend("nonexistent")
