"""Tests for CameraNode backend factory logic."""
import pytest

from bennu_camera.backends import LibcameraBackend, PlaceholderBackend

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


def test_timer_interval_is_declared_parameter():
    """Timer interval (5.0s) should be a declared ROS parameter, not hardcoded."""
    import ast
    from pathlib import Path

    camera_node_src = Path(__file__).parent.parent / "bennu_camera" / "camera_node.py"
    tree = ast.parse(camera_node_src.read_text())

    # Find declare_parameter calls to verify timer_interval exists
    param_names = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "declare_parameter"
            and len(node.args) >= 1
            and isinstance(node.args[0], ast.Constant)
        ):
            param_names.append(node.args[0].value)

    assert "timer_interval" in param_names, (
        f"Expected 'timer_interval' in declared parameters, found: {param_names}"
    )
