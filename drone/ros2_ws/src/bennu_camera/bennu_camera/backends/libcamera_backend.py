import subprocess
from pathlib import Path
from bennu_camera.capture_backend import CaptureBackend


class LibcameraBackend(CaptureBackend):
    """Captures images using libcamera-still on real hardware."""

    def capture(self, filepath: Path, width: int, height: int) -> bool:
        try:
            subprocess.run(
                [
                    "libcamera-still",
                    "-o", str(filepath),
                    "--width", str(width),
                    "--height", str(height),
                    "--nopreview",
                    "-t", "1",
                ],
                check=True,
                capture_output=True,
                timeout=10,
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired,
                FileNotFoundError):
            return False

    @property
    def name(self) -> str:
        return "libcamera"
