"""Drone identity and hardware manifest for mission bundles."""
from dataclasses import dataclass, field
from typing import List


@dataclass
class DroneIdentity:
    """Represents the identity and hardware configuration of a Bennu drone.

    Used to populate the `drone_hardware` section of manifest.json.
    """
    drone_id: str
    flight_controller: str
    px4_version: str
    gps_model: str
    sensors: List[str] = field(default_factory=list)

    def hardware_manifest(self) -> dict:
        """Return dict matching manifest.json drone_hardware schema."""
        return {
            "flight_controller": self.flight_controller,
            "px4_version": self.px4_version,
            "gps_model": self.gps_model,
            "sensors": list(self.sensors),
        }
