import logging
import subprocess
from pathlib import Path

from bennu_camera.capture_backend import CaptureBackend

logger = logging.getLogger(__name__)


class LibcameraBackend(CaptureBackend):
    """Captures images using libcamera-still on real hardware.

    Returns False if libcamera-still is not installed, times out,
    or exits with an error. Each failure mode is logged separately.
    """

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
        except FileNotFoundError:
            logger.error("libcamera-still not found — is libcamera installed?")
            return False
        except subprocess.TimeoutExpired:
            logger.error(
                "libcamera-still timed out after 10s capturing %s", filepath
            )
            return False
        except subprocess.CalledProcessError as e:
            logger.error(
                "libcamera-still failed (exit %d) capturing %s: %s",
                e.returncode,
                filepath,
                e.stderr.decode(errors="replace") if e.stderr else "(no stderr)",
            )
            return False

    @property
    def name(self) -> str:
        return "libcamera"
