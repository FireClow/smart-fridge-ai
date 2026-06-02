"""Course topic: ORB (Oriented FAST and Rotated BRIEF) descriptors.

ORB detects FAST keypoints, assigns orientation, and computes a rotation-aware
binary BRIEF descriptor. Binary descriptors are matched with Hamming distance
(see matching.py).
"""

from __future__ import annotations

import cv2
import numpy as np

# A single shared detector instance is fine; ORB is stateless per call.
_ORB = cv2.ORB_create(nfeatures=500)


def _to_gray(image: np.ndarray) -> np.ndarray:
  if image.ndim == 2:
    return image
  return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def extract_orb(image: np.ndarray):
  """Return (keypoints, descriptors) for an image (or crop).

  keypoints: list[cv2.KeyPoint]
  descriptors: np.ndarray of shape (N, 32) dtype=uint8, or None when N == 0.
  """
  gray = _to_gray(image)
  keypoints, descriptors = _ORB.detectAndCompute(gray, None)
  return list(keypoints or []), descriptors


def orb_summary(image: np.ndarray) -> dict:
  """Counts for the dashboard: keypoints and descriptor rows."""
  keypoints, descriptors = extract_orb(image)
  descriptor_count = int(descriptors.shape[0]) if descriptors is not None else 0
  return {
    "keypoint_count": len(keypoints),
    "descriptor_count": descriptor_count,
    "keypoints": [(int(kp.pt[0]), int(kp.pt[1])) for kp in keypoints],
  }
