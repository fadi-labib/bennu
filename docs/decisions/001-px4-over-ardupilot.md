# ADR-001: PX4 over ArduPilot

## Status

Accepted

## Context

Choosing a flight controller firmware for a photogrammetry drone that needs
tight ROS2 integration for autonomous waypoint missions and camera triggering.
Both PX4 and ArduPilot are mature open-source autopilots with large communities.

The drone needs:
- Native ROS2 communication (topics for position, camera triggers)
- Waypoint mission execution with camera trigger support
- Reliable failsafes (RC loss, battery, geofence)
- Active development and long-term support

## Decision

Use **PX4 v1.16+** as the flight controller firmware on a Holybro Pixhawk 6C.

## Consequences

**Positive:**

- **Native ROS2 support** via uXRCE-DDS — PX4 has a built-in DDS client that
  publishes topics directly to ROS2. No bridge layer needed.
- **Production-grade path** — PX4 is used by commercial drone companies (Auterion,
  Dronecode), providing a realistic development experience.
- **Camera trigger module** — Built-in distance-based triggering via TRIG_MODE/TRIG_DIST
  parameters, sends events to companion via MAVLink.
- **Pixhawk 6C is a PX4 reference board** — first-class support guaranteed.

**Negative:**

- **Smaller hobby community** than ArduPilot — fewer forum posts for DIY quad tuning.
- **ArduPilot tuning guides don't apply** — PX4 has its own parameter ecosystem.
- **ArduPilot's MAVROS** is more documented for ROS integration, but MAVROS is a
  translation layer (MAVLink→ROS) while uXRCE-DDS is native.

**Neutral:**

- Both support the same hardware (Pixhawk ecosystem).
- Both have waypoint mission support via QGroundControl/Mission Planner.
