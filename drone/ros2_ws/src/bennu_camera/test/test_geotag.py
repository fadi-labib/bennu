"""Tests for geotagging utility functions."""
import os
import shutil
import tempfile
import pytest
from unittest.mock import patch

from bennu_camera.geotag import write_gps_exif, format_gps_coord

HAS_EXIFTOOL = shutil.which("exiftool") is not None


class TestFormatGpsCoord:
    def test_positive_latitude(self):
        # 37.7749° N
        degrees, minutes, seconds, ref = format_gps_coord(37.7749, is_lat=True)
        assert ref == "N"
        assert degrees == 37
        assert minutes == 46
        assert 29.0 < seconds < 30.0

    def test_negative_latitude(self):
        # -33.8688° S
        degrees, minutes, seconds, ref = format_gps_coord(-33.8688, is_lat=True)
        assert ref == "S"
        assert degrees == 33

    def test_positive_longitude(self):
        # 2.3522° E
        degrees, minutes, seconds, ref = format_gps_coord(2.3522, is_lat=False)
        assert ref == "E"
        assert degrees == 2

    def test_negative_longitude(self):
        degrees, minutes, seconds, ref = format_gps_coord(-122.4194, is_lat=False)
        assert ref == "W"
        assert degrees == 122

    def test_zero(self):
        degrees, minutes, seconds, ref = format_gps_coord(0.0, is_lat=True)
        assert degrees == 0
        assert minutes == 0
        assert ref == "N"


class TestWriteGpsExif:
    @pytest.mark.skipif(not HAS_EXIFTOOL, reason="exiftool not installed")
    def test_writes_exif_to_jpeg(self):
        """Create a minimal JPEG, write GPS EXIF, verify it was written."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            # Minimal JPEG file (1x1 white pixel)
            f.write(bytes([
                0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46,
                0x49, 0x46, 0x00, 0x01, 0x01, 0x00, 0x00, 0x01,
                0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
                0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08,
                0x07, 0x07, 0x07, 0x09, 0x09, 0x08, 0x0A, 0x0C,
                0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
                0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D,
                0x1A, 0x1C, 0x1C, 0x20, 0x24, 0x2E, 0x27, 0x20,
                0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
                0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27,
                0x39, 0x3D, 0x38, 0x32, 0x3C, 0x2E, 0x33, 0x34,
                0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
                0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4,
                0x00, 0x1F, 0x00, 0x00, 0x01, 0x05, 0x01, 0x01,
                0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00,
                0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04,
                0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0xFF,
                0xDA, 0x00, 0x08, 0x01, 0x01, 0x00, 0x00, 0x3F,
                0x00, 0x7B, 0x40, 0x1B, 0xFF, 0xD9
            ]))
            temp_path = f.name

        try:
            result = write_gps_exif(temp_path, 37.7749, -122.4194, 50.0)
            assert result is True

            # Verify with exiftool if available
            import subprocess
            try:
                output = subprocess.check_output(
                    ["exiftool", "-GPSLatitude", "-GPSLongitude", "-n", temp_path],
                    text=True
                )
                assert "37.77" in output
                assert "122.41" in output
            except FileNotFoundError:
                # exiftool not installed, skip verification
                pass
        finally:
            os.unlink(temp_path)


class TestWriteGpsExifErrors:
    def test_returns_error_message_when_exiftool_missing(self, tmp_path):
        """write_gps_exif returns error string when exiftool is not installed."""
        jpeg = tmp_path / "test.jpg"
        jpeg.write_bytes(b'\xff\xd8\xff\xd9')  # minimal JPEG
        with patch(
            "bennu_camera.geotag.subprocess.run",
            side_effect=FileNotFoundError("exiftool"),
        ):
            result = write_gps_exif(str(jpeg), 37.0, -122.0, 50.0)
        assert result is not True
        assert "exiftool" in result.lower()

    def test_returns_error_message_on_process_failure(self, tmp_path):
        """write_gps_exif returns error string on subprocess failure."""
        import subprocess as sp
        jpeg = tmp_path / "test.jpg"
        jpeg.write_bytes(b'\xff\xd8\xff\xd9')
        with patch(
            "bennu_camera.geotag.subprocess.run",
            side_effect=sp.CalledProcessError(1, "exiftool", stderr=b"bad image"),
        ):
            result = write_gps_exif(str(jpeg), 37.0, -122.0, 50.0)
        assert result is not True
        assert isinstance(result, str)
        assert "bad image" in result

    def test_returns_no_stderr_fallback_on_process_failure(self, tmp_path):
        """write_gps_exif handles CalledProcessError with stderr=None."""
        import subprocess as sp
        jpeg = tmp_path / "test.jpg"
        jpeg.write_bytes(b'\xff\xd8\xff\xd9')
        with patch(
            "bennu_camera.geotag.subprocess.run",
            side_effect=sp.CalledProcessError(1, "exiftool", stderr=None),
        ):
            result = write_gps_exif(str(jpeg), 37.0, -122.0, 50.0)
        assert result is not True
        assert "(no stderr)" in result
