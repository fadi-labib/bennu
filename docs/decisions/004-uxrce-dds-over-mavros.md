# ADR-004: uXRCE-DDS over MAVROS

## Status

Accepted

## Context

Need a communication bridge between PX4 (flight controller) and ROS2
(companion computer) for real-time access to position data, camera triggers,
and future autonomous commands.

Two established options:

- **MAVROS** — Community-maintained ROS package that translates MAVLink
  messages to/from ROS topics. Mature, well-documented, widely used.
- **uXRCE-DDS** — PX4's native DDS client that publishes PX4 topics
  directly to the ROS2 DDS network. Built into PX4 since v1.14.

## Decision

Use **uXRCE-DDS** (Micro XRCE-DDS) as the PX4-ROS2 communication bridge.

## Consequences

**Positive:**

- **Native integration** — PX4 publishes DDS topics directly. No translation
  layer, no message conversion, no bridge node to maintain.
- **Lower latency** — Direct DDS pub/sub vs MAVLink encode/decode/re-publish.
- **PX4-maintained** — Part of the PX4 codebase, guaranteed to stay in sync
  with firmware updates.
- **Simpler stack** — Just run `MicroXRCEAgent` on Pi 5, PX4 handles the rest.
  No need to install/configure MAVROS.
- **Same topics in sim and hardware** — Only transport changes (UDP vs UART),
  topic names and types are identical.

**Negative:**

- **Less community documentation** than MAVROS — fewer tutorials and Stack
  Overflow answers available.
- **Requires PX4 v1.14+** — not available on older firmware.
- **TELEM2 configuration required** — must set specific baud rate (921600)
  and MAV_1_CONFIG parameters.

**Neutral:**

- MAVROS is still useful for ArduPilot integration but is not needed for PX4+ROS2.
- The Micro XRCE-DDS Agent is lightweight (~5MB) and easy to build from source.
