from bennu_camera.backends.libcamera_backend import LibcameraBackend
from bennu_camera.backends.placeholder_backend import PlaceholderBackend
from bennu_camera.capture_backend import CaptureBackend

__all__ = ["LibcameraBackend", "PlaceholderBackend", "create_backend"]

_REGISTRY = {
    "libcamera": LibcameraBackend,
    "placeholder": PlaceholderBackend,
}


def create_backend(name: str) -> CaptureBackend:
    """Create a capture backend by name.

    Raises ValueError if the name is not recognized.
    """
    if name not in _REGISTRY:
        raise ValueError(f"Unknown camera backend: {name} (valid: {', '.join(sorted(_REGISTRY))})")
    return _REGISTRY[name]()
