# Simulation Stack

PX4 SITL + Gazebo Harmonic + ROS2 Jazzy in Docker.

## Quick Start

```bash
make sim          # One command: containers + QGC + auto-fly + shell
make dev          # Headless containers only (no GUI)
make qgc          # Launch QGroundControl
make test         # Unit tests (no PX4)
make test-smoke   # Full mission SIL
make clean        # Stop everything
make help         # All targets
```

## Documentation

Full guide: [Run the Gazebo SITL Simulation](../docs/how-to/run-simulation.md)
