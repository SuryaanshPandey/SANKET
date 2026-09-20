"""Orchestrator for document image preprocessing."""

from dataclasses import asdict, dataclass
import io
from typing import Any, Dict, Tuple
import cv2
import numpy as np

from clarity.preprocessing.enhance import preprocess_image_enhancement
from clarity.preprocessing.orient import auto_orient_exif, detect_skew_angle, rotate_image
from clarity.preprocessing.perspective import correct_perspective


@dataclass
class PreprocessingResult:
    preprocessed_bytes: bytes
    metrics: Dict[str, Any]
    image_width: int
    image_height: int


def run_preprocessing_pipeline(image_bytes: bytes) -> PreprocessingResult:
    """Run full evidentiary preprocessing pipeline on untouched raw bytes.

    Never mutates original bytes; produces a clean derivative image optimized
    for optical OCR and vision-language comprehension.
    """
    # 1. EXIF orientation
    cv_img, exif_applied = auto_orient_exif(image_bytes)
    orig_h, orig_w = cv_img.shape[:2]

    # 2. Perspective correction
    perspective_img, perspective_applied = correct_perspective(cv_img)

    # 3. Deskew
    skew_angle = detect_skew_angle(perspective_img)
    deskewed_img = rotate_image(perspective_img, skew_angle)

    # 4. Contrast enhancement & Denoising
    enhanced_img = preprocess_image_enhancement(deskewed_img)

    # Normalize resolution for VLM processing if max dimension > 1024
    max_dim = max(enhanced_img.shape[:2])
    if max_dim > 1024:
        scale = 1024.0 / max_dim
        new_w = int(enhanced_img.shape[1] * scale)
        new_h = int(enhanced_img.shape[0] * scale)
        enhanced_img = cv2.resize(enhanced_img, (new_w, new_h), interpolation=cv2.INTER_AREA)

    final_h, final_w = enhanced_img.shape[:2]

    # Encode derivative to PNG
    success, encoded = cv2.imencode(".png", enhanced_img)
    if not success:
        raise RuntimeError("Failed to encode preprocessed image to PNG")

    derivative_bytes = encoded.tobytes()

    metrics = {
        "original_dimensions": [orig_w, orig_h],
        "final_dimensions": [final_w, final_h],
        "exif_transposed": exif_applied,
        "perspective_corrected": perspective_applied,
        "deskew_angle_degrees": round(skew_angle, 2),
        "enhanced": True,
    }

    return PreprocessingResult(
        preprocessed_bytes=derivative_bytes,
        metrics=metrics,
        image_width=final_w,
        image_height=final_h,
    )
