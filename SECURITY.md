# Security Policy

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Instead, email **github@fadilabib.com** with:

- A description of the vulnerability
- Steps to reproduce or a proof of concept
- The affected component(s) and version(s)

## Response Timeline

- **Acknowledgment:** Within 72 hours of your report.
- **Assessment:** We will evaluate severity and affected components within one week.
- **Fix:** Patches will be developed and released as quickly as possible, depending on complexity.

## Scope

This policy covers:

- **Drone firmware** — PX4 parameter files, flash scripts
- **Companion computer software** — ROS2 nodes, camera capture, geotagging
- **Ground station tools** — image transfer scripts, WebODM configuration
- **Simulation stack** — Docker images, SITL configuration

## Out of Scope

- Vulnerabilities in upstream dependencies (PX4, ROS2, Gazebo, OpenDroneMap) — please report those to their respective projects.
- Physical security of the drone hardware.

## Bug Bounty

Bennu is a hobby/open-source project. There is no bug bounty program. We appreciate responsible disclosure and will credit reporters in release notes (with permission).

## Supported Versions

Only the latest release on the `main` branch is actively supported with security fixes.
