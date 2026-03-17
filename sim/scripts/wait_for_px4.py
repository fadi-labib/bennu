#!/usr/bin/env python3
"""Wait for PX4 SITL to be ready for mission upload."""
import argparse
import asyncio
import sys

from mavsdk import System


async def wait_for_px4(address: str = "udp://:14540") -> bool:
    """Poll PX4 via MAVSDK until GPS fix and home position are set.

    Returns True when PX4 is ready. This coroutine runs indefinitely
    until PX4 reports ready — use asyncio.wait_for() to enforce a timeout.
    """
    drone = System()
    await drone.connect(system_address=address)

    print(f"Waiting for PX4 at {address}...")

    # Wait for connection
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("PX4 connected.")
            break

    # Wait for GPS fix + home position
    print("Waiting for GPS fix...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("PX4 ready: GPS fix OK, home position set.")
            return True

    return False


async def _main(address: str, timeout: int) -> bool:
    """Run wait_for_px4 with a timeout wrapper."""
    return await asyncio.wait_for(
        wait_for_px4(address=address),
        timeout=timeout,
    )


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Wait for PX4 SITL readiness")
    parser.add_argument(
        "--address",
        default="udp://:14540",
        help="MAVSDK connection address (default: udp://:14540)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Timeout in seconds (default: 120)",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = _parse_args()
    try:
        result = asyncio.run(_main(address=args.address, timeout=args.timeout))
        sys.exit(0 if result else 1)
    except asyncio.TimeoutError:
        print(f"Timeout: PX4 not ready after {args.timeout}s", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
