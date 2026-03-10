"""Tests for image quality scoring."""
import numpy as np

from bennu_camera.quality import ImageQualityScorer


def test_sharp_image_scores_high():
    """Random noise (high frequency content) scores high."""
    scorer = ImageQualityScorer(blur_threshold=100.0)
    image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    result = scorer.score(image)
    assert result.score > 0.5
    assert "ok" in result.flags


def test_blurry_image_scores_low():
    """Heavily blurred image gets blur flag."""
    scorer = ImageQualityScorer(blur_threshold=100.0)
    # Create sharp image then blur it
    image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    blurred = np.full_like(image, 128)  # Uniform = zero variance
    result = scorer.score(blurred)
    assert result.score <= 0.5
    assert "blur" in result.flags


def test_overexposed_image_flagged():
    """White image gets overexposed flag."""
    scorer = ImageQualityScorer(blur_threshold=100.0)
    image = np.full((480, 640, 3), 250, dtype=np.uint8)
    result = scorer.score(image)
    assert "overexposed" in result.flags


def test_underexposed_image_flagged():
    """Black image gets underexposed flag."""
    scorer = ImageQualityScorer(blur_threshold=100.0)
    image = np.full((480, 640, 3), 5, dtype=np.uint8)
    result = scorer.score(image)
    assert "underexposed" in result.flags


def test_quality_flags_include_ok():
    """Normal image gets only 'ok' flag."""
    scorer = ImageQualityScorer(blur_threshold=100.0)
    # Create an image with varied content (not uniform)
    image = np.random.randint(50, 200, (480, 640, 3), dtype=np.uint8)
    result = scorer.score(image)
    assert "ok" in result.flags
    assert "blur" not in result.flags
    assert "overexposed" not in result.flags
    assert "underexposed" not in result.flags
