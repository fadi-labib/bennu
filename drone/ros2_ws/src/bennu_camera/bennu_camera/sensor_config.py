"""YAML-based sensor configuration for multi-sensor flight profiles."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

import yaml

# Known sensor types supported by the platform.
KNOWN_SENSORS = {"rgb", "nir", "thermal"}


@dataclass(frozen=True)
class SensorConfig:
    """Immutable sensor configuration loaded from a YAML file.

    Attributes:
        sensors: List of active sensor names (e.g. ["rgb", "nir"]).
        has_ambient_light: Whether a BH1750 ambient-light sensor is present.
        capture_order: Ordered list of sensors for synchronised capture timing.
    """

    sensors: List[str]
    has_ambient_light: bool
    capture_order: List[str]

    @classmethod
    def from_yaml(cls, path: str | Path) -> "SensorConfig":
        """Load a sensor configuration from a YAML file.

        Raises:
            FileNotFoundError: If *path* does not exist.
            ValueError: If any sensor name is not in KNOWN_SENSORS, if
                the sensors list is empty, or if required keys are missing.
        """
        path = Path(path)
        with open(path) as fh:
            data = yaml.safe_load(fh)

        if not isinstance(data, dict):
            raise ValueError(f"Expected a YAML mapping, got {type(data).__name__}")

        for key in ("sensors", "ambient_light", "capture_order"):
            if key not in data:
                raise ValueError(f"Missing required key: {key!r}")

        sensors = data["sensors"]
        if not sensors:
            raise ValueError("sensors list must not be empty")

        unknown = set(sensors) - KNOWN_SENSORS
        if unknown:
            raise ValueError(
                f"Unknown sensor(s): {sorted(unknown)}. "
                f"Valid sensors: {sorted(KNOWN_SENSORS)}"
            )

        capture_order = data["capture_order"]
        invalid_order = set(capture_order) - set(sensors)
        if invalid_order:
            raise ValueError(
                f"capture_order contains sensors not in sensors list: {sorted(invalid_order)}. "
                f"Active sensors: {sorted(sensors)}"
            )

        return cls(
            sensors=list(sensors),
            has_ambient_light=bool(data["ambient_light"]),
            capture_order=list(capture_order),
        )
