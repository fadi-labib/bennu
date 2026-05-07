"""Survey grid planner — generates photogrammetric flight lines from an AOI polygon."""

import math
from dataclasses import dataclass

Coordinate = tuple[float, float]  # (lat, lon) in decimal degrees
Waypoint = dict  # {"lat": float, "lon": float, "alt": float}


@dataclass(frozen=True)
class SensorParams:
    """Camera/sensor geometry needed for footprint calculation."""

    image_width_px: int
    image_height_px: int
    focal_length_mm: float
    sensor_width_mm: float
    sensor_height_mm: float


_WGS84_A = 6378137.0
_WGS84_F = 1 / 298.257223563
_WGS84_E2 = 2 * _WGS84_F - _WGS84_F**2


def _deg2rad(d: float) -> float:
    return d * math.pi / 180.0


def _rad2deg(r: float) -> float:
    return r * 180.0 / math.pi


def _latlon_to_utm(lat: float, lon: float) -> tuple[float, float, int, str]:
    """Convert WGS84 lat/lon to UTM easting/northing.

    Returns (easting, northing, zone_number, zone_letter).
    """
    zone_number = int((lon + 180) / 6) + 1
    zone_letter = "N" if lat >= 0 else "S"

    lon_origin = (zone_number - 1) * 6 - 180 + 3
    lat_rad = _deg2rad(lat)
    lon_rad = _deg2rad(lon)
    lon_origin_rad = _deg2rad(lon_origin)

    N = _WGS84_A / math.sqrt(1 - _WGS84_E2 * math.sin(lat_rad) ** 2)
    T = math.tan(lat_rad) ** 2
    C = (_WGS84_E2 / (1 - _WGS84_E2)) * math.cos(lat_rad) ** 2
    A = math.cos(lat_rad) * (lon_rad - lon_origin_rad)

    e_prime_sq = _WGS84_E2 / (1 - _WGS84_E2)

    M = _WGS84_A * (
        (1 - _WGS84_E2 / 4 - 3 * _WGS84_E2**2 / 64 - 5 * _WGS84_E2**3 / 256) * lat_rad
        - (3 * _WGS84_E2 / 8 + 3 * _WGS84_E2**2 / 32 + 45 * _WGS84_E2**3 / 1024)
        * math.sin(2 * lat_rad)
        + (15 * _WGS84_E2**2 / 256 + 45 * _WGS84_E2**3 / 1024) * math.sin(4 * lat_rad)
        - (35 * _WGS84_E2**3 / 3072) * math.sin(6 * lat_rad)
    )

    k0 = 0.9996

    easting = (
        k0
        * N
        * (
            A
            + (1 - T + C) * A**3 / 6
            + (5 - 18 * T + T**2 + 72 * C - 58 * e_prime_sq) * A**5 / 120
        )
        + 500000.0
    )

    northing = k0 * (
        M
        + N
        * math.tan(lat_rad)
        * (
            A**2 / 2
            + (5 - T + 9 * C + 4 * C**2) * A**4 / 24
            + (61 - 58 * T + T**2 + 600 * C - 330 * e_prime_sq) * A**6 / 720
        )
    )

    if lat < 0:
        northing += 10000000.0

    return easting, northing, zone_number, zone_letter


def _utm_to_latlon(
    easting: float, northing: float, zone_number: int, zone_letter: str
) -> tuple[float, float]:
    """Convert UTM easting/northing back to WGS84 lat/lon."""
    k0 = 0.9996
    e_prime_sq = _WGS84_E2 / (1 - _WGS84_E2)

    x = easting - 500000.0
    y = northing
    if zone_letter == "S":
        y -= 10000000.0

    M = y / k0
    mu = M / (_WGS84_A * (1 - _WGS84_E2 / 4 - 3 * _WGS84_E2**2 / 64 - 5 * _WGS84_E2**3 / 256))

    e1 = (1 - math.sqrt(1 - _WGS84_E2)) / (1 + math.sqrt(1 - _WGS84_E2))

    phi1 = (
        mu
        + (3 * e1 / 2 - 27 * e1**3 / 32) * math.sin(2 * mu)
        + (21 * e1**2 / 16 - 55 * e1**4 / 32) * math.sin(4 * mu)
        + (151 * e1**3 / 96) * math.sin(6 * mu)
        + (1097 * e1**4 / 512) * math.sin(8 * mu)
    )

    N1 = _WGS84_A / math.sqrt(1 - _WGS84_E2 * math.sin(phi1) ** 2)
    T1 = math.tan(phi1) ** 2
    C1 = e_prime_sq * math.cos(phi1) ** 2
    R1 = _WGS84_A * (1 - _WGS84_E2) / (1 - _WGS84_E2 * math.sin(phi1) ** 2) ** 1.5
    D = x / (N1 * k0)

    lat = phi1 - (N1 * math.tan(phi1) / R1) * (
        D**2 / 2
        - (5 + 3 * T1 + 10 * C1 - 4 * C1**2 - 9 * e_prime_sq) * D**4 / 24
        + (61 + 90 * T1 + 298 * C1 + 45 * T1**2 - 252 * e_prime_sq - 3 * C1**2) * D**6 / 720
    )

    lon_origin = _deg2rad((zone_number - 1) * 6 - 180 + 3)
    lon = lon_origin + (
        D
        - (1 + 2 * T1 + C1) * D**3 / 6
        + (5 - 2 * C1 + 28 * T1 - 3 * C1**2 + 8 * e_prime_sq + 24 * T1**2) * D**5 / 120
    ) / math.cos(phi1)

    return _rad2deg(lat), _rad2deg(lon)


class GridPlanner:
    """Generates survey waypoints for photogrammetric coverage of an AOI polygon.

    Uses a lawnmower (boustrophedon) pattern with configurable front/side overlap.
    All distance computations use UTM projection.
    """

    def __init__(
        self,
        overlap_front: float,
        overlap_side: float,
        altitude_m: float,
        gsd_cm: float,
        sensor: SensorParams,
    ):
        if not (0.0 < overlap_front < 1.0):
            raise ValueError(f"overlap_front must be in (0, 1), got {overlap_front}")
        if not (0.0 < overlap_side < 1.0):
            raise ValueError(f"overlap_side must be in (0, 1), got {overlap_side}")
        if altitude_m <= 0:
            raise ValueError(f"altitude_m must be positive, got {altitude_m}")
        if gsd_cm <= 0:
            raise ValueError(f"gsd_cm must be positive, got {gsd_cm}")

        self.overlap_front = overlap_front
        self.overlap_side = overlap_side
        self.altitude_m = altitude_m
        self.gsd_cm = gsd_cm
        self.sensor = sensor

        self._footprint_x_m = (gsd_cm / 100.0) * sensor.image_width_px
        self._footprint_y_m = (gsd_cm / 100.0) * sensor.image_height_px
        self._line_spacing_m = self._footprint_x_m * (1.0 - overlap_side)
        self._shot_spacing_m = self._footprint_y_m * (1.0 - overlap_front)

    def plan(self, aoi_polygon: list[Coordinate]) -> list[Waypoint]:
        """Generate survey waypoints covering the AOI polygon.

        Args:
            aoi_polygon: List of (lat, lon) vertices defining the area of interest.
                         Must have at least 3 non-degenerate vertices.

        Returns:
            List of waypoint dicts with keys: lat, lon, alt.
        """
        if len(aoi_polygon) < 3:
            raise ValueError(f"AOI polygon must have at least 3 vertices, got {len(aoi_polygon)}")

        ref_lat = aoi_polygon[0][0]
        ref_lon = aoi_polygon[0][1]
        _, _, zone_number, zone_letter = _latlon_to_utm(ref_lat, ref_lon)

        utm_points = []
        for lat, lon in aoi_polygon:
            e, n, _, _ = _latlon_to_utm(lat, lon)
            utm_points.append((e, n))

        min_e = min(p[0] for p in utm_points)
        max_e = max(p[0] for p in utm_points)
        min_n = min(p[1] for p in utm_points)
        max_n = max(p[1] for p in utm_points)

        if (max_e - min_e) < 1e-6 or (max_n - min_n) < 1e-6:
            raise ValueError("AOI polygon is degenerate (zero area)")

        waypoints: list[Waypoint] = []
        line_x = min_e + self._line_spacing_m / 2.0
        line_idx = 0

        while line_x <= max_e:
            y_start = min_n + self._shot_spacing_m / 2.0
            y_positions = []
            y = y_start
            while y <= max_n:
                if self._point_in_polygon_utm(line_x, y, utm_points):
                    y_positions.append(y)
                y += self._shot_spacing_m

            if line_idx % 2 == 1:
                y_positions.reverse()

            for y_pos in y_positions:
                lat, lon = _utm_to_latlon(line_x, y_pos, zone_number, zone_letter)
                waypoints.append({"lat": lat, "lon": lon, "alt": self.altitude_m})

            line_x += self._line_spacing_m
            line_idx += 1

        return waypoints

    @staticmethod
    def _point_in_polygon_utm(x: float, y: float, polygon: list[tuple[float, float]]) -> bool:
        """Ray-casting point-in-polygon test in UTM coordinates."""
        n = len(polygon)
        inside = False
        j = n - 1
        for i in range(n):
            xi, yi = polygon[i]
            xj, yj = polygon[j]
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            j = i
        return inside
