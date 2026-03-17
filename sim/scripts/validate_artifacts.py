#!/usr/bin/env python3
"""Validate mission artifacts against scenario assertions.

Loads a scenario YAML, counts images in the output directory,
verifies the count meets min_triggers, and checks that every
image is a valid JPEG (starts with FF D8 magic bytes).
"""
import argparse
import sys
from pathlib import Path

import yaml

JPEG_MAGIC = b"\xff\xd8"


def validate(scenario_path: str, output_dir: str) -> bool:
    """Validate artifacts in *output_dir* against *scenario_path* assertions.

    Returns True if all assertions pass, False otherwise.
    """
    scenario = yaml.safe_load(Path(scenario_path).read_text())
    assertions = scenario.get("assertions", {})
    min_triggers = assertions.get("min_triggers", 0)

    out = Path(output_dir)
    if not out.is_dir():
        print(f"FAIL: output directory does not exist: {out}")
        return False

    images = sorted(out.glob("*.jpg"))
    count = len(images)
    passed = True

    # --- Check image count ---
    if count >= min_triggers:
        print(f"PASS: image count {count} >= min_triggers {min_triggers}")
    else:
        print(f"FAIL: image count {count} < min_triggers {min_triggers}")
        passed = False

    # --- Check JPEG magic bytes ---
    for img in images:
        header = img.read_bytes()[:2]
        if header != JPEG_MAGIC:
            print(f"FAIL: {img.name} is not a valid JPEG (header: {header.hex()})")
            passed = False

    if passed:
        print("All artifact checks passed.")
    else:
        print("Some artifact checks failed.")

    return passed


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate SIL mission artifacts")
    parser.add_argument(
        "--scenario",
        required=True,
        help="Path to scenario YAML file",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Path to output directory containing captured images",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = _parse_args()
    ok = validate(args.scenario, args.output_dir)
    sys.exit(0 if ok else 1)
