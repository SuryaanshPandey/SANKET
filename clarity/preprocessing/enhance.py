"""Denoising and contrast enhancement for low-light, shadowed, or degraded documents."""

import cv2
import numpy as np


def enhance_contrast_clahe(cv_image: np.ndarray, clip_limit: float = 2.0, tile_grid_size: int = 8) -> np.ndarray:
    """Apply CLAHE on the Lightness channel of LAB color space to equalize shadows/lighting."""
    # Convert BGR to LAB
    lab = cv2.cvtColor(cv_image, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)

    # Apply CLAHE to L channel
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile_grid_size, tile_grid_size))
    cl = clahe.apply(l_channel)

    # Merge channels and convert back to BGR
    merged = cv2.merge((cl, a_channel, b_channel))
    enhanced = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
    return enhanced


def denoise_document(cv_image: np.ndarray) -> np.ndarray:
    """Apply bilateral filtering to eliminate sensor noise and paper grain while preserving sharp text."""
    # d=7, sigmaColor=50, sigmaSpace=50
    denoised = cv2.bilateralFilter(cv_image, d=7, sigmaColor=50, sigmaSpace=50)
    return denoised


def preprocess_image_enhancement(cv_image: np.ndarray) -> np.ndarray:
    """Full enhancement pipeline for document images."""
    denoised = denoise_document(cv_image)
    enhanced = enhance_contrast_clahe(denoised, clip_limit=2.0, tile_grid_size=8)
    return enhanced
