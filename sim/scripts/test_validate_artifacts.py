"""Tests for artifact validation script (not yet implemented — see Phase 2)."""
from pathlib import Path

import pytest

validate_artifacts = pytest.importorskip(
    "validate_artifacts", reason="validate_artifacts not yet implemented"
)
validate = validate_artifacts.validate


def _write_scenario(tmp_path: Path, min_triggers: int) -> Path:
    """Write a minimal scenario YAML for testing."""
    scenario = tmp_path / "scenario.yaml"
    scenario.write_text(
        f"name: test\nassertions:\n  min_triggers: {min_triggers}\n"
    )
    return scenario


def _write_jpeg(path: Path):
    """Write a minimal valid JPEG file."""
    path.write_bytes(b'\xff\xd8\xff\xe0' + b'\x00' * 20 + b'\xff\xd9')


def test_passes_with_enough_images(tmp_path):
    """Passes when image count meets minimum triggers."""
    scenario = _write_scenario(tmp_path, min_triggers=4)
    output = tmp_path / "output"
    output.mkdir()
    for i in range(6):
        _write_jpeg(output / f"img_{i}.jpg")

    assert validate(str(scenario), str(output)) is True


def test_fails_with_too_few(tmp_path):
    """Fails when image count is below minimum triggers."""
    scenario = _write_scenario(tmp_path, min_triggers=4)
    output = tmp_path / "output"
    output.mkdir()
    for i in range(2):
        _write_jpeg(output / f"img_{i}.jpg")

    assert validate(str(scenario), str(output)) is False


def test_validates_jpeg_magic_bytes(tmp_path):
    """Fails when a file doesn't have JPEG magic bytes."""
    scenario = _write_scenario(tmp_path, min_triggers=1)
    output = tmp_path / "output"
    output.mkdir()
    (output / "bad.jpg").write_bytes(b'not a jpeg')

    assert validate(str(scenario), str(output)) is False
