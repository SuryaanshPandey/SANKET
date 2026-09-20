"""Auto-orientation and deskewing routines."""

import io
from typing import Tuple
import cv2
import numpy as np
from PIL import Image, ImageOps


def auto_orient_exif(image_bytes: bytes) -> Tuple[np.ndarray, bool]:
    """Transpose image according to EXIF orientation tag if present."""
    pil_img = Image.open(io.BytesIO(image_bytes))
    exif_applied = False

    # Apply EXIF transpose
    transposed = ImageOps.exif_transpose(pil_img)
    if transposed != pil_img:
        exif_applied = True

    # Convert to OpenCV RGB -> BGR
    rgb = np.array(transposed.convert("RGB"))
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    return bgr, exif_applied


def detect_skew_angle(cv_image: np.ndarray) -> float:
    """Calculate skew angle of text lines using Hough Line Transform and contours."""
    gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
    # Blur and threshold
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 5
    )

    # Detect lines using Probabilistic Hough Transform
    lines = cv2.HoughLinesP(thresh, 1, np.pi / 180, threshold=100, minLineLength=80, maxLineGap=10)

    angles = []
    if lines is not None:
        for line in lines:
            pts = line.ravel()
            if len(pts) >= 4:
                x1, y1, x2, y2 = pts[:4]
                angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                # Only consider near-horizontal lines (-45 to 45 degrees)
                if -45 < angle < 45:
                    angles.append(angle)

    if angles:
        # Median angle is resilient against vertical margins and noise
        return float(np.median(angles))

    # Fallback to minAreaRect on foreground contours
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) > 50:
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        if -45 < angle < 45:
            return float(angle)

    return 0.0


def rotate_image(cv_image: np.ndarray, angle: float) -> np.ndarray:
    """Rotate image by angle around its center, expanding borders with white background."""
    if abs(angle) < 0.2:
        return cv_image

    (h, w) = cv_image.shape[:2]
    center = (w // 2, h // 2)

    rot_mat = cv2.getRotationMatrix2D(center, angle, 1.0)
    # Compute new bounding dimensions so corners aren't clipped
    cos = np.abs(rot_mat[0, 0])
    sin = np.abs(rot_mat[0, 1])
    new_w = int((h * sin) + (w * cos))
    new_h = int((h * cos) + (w * sin))

    rot_mat[0, 2] += (new_w / 2) - center[0]
    rot_mat[1, 2] += (new_h / 2) - center[1]

    # Warp with white border (typical for document paper)
    rotated = cv2.warpAffine(
        cv_image,
        rot_mat,
        (new_w, new_h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(255, 255, 255),
    )
    return rotated
