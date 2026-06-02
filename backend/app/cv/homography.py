"""Course topic: Homography estimation (findHomography + RANSAC) and warp.

Given ORB matches between a reference and the current view, estimate the
planar homography with RANSAC, split inlier/outlier matches, and optionally
warp the current view to a frontal (reference) perspective.
"""

from __future__ import annotations

import cv2
import numpy as np

from backend.app.cv.matching import match_images

_MIN_MATCHES = 4


def estimate_homography(reference: np.ndarray, current: np.ndarray) -> dict:
  """Estimate homography from ORB matches and return inlier/outlier info."""
  result = match_images(reference, current)
  kp_ref = result["kp_ref"]
  kp_cur = result["kp_cur"]
  good = result["good_matches"]

  if len(good) < _MIN_MATCHES:
    return {
      "homography": None,
      "inliers": 0,
      "outliers": len(good),
      "match_count": len(good),
      "match_score": result["match_score"],
      "warped": None,
      "vis": result["match_image"],
    }

  src_pts = np.float32([kp_ref[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
  dst_pts = np.float32([kp_cur[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

  homography, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
  mask = mask.reshape(-1) if mask is not None else np.zeros(len(good), dtype=np.uint8)
  inliers = int(mask.sum())
  outliers = int(len(good) - inliers)

  # Inlier matches drawn green, outliers red (matchesMask filters inliers).
  vis = cv2.drawMatches(
    reference, kp_ref, current, kp_cur, good, None,
    matchColor=(0, 255, 0), singlePointColor=(0, 0, 255),
    matchesMask=mask.tolist(), flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS,
  )

  # Perspective correction: warp current view back onto the reference plane.
  warped = None
  if homography is not None:
    inv = np.linalg.inv(homography)
    h, w = reference.shape[:2]
    warped = cv2.warpPerspective(current, inv, (w, h))

  return {
    "homography": homography.tolist() if homography is not None else None,
    "inliers": inliers,
    "outliers": outliers,
    "match_count": len(good),
    "match_score": result["match_score"],
    "warped": warped,
    "vis": vis,
  }
