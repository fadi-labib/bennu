"""Tests for the YAML-based sensor configuration system."""

import os
import tempfile

import pytest
import yaml

from bennu_camera.sensor_config import SensorConfig

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CONFIGS_DIR = os.path.join(
    os.path.dirname(__file__),
    os.pardir,
    os.pardir,
    "bennu_bringup",
    "config",
    "sensor_configs",
)


def _config_path(name: str) -> str:
    return os.path.normpath(os.path.join(_CONFIGS_DIR, name))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_load_survey_config():
    """survey.yaml must contain rgb + nir sensors and ambient light."""
    cfg = SensorConfig.from_yaml(_config_path("survey.yaml"))

    assert "rgb" in cfg.sensors
    assert "nir" in cfg.sensors
    assert cfg.has_ambient_light is True
    assert cfg.capture_order == ["rgb", "nir"]


def test_load_mapping_config():
    """mapping.yaml must contain rgb only and no ambient light."""
    cfg = SensorConfig.from_yaml(_config_path("mapping.yaml"))

    assert cfg.sensors == ["rgb"]
    assert cfg.has_ambient_light is False
    assert cfg.capture_order == ["rgb"]


def test_unknown_sensor_raises():
    """An unknown sensor name in the YAML must raise ValueError."""
    bad_config = {
        "sensors": ["rgb", "lidar"],
        "ambient_light": False,
        "capture_order": ["rgb", "lidar"],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
        yaml.dump(bad_config, tmp)
        tmp_path = tmp.name

    try:
        with pytest.raises(ValueError, match="Unknown sensor"):
            SensorConfig.from_yaml(tmp_path)
    finally:
        os.unlink(tmp_path)


def test_capture_order_sensor_not_in_active_sensors():
    """capture_order with a sensor not in the active sensors list must raise."""
    bad_config = {
        "sensors": ["rgb"],
        "ambient_light": False,
        "capture_order": ["rgb", "thermal"],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
        yaml.dump(bad_config, tmp)
        tmp_path = tmp.name

    try:
        with pytest.raises(ValueError, match="not in sensors list"):
            SensorConfig.from_yaml(tmp_path)
    finally:
        os.unlink(tmp_path)


def test_empty_sensors_raises():
    """An empty sensors list must raise ValueError."""
    bad_config = {
        "sensors": [],
        "ambient_light": False,
        "capture_order": [],
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
        yaml.dump(bad_config, tmp)
        tmp_path = tmp.name

    try:
        with pytest.raises(ValueError, match="must not be empty"):
            SensorConfig.from_yaml(tmp_path)
    finally:
        os.unlink(tmp_path)


def test_missing_required_key_raises():
    """A YAML missing a required key must raise ValueError."""
    bad_config = {"sensors": ["rgb"]}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
        yaml.dump(bad_config, tmp)
        tmp_path = tmp.name

    try:
        with pytest.raises(ValueError, match="Missing required key"):
            SensorConfig.from_yaml(tmp_path)
    finally:
        os.unlink(tmp_path)


def test_load_inspection_config():
    """inspection.yaml must contain rgb + thermal sensors."""
    cfg = SensorConfig.from_yaml(_config_path("inspection.yaml"))

    assert "rgb" in cfg.sensors
    assert "thermal" in cfg.sensors
