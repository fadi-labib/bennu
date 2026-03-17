"""Tests for scenario matrix runner."""
import asyncio
from pathlib import Path

import pytest
from run_scenarios import (
    ScenarioResult,
    discover_scenarios,
    load_scenario_name,
    print_summary,
    run_all_scenarios,
    run_single_scenario,
)


def _write_scenario(path: Path, name: str = "test_scenario") -> Path:
    """Write a minimal scenario YAML and return its path."""
    path.write_text(
        f"name: {name}\nmission:\n  type: grid\n  altitude_m: 30\n"
        f"  speed_mps: 3\n  waypoints: 4\nassertions:\n  min_triggers: 2\n"
    )
    return path


# ---------------------------------------------------------------------------
# discover_scenarios
# ---------------------------------------------------------------------------


def test_discover_finds_yaml_files(tmp_path):
    """Discovers .yaml files in a directory."""
    _write_scenario(tmp_path / "a.yaml", "alpha")
    _write_scenario(tmp_path / "b.yaml", "beta")
    (tmp_path / "not_yaml.txt").write_text("ignore me")

    found = discover_scenarios(str(tmp_path))
    assert len(found) == 2
    assert found[0].endswith("a.yaml")
    assert found[1].endswith("b.yaml")


def test_discover_empty_directory(tmp_path):
    """Returns empty list when no YAML files exist."""
    found = discover_scenarios(str(tmp_path))
    assert found == []


def test_discover_nonexistent_directory():
    """Raises FileNotFoundError for missing directory."""
    with pytest.raises(FileNotFoundError, match="does not exist"):
        discover_scenarios("/nonexistent/path")


def test_discover_returns_sorted(tmp_path):
    """Results are sorted alphabetically."""
    _write_scenario(tmp_path / "z_last.yaml", "z")
    _write_scenario(tmp_path / "a_first.yaml", "a")

    found = discover_scenarios(str(tmp_path))
    assert Path(found[0]).name == "a_first.yaml"
    assert Path(found[1]).name == "z_last.yaml"


# ---------------------------------------------------------------------------
# load_scenario_name
# ---------------------------------------------------------------------------


def test_load_scenario_name(tmp_path):
    """Extracts name from scenario YAML."""
    path = _write_scenario(tmp_path / "test.yaml", "my_mission")
    assert load_scenario_name(str(path)) == "my_mission"


def test_load_scenario_name_fallback(tmp_path):
    """Falls back to filename stem when name key is missing."""
    path = tmp_path / "fallback.yaml"
    path.write_text("mission:\n  type: grid\n")
    assert load_scenario_name(str(path)) == "fallback"


# ---------------------------------------------------------------------------
# ScenarioResult
# ---------------------------------------------------------------------------


def test_scenario_result_defaults():
    """ScenarioResult has sensible defaults."""
    r = ScenarioResult(name="test", path="/tmp/test.yaml", passed=True, duration_s=1.5)
    assert r.error is None
    assert r.passed is True


def test_scenario_result_with_error():
    """ScenarioResult can carry an error message."""
    r = ScenarioResult(
        name="fail", path="/tmp/fail.yaml", passed=False, duration_s=0.1, error="boom"
    )
    assert r.passed is False
    assert r.error == "boom"


# ---------------------------------------------------------------------------
# run_single_scenario (mocked)
# ---------------------------------------------------------------------------


def test_run_single_scenario_success(tmp_path):
    """Successful mission run produces a passing result."""
    path = _write_scenario(tmp_path / "ok.yaml", "ok_scenario")

    async def _mock_runner(**kwargs):
        return True

    result = asyncio.run(
        run_single_scenario(str(path), address="udp://:14540", timeout=10, runner=_mock_runner)
    )
    assert result.passed is True
    assert result.name == "ok_scenario"
    assert result.error is None
    assert result.duration_s >= 0


def test_run_single_scenario_failure(tmp_path):
    """Failed mission run produces a failing result."""
    path = _write_scenario(tmp_path / "fail.yaml", "fail_scenario")

    async def _mock_runner(**kwargs):
        return False

    result = asyncio.run(
        run_single_scenario(str(path), address="udp://:14540", timeout=10, runner=_mock_runner)
    )
    assert result.passed is False
    assert result.name == "fail_scenario"


def test_run_single_scenario_exception(tmp_path):
    """Exception during mission produces a failing result with error message."""
    path = _write_scenario(tmp_path / "crash.yaml", "crash_scenario")

    async def _mock_runner(**kwargs):
        raise ConnectionError("PX4 not reachable")

    result = asyncio.run(
        run_single_scenario(str(path), address="udp://:14540", timeout=10, runner=_mock_runner)
    )
    assert result.passed is False
    assert "PX4 not reachable" in result.error


# ---------------------------------------------------------------------------
# run_all_scenarios (mocked)
# ---------------------------------------------------------------------------


def test_run_all_scenarios_empty(tmp_path):
    """Empty directory produces empty results."""
    results = asyncio.run(
        run_all_scenarios(str(tmp_path), address="udp://:14540", timeout=10)
    )
    assert results == []


def test_run_all_scenarios_mixed(tmp_path):
    """Mixed pass/fail scenarios produce correct result list."""
    _write_scenario(tmp_path / "a.yaml", "pass_scenario")
    _write_scenario(tmp_path / "b.yaml", "fail_scenario")

    call_count = 0

    async def _mock_runner(**kwargs):
        nonlocal call_count
        call_count += 1
        # First scenario passes, second fails
        return call_count == 1

    results = asyncio.run(
        run_all_scenarios(str(tmp_path), address="udp://:14540", timeout=10, runner=_mock_runner)
    )
    assert len(results) == 2
    assert results[0].passed is True
    assert results[1].passed is False


# ---------------------------------------------------------------------------
# print_summary
# ---------------------------------------------------------------------------


def test_print_summary_output(capsys):
    """Summary prints pass/fail counts."""
    results = [
        ScenarioResult(name="a", path="a.yaml", passed=True, duration_s=1.0),
        ScenarioResult(name="b", path="b.yaml", passed=False, duration_s=2.0, error="timeout"),
    ]
    print_summary(results)
    output = capsys.readouterr().out
    assert "1/2 scenarios passed" in output
    assert "[PASS] a" in output
    assert "[FAIL] b" in output
    assert "timeout" in output
