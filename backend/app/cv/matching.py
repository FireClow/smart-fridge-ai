"""Course topic: Feature Matching (Brute-Force matcher, Hamming distance).

ORB produces binary descriptors, so the natural distance is Hamming. We use a
KNN match + Lowe's ratio test to keep only confident correspondences, then
report a simple match score for the UI.
"""

from __future__ import annotations

import cv2
import numpy as np

from backend.app.cv.orb_features import extract_orb

_RATIO = 0.75


def match_descriptors(desc1: np.ndarray | None, desc2: np.ndarray | None):
  """KNN BFMatcher (Hamming) + Lowe ratio test -> list of good DMatch."""
  if desc1 is None or desc2 is None or len(desc1) == 0 or len(desc2) == 0:
    return []
  bf = cv2.BFMatcher(cv2.NORM_HAMMING)
  raw = bf.knnMatch(desc1, desc2, k=2)
  good = []
  for pair in raw:
    if len(pair) < 2:
      continue
    m, n = pair
    if m.distance < _RATIO * n.distance:
      good.append(m)
  return good


def match_images(reference: np.ndarray, current: np.ndarray) -> dict:
  """Match a reference image against the current detection crop.

  Returns keypoints, good matches, and a 0-1 match score (good matches over
  the smaller keypoint set).
  """
  kp_ref, desc_ref = extract_orb(reference)
  kp_cur, desc_cur = extract_orb(current)
  good = match_descriptors(desc_ref, desc_cur)

  denom = max(1, min(len(kp_ref), len(kp_cur)))
  score = round(len(good) / denom, 3)

  match_image = cv2.drawMatches(
    reference, kp_ref, current, kp_cur, good[:40], None,
    flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS,
  )
  return {
    "kp_ref": kp_ref,
    "kp_cur": kp_cur,
    "good_matches": good,
    "match_count": len(good),
    "ref_keypoints": len(kp_ref),
    "cur_keypoints": len(kp_cur),
    "match_score": score,
    "match_image": match_image,
  }
