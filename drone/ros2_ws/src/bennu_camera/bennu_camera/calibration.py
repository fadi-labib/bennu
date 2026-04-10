"""Ambient-light calibration data capture and CSV writer."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from bennu_camera.sensor_config import SensorConfig


@dataclass
class LuxReading:
    """A single ambient-light reading from the BH1750 sensor."""

    timestamp_utc: str
    lux: float


class CalibrationCapture:
    """Captures and persists ambient-light calibration readings.

    Calibration data is only generated when the active sensor
    configuration includes an ambient-light sensor
    (``SensorConfig.has_ambient_light is True``).
    """

    CSV_HEADER = ["timestamp_utc", "lux"]

    def __init__(self, config: SensorConfig) -> None:
        self._config = config
        self._readings: list[LuxReading] = []

    @property
    def enabled(self) -> bool:
        """Whether calibration capture is active for this config."""
        return self._config.has_ambient_light

    def record(self, lux: float, timestamp_utc: str | None = None) -> None:
        """Record a single lux reading.

        Parameters:
            lux: Ambient-light value in lux.
            timestamp_utc: ISO-8601 timestamp.  If *None*, the current
                UTC time is used.

        Raises:
            RuntimeError: If calibration is not enabled for this config.
        """
        if not self.enabled:
            raise RuntimeError(
                "Calibration capture is disabled — sensor config has no ambient light"
            )
        if timestamp_utc is None:
            timestamp_utc = datetime.now(UTC).isoformat()
        self._readings.append(LuxReading(timestamp_utc=timestamp_utc, lux=lux))

    def to_csv(self) -> str:
        """Return calibration readings as a CSV string (with header).

        Returns an empty string if calibration is not enabled.
        """
        if not self.enabled:
            return ""

        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=self.CSV_HEADER)
        writer.writeheader()
        for reading in self._readings:
            writer.writerow(
                {"timestamp_utc": reading.timestamp_utc, "lux": reading.lux}
            )
        return buf.getvalue()

    def write_csv(self, path: str | Path) -> bool:
        """Write calibration.csv to *path*.

        Returns True if the file was written, False if calibration is
        disabled (no file created).
        """
        if not self.enabled:
            return False

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_csv())
        return True
