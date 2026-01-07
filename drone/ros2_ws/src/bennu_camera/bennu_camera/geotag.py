"""GPS geotagging utilities for JPEG images."""
import subprocess
from typing import Tuple


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
) -> bool:
    """Write GPS coordinates into JPEG EXIF data using exiftool."""
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
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
