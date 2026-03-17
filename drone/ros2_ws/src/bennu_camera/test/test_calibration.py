"""Tests for ambient-light calibration capture."""

import csv
import io
import os
import tempfile

import pytest

from bennu_camera.calibration import CalibrationCapture
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


def test_calibration_csv_generated_with_ambient_light():
    """When has_ambient_light is True, calibration.csv must be written."""
    cfg = SensorConfig.from_yaml(_config_path("survey.yaml"))
    assert cfg.has_ambient_light is True

    cal = CalibrationCapture(cfg)
    cal.record(lux=1200.5, timestamp_utc="2026-03-17T10:00:00+00:00")
    cal.record(lux=1150.0, timestamp_utc="2026-03-17T10:00:05+00:00")

    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "calibration.csv")
        written = cal.write_csv(csv_path)

        assert written is True
        assert os.path.exists(csv_path)

        with open(csv_path) as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)

        assert len(rows) == 2
        assert rows[0]["timestamp_utc"] == "2026-03-17T10:00:00+00:00"
        assert float(rows[0]["lux"]) == pytest.approx(1200.5)
        assert rows[1]["timestamp_utc"] == "2026-03-17T10:00:05+00:00"
        assert float(rows[1]["lux"]) == pytest.approx(1150.0)


def test_calibration_csv_not_generated_without_ambient_light():
    """When has_ambient_light is False, no CSV must be written."""
    cfg = SensorConfig.from_yaml(_config_path("mapping.yaml"))
    assert cfg.has_ambient_light is False

    cal = CalibrationCapture(cfg)

    # record should raise because calibration is disabled
    with pytest.raises(RuntimeError):
        cal.record(lux=500.0)

    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "calibration.csv")
        written = cal.write_csv(csv_path)

        assert written is False
        assert not os.path.exists(csv_path)

    # to_csv should return empty string
    assert cal.to_csv() == ""
