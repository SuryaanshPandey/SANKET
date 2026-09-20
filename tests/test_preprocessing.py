"""Test image preprocessing: orientation, deskew, perspective, enhancement."""

import io
import cv2
import numpy as np
import pytest
from PIL import Image

from clarity.preprocessing.enhance import preprocess_image_enhancement
from clarity.preprocessing.orient import detect_skew_angle, rotate_image
from clarity.preprocessing.perspective import correct_perspective
from clarity.preprocessing.pipeline import run_preprocessing_pipeline


def make_sample_doc_image():
    """Create a high-contrast synthetic document image."""
    img = np.ones((600, 800, 3), dtype=np.uint8) * 255
    # Draw dark text-like bars
    for y in range(80, 500, 40):
        cv2.line(img, (100, y), (700, y), (0, 0, 0), 4)
    return img


def test_rotate_and_deskew():
    base = make_sample_doc_image()
    # Rotate by 5 degrees
    rotated = rotate_image(base, 5.0)
    assert rotated.shape[0] > 0 and rotated.shape[1] > 0

    # Running deskew
    detected = detect_skew_angle(rotated)
    assert isinstance(detected, float)


def test_enhancement():
    base = make_sample_doc_image()
    # Add noise and darken
    noisy = (base * 0.6).astype(np.uint8)
    enhanced = preprocess_image_enhancement(noisy)
    assert enhanced.shape == noisy.shape


def test_full_preprocessing_pipeline():
    img = Image.new("RGB", (600, 400), color=(240, 240, 240))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    raw_bytes = buf.getvalue()

    result = run_preprocessing_pipeline(raw_bytes)
    assert len(result.preprocessed_bytes) > 0
    assert result.metrics["enhanced"] is True
    assert "original_dimensions" in result.metrics
    assert "final_dimensions" in result.metrics
