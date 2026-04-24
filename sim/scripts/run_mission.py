#!/usr/bin/env python3
"""Run a single MAVSDK mission from a scenario YAML file.

Loads a scenario YAML, waits for PX4 readiness, generates a small grid
of waypoints around the home position, uploads the mission via MAVSDK,
arms, flies, and monitors until landing. Exits 0 on success, 1 on failure.
"""
import argparse
import asyncio
import math
import sys
from pathlib import Path

import yaml
from mavsdk import System
from mavsdk.mission import MissionItem, MissionPlan
from wait_for_px4 import wait_for_px4


def load_scenario(path: str) -> dict:
    """Load and return a scenario YAML file."""
    return yaml.safe_load(Path(path).read_text())


def generate_grid_waypoints(
    home_lat: float,
    home_lon: float,
    altitude_m: float,
    speed_mps: float,
    num_waypoints: int,
    trigger_distance_m: float,
) -> list:
    """Generate a small grid of MissionItems around the home position.

    Creates a simple lawnmower pattern: alternating north-south legs
    offset east, all at the specified altitude. The first waypoint
    enables distance-based camera triggering.
    """
    NAN = float("nan")
    items = []

    # Approximate meters-to-degrees conversion at the home latitude
    m_per_deg_lat = 111_320.0
    m_per_deg_lon = 111_320.0 * math.cos(math.radians(home_lat))

    # Grid spacing: 30m between legs, 50m leg length
    leg_length_m = 50.0
    leg_spacing_m = 30.0

    for i in range(num_waypoints):
        leg = i // 2          # which east-west column
        direction = i % 2     # 0 = north, 1 = south

        east_offset_m = leg * leg_spacing_m
        north_offset_m = leg_length_m if direction == 0 else 0.0

        lat = home_lat + (north_offset_m / m_per_deg_lat)
        lon = home_lon + (east_offset_m / m_per_deg_lon)

        # First waypoint: start distance-based camera triggering
        if i == 0:
            camera_action = MissionItem.CameraAction.START_PHOTO_DISTANCE
            photo_distance = trigger_distance_m
        else:
            camera_action = MissionItem.CameraAction.NONE
            photo_distance = NAN

        items.append(MissionItem(
            lat,
            lon,
            altitude_m,
            speed_mps,
            True,           # is_fly_through
            NAN,            # gimbal_pitch_deg
            NAN,            # gimbal_yaw_deg
            camera_action,
            NAN,            # loiter_time_s
            NAN,            # camera_photo_interval_s
            NAN,            # acceptance_radius_m
            NAN,            # yaw_deg
            photo_distance, # camera_photo_distance_m
            MissionItem.VehicleAction.NONE,
        ))

    return items


async def _connect_with_backoff(address: str, max_retries: int = 5) -> System:
    """Connect to PX4 with exponential backoff. Returns connected System."""
    drone = System()
    for attempt in range(max_retries):
        delay = min(2 ** attempt, 30)
        try:
            await drone.connect(system_address=address)
            async for state in drone.core.connection_state():
                if state.is_connected:
                    print(f"[run_mission] Connected on attempt {attempt + 1}")
                    return drone
        except Exception as e:
            print(f"[run_mission] Connection attempt {attempt + 1} failed: {e}")
        if attempt < max_retries - 1:
            print(f"[run_mission] Retrying in {delay}s...")
            await asyncio.sleep(delay)
    raise ConnectionError(f"Failed to connect after {max_retries} attempts")


async def run_mission(scenario_path: str, address: str, timeout: int) -> bool:
    """Execute a full mission from scenario YAML. Returns True on success."""
    scenario = load_scenario(scenario_path)
    mission_cfg = scenario["mission"]
    assertions = scenario.get("assertions", {})
    max_duration = assertions.get("max_duration_s", 300)

    print(f"[run_mission] Scenario: {scenario['name']}")
    print(f"[run_mission] Mission: {mission_cfg}")

    # 1. Connect with backoff and wait for PX4 readiness
    drone = await _connect_with_backoff(address)

    print("[run_mission] Waiting for PX4 readiness (GPS fix + home position)...")
    await asyncio.wait_for(wait_for_px4(address=address), timeout=timeout)

    # 2. Get home position for waypoint generation
    print("[run_mission] Getting home position...")
    home_lat = None
    home_lon = None
    async for position in drone.telemetry.position():
        home_lat = position.latitude_deg
        home_lon = position.longitude_deg
        print(f"[run_mission] Home: ({home_lat:.6f}, {home_lon:.6f})")
        break

    # 3. Generate waypoints
    items = generate_grid_waypoints(
        home_lat=home_lat,
        home_lon=home_lon,
        altitude_m=mission_cfg["altitude_m"],
        speed_mps=mission_cfg["speed_mps"],
        num_waypoints=mission_cfg["waypoints"],
        trigger_distance_m=mission_cfg.get("trigger_distance_m", 10),
    )
    print(f"[run_mission] Generated {len(items)} waypoints")

    # 4. Upload mission
    mission_plan = MissionPlan(items)
    await drone.mission.set_return_to_launch_after_mission(True)

    print("[run_mission] Uploading mission...")
    await drone.mission.upload_mission(mission_plan)
    print("[run_mission] Mission uploaded")

    # 5. Arm and start
    print("[run_mission] Arming...")
    await drone.action.arm()

    print("[run_mission] Starting mission...")
    await drone.mission.start_mission()

    # 6. Monitor progress with timeout
    print("[run_mission] Flying mission...")
    mission_complete = False

    async def monitor_progress():
        nonlocal mission_complete
        async for progress in drone.mission.mission_progress():
            print(f"[run_mission] Progress: {progress.current}/{progress.total}")
            if progress.current == progress.total:
                mission_complete = True
                return

    try:
        await asyncio.wait_for(monitor_progress(), timeout=max_duration)
    except TimeoutError:
        print(f"[run_mission] TIMEOUT: mission did not complete in {max_duration}s",
              file=sys.stderr)
        return False

    # 7. Wait for landing
    if mission_complete:
        print("[run_mission] Mission items complete, waiting for landing...")
        try:
            async def wait_for_landed():
                async for in_air in drone.telemetry.in_air():
                    if not in_air:
                        return

            await asyncio.wait_for(wait_for_landed(), timeout=60)
            print("[run_mission] Landed successfully")
        except TimeoutError:
            print("[run_mission] WARNING: landing timeout, but mission items completed")

    print("[run_mission] Mission finished successfully")
    return True


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a MAVSDK mission scenario")
    parser.add_argument(
        "--scenario", required=True, help="Path to scenario YAML"
    )
    parser.add_argument(
        "--address",
        default="udp://:14540",
        help="MAVSDK connection address (default: udp://:14540)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=180,
        help="PX4 readiness timeout in seconds (default: 180)",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = _parse_args()
    try:
        ok = asyncio.run(run_mission(
            scenario_path=args.scenario,
            address=args.address,
            timeout=args.timeout,
        ))
        sys.exit(0 if ok else 1)
    except TimeoutError:
        print("[run_mission] TIMEOUT: PX4 not ready", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[run_mission] ERROR: {e}", file=sys.stderr)
        sys.exit(1)
