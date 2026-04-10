"""Tests for the survey grid planner."""

import math

import pytest

from bennu_survey.grid_planner import GridPlanner, SensorParams

IMX477 = SensorParams(
    image_width_px=4056,
    image_height_px=3040,
    focal_length_mm=6.0,
    sensor_width_mm=6.287,
    sensor_height_mm=4.712,
)


def _square_aoi(center_lat: float, center_lon: float, size_m: float):
    """Create a square AOI polygon (approximate, good enough for mid-latitudes)."""
    d_lat = (size_m / 2) / 111320.0
    d_lon = (size_m / 2) / (111320.0 * math.cos(math.radians(center_lat)))
    return [
        (center_lat - d_lat, center_lon - d_lon),
        (center_lat - d_lat, center_lon + d_lon),
        (center_lat + d_lat, center_lon + d_lon),
        (center_lat + d_lat, center_lon - d_lon),
    ]


def test_square_aoi_generates_grid():
    """100x100m square AOI at 80m altitude with 70% overlap should produce a reasonable grid."""
    planner = GridPlanner(
        overlap_front=0.7,
        overlap_side=0.6,
        altitude_m=80.0,
        gsd_cm=2.1,
        sensor=IMX477,
    )
    aoi = _square_aoi(30.0, 31.0, 100.0)
    waypoints = planner.plan(aoi)

    assert len(waypoints) > 0
    for wp in waypoints:
        assert "lat" in wp
        assert "lon" in wp
        assert "alt" in wp
        assert wp["alt"] == 80.0


def test_higher_overlap_more_waypoints():
    """Higher side overlap → narrower line spacing → more waypoints."""
    aoi = _square_aoi(30.0, 31.0, 200.0)

    planner_60 = GridPlanner(
        overlap_front=0.7, overlap_side=0.6, altitude_m=80.0, gsd_cm=2.1, sensor=IMX477
    )
    planner_80 = GridPlanner(
        overlap_front=0.7, overlap_side=0.8, altitude_m=80.0, gsd_cm=2.1, sensor=IMX477
    )

    wp_60 = planner_60.plan(aoi)
    wp_80 = planner_80.plan(aoi)

    assert len(wp_80) > len(wp_60)


def test_rectangular_aoi():
    """Non-square AOI (200m x 50m) should still produce valid waypoints."""
    center_lat, center_lon = 30.0, 31.0
    d_lat_short = 25.0 / 111320.0

    d_lon_long = 100.0 / (111320.0 * math.cos(math.radians(center_lat)))

    aoi = [
        (center_lat - d_lat_short, center_lon - d_lon_long),
        (center_lat - d_lat_short, center_lon + d_lon_long),
        (center_lat + d_lat_short, center_lon + d_lon_long),
        (center_lat + d_lat_short, center_lon - d_lon_long),
    ]

    planner = GridPlanner(
        overlap_front=0.7, overlap_side=0.6, altitude_m=80.0, gsd_cm=2.1, sensor=IMX477
    )
    waypoints = planner.plan(aoi)

    assert len(waypoints) > 0
    for wp in waypoints:
        assert wp["alt"] == 80.0


def test_empty_polygon_raises():
    """Polygon with fewer than 3 vertices is rejected."""
    planner = GridPlanner(
        overlap_front=0.7, overlap_side=0.6, altitude_m=80.0, gsd_cm=2.1, sensor=IMX477
    )
    with pytest.raises(ValueError, match="at least 3 vertices"):
        planner.plan([(0, 0), (1, 1)])

    with pytest.raises(ValueError, match="at least 3 vertices"):
        planner.plan([])
