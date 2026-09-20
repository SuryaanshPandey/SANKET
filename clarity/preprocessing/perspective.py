"""Perspective detection and quadrilateral correction."""

from typing import Optional, Tuple
import cv2
import numpy as np


def order_points(pts: np.ndarray) -> np.ndarray:
    """Order points in [top-left, top-right, bottom-right, bottom-left] order."""
    rect = np.zeros((4, 2), dtype="float32")

    # Sum: top-left has smallest sum, bottom-right has largest sum
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    # Diff: top-right has smallest diff, bottom-left has largest diff
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    return rect


def find_document_quadrilateral(cv_image: np.ndarray) -> Optional[np.ndarray]:
    """Find the 4-corner quadrilateral boundary of a document in the photo."""
    h, w = cv_image.shape[:2]
    image_area = h * w

    # Resize image for fast contour detection
    ratio = 800.0 / max(h, w)
    if ratio < 1.0:
        small = cv2.resize(cv_image, (int(w * ratio), int(h * ratio)))
    else:
        small = cv_image.copy()
        ratio = 1.0

    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 50, 150)

    # Morphological closing to bridge gaps
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    closed = cv2.morphologyEx(edged, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # Sort contours by area descending
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

    for c in contours:
        area = cv2.contourArea(c)
        # Only accept if contour occupies at least 25% of the total frame
        if area < (0.25 * small.shape[0] * small.shape[1]):
            continue

        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)

        # If approximation has 4 points and is convex
        if len(approx) == 4 and cv2.isContourConvex(approx):
            # Scale coordinates back to original resolution
            pts = approx.reshape(4, 2).astype("float32") / ratio
            return pts

    return None


def correct_perspective(cv_image: np.ndarray) -> Tuple[np.ndarray, bool]:
    """Perspective-correct document if angled in frame. Returns (image, was_corrected)."""
    quad = find_document_quadrilateral(cv_image)
    if quad is None:
        return cv_image, False

    rect = order_points(quad)
    (tl, tr, br, bl) = rect

    # Compute width of new image
    width_a = np.linalg.norm(br - bl)
    width_b = np.linalg.norm(tr - tl)
    max_width = max(int(width_a), int(width_b))

    # Compute height of new image
    height_a = np.linalg.norm(tr - br)
    height_b = np.linalg.norm(tl - bl)
    max_height = max(int(height_a), int(height_b))

    # Guard against extreme or degenerate warp
    if max_width < 100 or max_height < 100:
        return cv_image, False

    aspect_ratio = max_width / float(max_height)
    if aspect_ratio < 0.2 or aspect_ratio > 5.0:
        return cv_image, False

    dst = np.array(
        [
            [0, 0],
            [max_width - 1, 0],
            [max_width - 1, max_height - 1],
            [0, max_height - 1],
        ],
        dtype="float32",
    )

    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(
        cv_image,
        M,
        (max_width, max_height),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(255, 255, 255),
    )
    return warped, True
