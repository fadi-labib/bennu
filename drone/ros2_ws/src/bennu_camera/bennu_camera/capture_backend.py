from abc import ABC, abstractmethod
from pathlib import Path


class CaptureBackend(ABC):
    """Abstract base for image capture backends."""

    @abstractmethod
    def capture(self, filepath: Path, width: int, height: int) -> bool:
        """Capture an image to filepath. Returns True on success."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Backend identifier string."""
        ...

    def is_available(self) -> bool:
        """Check if this backend can function in the current environment."""
        return True
