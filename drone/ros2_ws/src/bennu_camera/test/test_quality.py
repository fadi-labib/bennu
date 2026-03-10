"""Tests for image quality scoring."""
import numpy as np
import pytest

from bennu_camera.quality import ImageQualityScorer, QualityResult


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
    blurred = np.full((480, 640, 3), 128, dtype=np.uint8)
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
    image = np.random.randint(50, 200, (480, 640, 3), dtype=np.uint8)
    result = scorer.score(image)
    assert "ok" in result.flags
    assert "blur" not in result.flags
    assert "overexposed" not in result.flags
    assert "underexposed" not in result.flags


def test_flags_are_tuple():
    """QualityResult.flags must be a tuple (immutable)."""
    scorer = ImageQualityScorer(blur_threshold=100.0)
    image = np.random.randint(50, 200, (480, 640, 3), dtype=np.uint8)
    result = scorer.score(image)
    assert isinstance(result.flags, tuple)


def test_none_image_raises():
    """Scoring None raises ValueError."""
    scorer = ImageQualityScorer()
    with pytest.raises(ValueError, match="None image"):
        scorer.score(None)


def test_empty_image_raises():
    """Scoring empty array raises ValueError."""
    scorer = ImageQualityScorer()
    with pytest.raises(ValueError, match="empty image"):
        scorer.score(np.array([]))


def test_grayscale_image_accepted():
    """Grayscale (2D) image is scored without error."""
    scorer = ImageQualityScorer(blur_threshold=100.0)
    gray = np.random.randint(50, 200, (480, 640), dtype=np.uint8)
    result = scorer.score(gray)
    assert 0.0 <= result.score <= 1.0


def test_quality_result_frozen():
    """QualityResult is immutable."""
    result = QualityResult(score=0.8, flags=("ok",), blur_variance=150.0)
    with pytest.raises(AttributeError):
        result.score = 0.5
