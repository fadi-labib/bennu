from bennu_core.drone_identity import DroneIdentity


def test_drone_identity_loads_config():
    """Fields stored correctly."""
    identity = DroneIdentity(
        drone_id="bennu-001",
        flight_controller="Pixhawk6C",
        px4_version="1.16.1",
        gps_model="M9N",
        sensors=["rgb:IMX477"],
    )
    assert identity.drone_id == "bennu-001"
    assert identity.flight_controller == "Pixhawk6C"
    assert identity.sensors == ["rgb:IMX477"]


def test_hardware_manifest_structure():
    """Output dict has all required keys matching manifest schema."""
    identity = DroneIdentity(
        drone_id="bennu-001",
        flight_controller="Pixhawk6C",
        px4_version="1.16.1",
        gps_model="F9P",
        sensors=["rgb:IMX477", "nir:IMX708_NoIR"],
    )
    hw = identity.hardware_manifest()
    assert hw == {
        "flight_controller": "Pixhawk6C",
        "px4_version": "1.16.1",
        "gps_model": "F9P",
        "sensors": ["rgb:IMX477", "nir:IMX708_NoIR"],
    }
