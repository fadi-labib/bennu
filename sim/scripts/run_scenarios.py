#!/usr/bin/env python3
"""Run all scenario YAML files in a directory and report results.

Discovers scenario YAMLs, runs each via run_mission.py, and optionally
validates artifacts. Produces a summary table at the end.
"""

import argparse
import asyncio
import glob
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class ScenarioResult:
    """Result of a single scenario run."""

    name: str
    path: str
    passed: bool
    duration_s: float
    error: str | None = None


def discover_scenarios(directory: str) -> list[str]:
    """Find all .yaml scenario files in a directory, sorted by name.

    Returns list of file paths. Raises FileNotFoundError if directory
    does not exist. Returns empty list if no YAML files found.
    """
    d = Path(directory)
    if not d.is_dir():
        raise FileNotFoundError(f"Scenario directory does not exist: {directory}")
    return sorted(glob.glob(f"{directory}/*.yaml"))


def load_scenario_name(path: str) -> str:
    """Load and return the scenario name from a YAML file."""
    data = yaml.safe_load(Path(path).read_text())
    return data.get("name", Path(path).stem)


async def run_single_scenario(
    scenario_path: str, address: str, timeout: int, runner=None
) -> ScenarioResult:
    """Run a single scenario and return the result.

    Args:
        runner: Optional async callable(scenario_path, address, timeout) -> bool.
                Defaults to run_mission.run_mission (imported at call time).
    """
    if runner is None:
        from run_mission import run_mission

        runner = run_mission

    name = load_scenario_name(scenario_path)
    start = time.monotonic()

    try:
        ok = await runner(
            scenario_path=scenario_path,
            address=address,
            timeout=timeout,
        )
        duration = time.monotonic() - start
        return ScenarioResult(name=name, path=scenario_path, passed=ok, duration_s=duration)
    except Exception as e:
        duration = time.monotonic() - start
        return ScenarioResult(
            name=name,
            path=scenario_path,
            passed=False,
            duration_s=duration,
            error=str(e),
        )


def print_summary(results: list[ScenarioResult]) -> None:
    """Print a summary table of scenario results."""
    print("\n" + "=" * 60)
    print("SCENARIO RESULTS")
    print("=" * 60)

    for r in results:
        status = "PASS" if r.passed else "FAIL"
        line = f"  [{status}] {r.name} ({r.duration_s:.1f}s)"
        if r.error:
            line += f" — {r.error}"
        print(line)

    passed = sum(1 for r in results if r.passed)
    total = len(results)
    print("-" * 60)
    print(f"  {passed}/{total} scenarios passed")
    print("=" * 60)


async def run_all_scenarios(
    directory: str, address: str, timeout: int, runner=None
) -> list[ScenarioResult]:
    """Discover and run all scenarios sequentially. Returns list of results."""
    scenarios = discover_scenarios(directory)
    if not scenarios:
        print(f"[run_scenarios] No scenarios found in {directory}")
        return []

    print(f"[run_scenarios] Found {len(scenarios)} scenario(s):")
    for s in scenarios:
        print(f"  - {s}")

    results = []
    for scenario_path in scenarios:
        print(f"\n{'─' * 60}")
        print(f"[run_scenarios] Running: {scenario_path}")
        print(f"{'─' * 60}")
        result = await run_single_scenario(scenario_path, address, timeout, runner=runner)
        results.append(result)

    print_summary(results)
    return results


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run scenario matrix")
    parser.add_argument("--dir", required=True, help="Directory containing scenario YAMLs")
    parser.add_argument(
        "--address",
        default="udp://:14540",
        help="MAVSDK connection address (default: udp://:14540)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="PX4 readiness timeout per scenario (default: 120s)",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = _parse_args()
    results = asyncio.run(
        run_all_scenarios(directory=args.dir, address=args.address, timeout=args.timeout)
    )
    all_passed = all(r.passed for r in results) if results else False
    sys.exit(0 if all_passed else 1)
