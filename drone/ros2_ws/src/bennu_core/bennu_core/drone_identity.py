"""Drone identity and hardware manifest for mission bundles."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DroneIdentity:
    """Represents the identity and hardware configuration of a Bennu drone.

    Used to populate the `drone_hardware` section of manifest.json.
    """

    drone_id: str
    flight_controller: str
    px4_version: str
    gps_model: str
    sensors: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self):
        if not self.drone_id:
            raise ValueError("drone_id must not be empty")
        if not self.flight_controller:
            raise ValueError("flight_controller must not be empty")
        if not self.px4_version:
            raise ValueError("px4_version must not be empty")
        if not self.gps_model:
            raise ValueError("gps_model must not be empty")
        if not self.sensors:
            raise ValueError("sensors must not be empty")

    def hardware_manifest(self) -> dict:
        """Return dict matching manifest.json drone_hardware schema."""
        return {
            "flight_controller": self.flight_controller,
            "px4_version": self.px4_version,
            "gps_model": self.gps_model,
            "sensors": list(self.sensors),
        }
