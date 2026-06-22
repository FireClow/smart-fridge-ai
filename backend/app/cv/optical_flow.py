"""Course topic: Optical Flow (Lucas-Kanade, pyramidal).

Estimates sparse motion between two consecutive frames using
cv2.calcOpticalFlowPyrLK on Shi-Tomasi feature points. Returns motion vectors
and the average motion magnitude, used to infer fridge activity.
"""

from __future__ import annotations

import cv2
import numpy as np

_LK_PARAMS = dict(
  winSize=(15, 15),
  maxLevel=2,
  criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03),
)

_FEATURE_PARAMS = dict(
  maxCorners=120,
  qualityLevel=0.01,
  minDistance=7,
  blockSize=7,
)


def to_gray(image: np.ndarray) -> np.ndarray:
  if image.ndim == 2:
    return image
  return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def calc_optical_flow(prev_gray: np.ndarray, curr_gray: np.ndarray) -> dict:
  """Lucas-Kanade optical flow between two grayscale frames.

  Returns:
    vectors: list of ((x0, y0), (x1, y1)) point pairs that were tracked.
    avg_magnitude: mean Euclidean displacement of tracked points.
    point_count: number of successfully tracked points.
  """
  if prev_gray.shape != curr_gray.shape:
    curr_gray = cv2.resize(curr_gray, (prev_gray.shape[1], prev_gray.shape[0]))
  if not prev_gray.flags["C_CONTIGUOUS"]:
    prev_gray = np.ascontiguousarray(prev_gray)
  if not curr_gray.flags["C_CONTIGUOUS"]:
    curr_gray = np.ascontiguousarray(curr_gray)

  prev_pts = cv2.goodFeaturesToTrack(prev_gray, mask=None, **_FEATURE_PARAMS)
  if prev_pts is None:
    return {"vectors": [], "avg_magnitude": 0.0, "point_count": 0}

  next_pts, status, _err = cv2.calcOpticalFlowPyrLK(
    prev_gray, curr_gray, prev_pts, None, **_LK_PARAMS
  )
  if next_pts is None or status is None:
    return {"vectors": [], "avg_magnitude": 0.0, "point_count": 0}

  status = status.reshape(-1)
  good_prev = prev_pts.reshape(-1, 2)[status == 1]
  good_next = next_pts.reshape(-1, 2)[status == 1]

  vectors = []
  magnitudes = []
  for (x0, y0), (x1, y1) in zip(good_prev, good_next):
    vectors.append(((int(x0), int(y0)), (int(x1), int(y1))))
    magnitudes.append(float(np.hypot(x1 - x0, y1 - y0)))

  avg_magnitude = float(np.mean(magnitudes)) if magnitudes else 0.0
  return {
    "vectors": vectors,
    "avg_magnitude": round(avg_magnitude, 3),
    "point_count": len(vectors),
  }


def still_second_frame(original: np.ndarray, processed: np.ndarray) -> np.ndarray:
  """Build a second BGR frame for still-image LK demos (upload mode)."""
  if original.shape != processed.shape:
    processed = cv2.resize(processed, (original.shape[1], original.shape[0]))
  if not np.array_equal(original, processed):
    return processed
  h, w = original.shape[:2]
  matrix = np.float32([[1, 0, 4], [0, 1, 3]])
  return cv2.warpAffine(original, matrix, (w, h), borderMode=cv2.BORDER_REPLICATE)
