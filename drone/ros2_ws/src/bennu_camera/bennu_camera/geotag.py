"""GPS geotagging utilities for JPEG images."""
import collections
import subprocess
from dataclasses import dataclass
from typing import Optional, Tuple, Union


def format_gps_coord(
    decimal_degrees: float, is_lat: bool
) -> Tuple[int, int, float, str]:
    """Convert decimal degrees to (degrees, minutes, seconds, ref)."""
    if is_lat:
        ref = "N" if decimal_degrees >= 0 else "S"
    else:
        ref = "E" if decimal_degrees >= 0 else "W"

    decimal_degrees = abs(decimal_degrees)
    degrees = int(decimal_degrees)
    minutes_float = (decimal_degrees - degrees) * 60
    minutes = int(minutes_float)
    seconds = (minutes_float - minutes) * 60

    return degrees, minutes, seconds, ref


def write_gps_exif(
    image_path: str, lat: float, lon: float, alt: float
) -> Union[bool, str]:
    """Write GPS coordinates into JPEG EXIF data using exiftool.

    Returns True on success, or an error description string on failure.
    """
    try:
        subprocess.run(
            [
                "exiftool",
                "-overwrite_original",
                f"-GPSLatitude={lat}",
                f"-GPSLongitude={lon}",
                f"-GPSAltitude={alt}",
                f"-GPSLatitudeRef={'N' if lat >= 0 else 'S'}",
                f"-GPSLongitudeRef={'E' if lon >= 0 else 'W'}",
                "-GPSAltitudeRef=0",
                image_path,
            ],
            check=True,
            capture_output=True,
        )
        return True
    except FileNotFoundError:
        return "exiftool not found — install with: sudo apt install libimage-exiftool-perl"
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode(errors="replace") if e.stderr else "(no stderr)"
        return f"exiftool failed (exit {e.returncode}): {stderr}"
    except OSError as e:
        return f"exiftool could not be launched: {e}"


@dataclass
class ImageMetadata:
    """Per-image metadata — all 18 columns of the images.csv contract."""
    sequence: int
    filename: str
    sensor: str
    timestamp_utc: str
    lat: float
    lon: float
    alt_msl: float
    alt_agl: float
    heading_deg: float
    pitch_deg: float
    roll_deg: float
    rtk_fix_type: str
    position_accuracy_m: float
    gsd_cm: float
    quality_score: float
    quality_flags: str
    ambient_light_lux: Optional[float] = None
    capture_offset_ms: Optional[float] = None

    # Column order matching the contract schema
    _COLUMNS = [
        "sequence", "filename", "sensor", "timestamp_utc",
        "lat", "lon", "alt_msl", "alt_agl",
        "heading_deg", "pitch_deg", "roll_deg",
        "rtk_fix_type", "position_accuracy_m", "gsd_cm",
        "quality_score", "quality_flags",
        "ambient_light_lux", "capture_offset_ms",
    ]

    def to_csv_dict(self) -> "collections.OrderedDict[str, object]":
        """Return ordered dict with all 18 columns for CSV writing."""
        return collections.OrderedDict(
            (col, getattr(self, col)) for col in self._COLUMNS
        )

    @classmethod
    def csv_header(cls) -> list:
        """Return the CSV header row (18 column names)."""
        return list(cls._COLUMNS)


def compute_gsd(
    altitude_m: float,
    focal_length_mm: float,
    sensor_height_mm: float,
    image_height_px: int,
) -> float:
    """Calculate ground sample distance in cm.

    GSD = (altitude * sensor_height) / (focal_length * image_height) * 100

    Returns GSD in centimeters.
    """
    if focal_length_mm <= 0 or image_height_px <= 0:
        raise ValueError("focal_length_mm and image_height_px must be positive")
    return (altitude_m * sensor_height_mm) / (focal_length_mm * image_height_px) * 100
