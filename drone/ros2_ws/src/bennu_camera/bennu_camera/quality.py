"""Image quality scoring — blur detection and exposure analysis."""
from dataclasses import dataclass
from typing import List

import cv2
import numpy as np


@dataclass(frozen=True)
class QualityResult:
    """Result of image quality analysis."""
    score: float           # 0.0-1.0 composite quality score
    flags: tuple           # "ok", "blur", "overexposed", "underexposed", "invalid"
    blur_variance: float   # Laplacian variance (higher = sharper)

    def __post_init__(self):
        if not (0.0 <= self.score <= 1.0):
            raise ValueError(f"score must be in [0.0, 1.0], got {self.score}")
        if not self.flags:
            raise ValueError("flags must not be empty")


class ImageQualityScorer:
    """Scores image quality using blur detection and exposure analysis."""

    def __init__(self, blur_threshold: float = 100.0):
        self._blur_threshold = blur_threshold

    def score(self, image: np.ndarray) -> QualityResult:
        """Analyze image quality.

        Args:
            image: BGR or grayscale numpy array (as from cv2.imread).

        Returns:
            QualityResult with score, flags, and blur_variance.

        Raises:
            ValueError: If image is None or empty (capture failure).
        """
        if image is None:
            raise ValueError("Cannot score a None image — capture likely failed")
        if image.size == 0:
            raise ValueError("Cannot score an empty image array")

        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        flags: List[str] = []
        penalties = 0.0

        # Blur detection via Laplacian variance
        blur_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        if blur_var < self._blur_threshold:
            flags.append("blur")
            penalties += 0.5

        # Exposure analysis via histogram
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
        total_pixels = gray.shape[0] * gray.shape[1]

        # Overexposed: >40% of pixels in top 10% brightness
        bright_pct = hist[230:].sum() / total_pixels
        if bright_pct > 0.4:
            flags.append("overexposed")
            penalties += 0.4

        # Underexposed: >40% of pixels in bottom 10% brightness
        dark_pct = hist[:25].sum() / total_pixels
        if dark_pct > 0.4:
            flags.append("underexposed")
            penalties += 0.4

        if not flags:
            flags.append("ok")

        score = max(0.0, min(1.0, 1.0 - penalties))
        return QualityResult(score=score, flags=tuple(flags), blur_variance=blur_var)
