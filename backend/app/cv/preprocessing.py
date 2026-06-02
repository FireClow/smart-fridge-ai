"""Course topic: Image Filtering & Enhancement.

Provides a small preprocessing pipeline that can run BEFORE YOLO inference.
Modes:
  - none      : return the image unchanged
  - gaussian  : Gaussian blur (linear smoothing, removes high-freq noise)
  - bilateral : Bilateral filter (edge-preserving smoothing)
  - clahe     : Contrast Limited Adaptive Histogram Equalization (enhancement)

All implementations use OpenCV.
"""

from __future__ import annotations

import cv2
import numpy as np

VALID_MODES = ("none", "gaussian", "bilateral", "clahe")


def normalize_mode(mode: str | None) -> str:
  """Return a safe, lower-cased mode, defaulting to 'none'."""
  if not mode:
    return "none"
  m = str(mode).strip().lower()
  return m if m in VALID_MODES else "none"


def apply_preprocess(image: np.ndarray, mode: str | None) -> np.ndarray:
  """Apply the selected filter and return a new BGR image.

  Image Filtering & Enhancement: each branch demonstrates a different
  classical filtering technique taught in the course.
  """
  m = normalize_mode(mode)

  if m == "none":
    return image

  if m == "gaussian":
    # Gaussian blur: convolution with a Gaussian kernel (low-pass filter).
    return cv2.GaussianBlur(image, (5, 5), sigmaX=0)

  if m == "bilateral":
    # Bilateral filter: smooths flat regions while preserving strong edges.
    return cv2.bilateralFilter(image, d=9, sigmaColor=75, sigmaSpace=75)

  if m == "clahe":
    # CLAHE on the L channel of LAB to enhance local contrast without
    # blowing out global brightness (histogram-equalization enhancement).
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_eq = clahe.apply(l_channel)
    merged = cv2.merge((l_eq, a_channel, b_channel))
    return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

  return image
