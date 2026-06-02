"""Course topics: Harris Corner Detection, Shi-Tomasi Good Features To Track,
and Non-Maximum Suppression.

All three are demonstrated here for academic comparison. Results are returned
as plain coordinate lists so the router can overlay them and report counts.
"""

from __future__ import annotations

import cv2
import numpy as np


def _to_gray(image: np.ndarray) -> np.ndarray:
  if image.ndim == 2:
    return image
  return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def non_max_suppression(
  response: np.ndarray,
  threshold: float,
  window: int = 5,
) -> list[tuple[int, int]]:
  """Non-Maximum Suppression on a dense corner-response map.

  Keeps only points that are the local maximum within a (window x window)
  neighborhood and above `threshold`. This thins the thick Harris response
  blobs into single, well-localized corner points.
  """
  # Dilation spreads each local maximum across its neighborhood; a pixel that
  # equals the dilated value is a local maximum (classic NMS trick).
  dilated = cv2.dilate(response, cv2.getStructuringElement(cv2.MORPH_RECT, (window, window)))
  local_max = (response == dilated) & (response > threshold)
  ys, xs = np.nonzero(local_max)
  return [(int(x), int(y)) for x, y in zip(xs, ys)]


def detect_harris(
  image: np.ndarray,
  *,
  block_size: int = 2,
  ksize: int = 3,
  k: float = 0.04,
  rel_threshold: float = 0.01,
) -> list[tuple[int, int]]:
  """Harris Corner Detection.

  Uses cv2.cornerHarris to compute the corner response, then applies
  Non-Maximum Suppression to get discrete corner points.
  """
  gray = np.float32(_to_gray(image))
  response = cv2.cornerHarris(gray, blockSize=block_size, ksize=ksize, k=k)
  response = cv2.dilate(response, None)
  threshold = rel_threshold * float(response.max() or 1.0)
  return non_max_suppression(response, threshold=threshold, window=5)


def detect_shi_tomasi(
  image: np.ndarray,
  *,
  max_corners: int = 200,
  quality_level: float = 0.01,
  min_distance: int = 7,
) -> list[tuple[int, int]]:
  """Shi-Tomasi 'Good Features To Track'.

  cv2.goodFeaturesToTrack already performs min-distance suppression, which is
  itself a form of Non-Maximum Suppression in the spatial domain.
  """
  gray = _to_gray(image)
  corners = cv2.goodFeaturesToTrack(
    gray,
    maxCorners=max_corners,
    qualityLevel=quality_level,
    minDistance=min_distance,
  )
  if corners is None:
    return []
  return [(int(pt[0][0]), int(pt[0][1])) for pt in corners]


def compare_corners(image: np.ndarray) -> dict:
  """Return Harris vs Shi-Tomasi points + counts for the comparison panel."""
  harris = detect_harris(image)
  shi = detect_shi_tomasi(image)
  return {
    "harris": harris,
    "shi_tomasi": shi,
    "harris_count": len(harris),
    "shi_tomasi_count": len(shi),
  }
