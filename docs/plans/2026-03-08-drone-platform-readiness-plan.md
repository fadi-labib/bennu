# Drone Platform-Readiness — Phase 3 Remaining

**Goal:** Complete Phase 3 (Survey Intelligence) — the final phase of the platform-readiness plan.

**Completed Phases:** Pre-flight bugs, Phase 0 (Foundation), Phase 1 (Data Quality), Phase 2 (Sensor Config) — see [ADR-007](../decisions/007-platform-readiness-phases-0-2.md).

**Design Doc:** `docs/plans/2026-03-08-drone-platform-readiness-design.md`

**Tech Stack:** Python 3.12, ROS2 Jazzy, PX4 v1.16+, uXRCE-DDS, pytest, jsonschema, PyNaCl, Gazebo Harmonic

---

## Phase 3: Survey Intelligence

### ~~Task 14: Grid Planner~~ ✓

Implemented in `bennu_survey/grid_planner.py`. Lawnmower pattern with configurable overlap, WGS84↔UTM projection, point-in-polygon containment. 4 tests passing.

---

### Task 15: Terrain Following

**What:** `adjust_waypoints_for_terrain()` takes planned waypoints and a DEM elevation function, adjusts each waypoint's altitude to maintain constant AGL.

**Why:** Over hilly terrain, flat altitude = variable GSD. Terrain following keeps GSD consistent.

**Module:** `bennu_survey/terrain_follow.py`
**Test:** `drone/ros2_ws/src/bennu_survey/test/test_terrain_follow.py`

**What the code does:**
- `adjust_waypoints_for_terrain(waypoints, target_agl, elevation_fn)` → adjusted waypoints
- Each waypoint's alt = `elevation_fn(lat, lon) + target_agl`

**Tests (2):**
```python
def test_flat_terrain_unchanged()              # All elevations 0 → alt = target_agl
def test_hilly_terrain_adjusts()               # Elevation 100m, 150m → alt 180m, 230m (target_agl=80)
```

**Accept:**
- [ ] Altitude = ground_elevation + target_agl
- [ ] Tests pass

---

### Task 16: Coverage Tracker (Image Footprint Based)

**What:** `CoverageTracker` tracks which planned grid cells are covered by actual image footprints (not waypoint proximity). Reports coverage percentage and identifies gaps.

**Why:** Distance-triggered capture can miss triggers or change spacing. Footprint-based coverage tells you what's actually photographed, not just where the drone flew.

**Module:** `bennu_mission/coverage_tracker.py`
**Test:** `drone/ros2_ws/src/bennu_mission/test/test_coverage_tracker.py`

**What the code does:**
- `CoverageTracker(grid_cells, cell_size_m)` — initializes with planned grid
- `.record_capture(lat, lon, gsd_cm, image_width_px, image_height_px)` — records an image with its footprint
- `.coverage_pct()` → 0.0-1.0 (cells covered / total cells)
- `.gaps()` → list of uncovered grid cells

**Tests (4):**
```python
def test_coverage_starts_at_zero()           # No captures → 0%
def test_coverage_from_image_footprint()     # Large footprint covers nearby cells
def test_partial_coverage()                  # Distant cells require separate captures
def test_gaps_reported()                     # Uncovered cells listed
```

**Accept:**
- [ ] Coverage is footprint-based, not waypoint-proximity-based
- [ ] Gap detection works
- [ ] Tests pass

---

### Task 17: Repeat Mission

**What:** `RepeatMission` loads a previous mission's waypoints and replays them. Tracks deviation from the planned path for repeatability metrics.

**Why:** Change detection requires flying the exact same grid repeatedly. Deviation tracking quantifies how reproducible the flights are.

**Module:** `bennu_mission/repeat_mission.py`
**Test:** `drone/ros2_ws/src/bennu_mission/test/test_repeat_mission.py`

**Tests (2):**
```python
def test_load_previous_waypoints()           # Loads waypoints from previous mission JSON
def test_deviation_zero_for_exact_match()    # Same positions → deviation < 1m
```

**Accept:**
- [ ] Previous mission waypoints loaded correctly
- [ ] Deviation metric makes physical sense (meters)
- [ ] Tests pass

---

### Task 18: Mission Execution Node

**What:** `MissionExecutor` manages flight state machine (idle → armed → takeoff → mission → RTL → land) and waypoint progress. Launch files wire everything for survey and mapping profiles.

**Why:** The planner produces waypoints but nothing executes them. This closes the loop.

**Module:** `bennu_mission/mission_node.py`
**Launch files:** `bennu_bringup/launch/survey.launch.py`, `mapping.launch.py`
**Test:** `drone/ros2_ws/src/bennu_mission/test/test_mission_node.py`

**What the code does:**
- `MissionExecutor(waypoints)` — holds waypoint list
- `.state` → current `MissionState` enum (IDLE, ARMED, TAKEOFF, MISSION, RTL, LANDED)
- `.arm()`, `.takeoff()`, `.advance_waypoint()` — state transitions
- `.progress_pct()` → fraction of waypoints completed
- Full ROS2 node behavior (PX4 topic publishing) tested in SITL, not unit tests

**Tests (3):**
```python
def test_mission_starts_idle()              # Initial state is IDLE
def test_mission_state_transitions()        # arm → ARMED, takeoff → TAKEOFF
def test_waypoint_progress()                # advance_waypoint increments, progress_pct correct
```

**Accept:**
- [ ] State machine has reasonable transitions
- [ ] Launch files wire camera + DDS + executor
- [ ] Unit tests pass
- [ ] SITL smoke test works (deferred to integration phase)

---

**Phase 3 Exit Gate:**
- [x] Grid planner generates waypoints from AOI polygon
- [ ] Terrain following adjusts altitudes from DEM
- [ ] Coverage tracker uses image footprints (not waypoint proximity)
- [ ] Mission executor manages flight state machine
- [ ] Launch files exist for survey and mapping profiles
- [ ] Repeat mission loads previous waypoints with deviation tracking
