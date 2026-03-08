#!/usr/bin/env python3
"""Run all scenario YAML files in a directory.

This is a stub — the full implementation arrives in Phase 2 (Task 9).
"""
import argparse
import glob
import sys


def main():
    parser = argparse.ArgumentParser(description="Run scenario matrix")
    parser.add_argument("--dir", required=True, help="Directory containing scenario YAMLs")
    args = parser.parse_args()

    scenarios = sorted(glob.glob(f"{args.dir}/*.yaml"))
    if not scenarios:
        print(f"[run_scenarios] No scenarios found in {args.dir}")
        sys.exit(1)

    print(f"[run_scenarios] Found {len(scenarios)} scenario(s):")
    for s in scenarios:
        print(f"  - {s}")

    print("[run_scenarios] STUB — scenario execution not yet implemented (Phase 2)")
    sys.exit(0)


if __name__ == "__main__":
    main()
