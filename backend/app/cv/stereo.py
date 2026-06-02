"""Course topics (bonus): Stereo Vision & 3D Reconstruction.

DEMONSTRATION ONLY. The fridge uses a single (monocular) camera, so this module
simulates a stereo pair from two horizontally-offset frames of the same scene
(e.g. two captures while the camera/object shifts slightly). It computes a
disparity map with StereoBM and an illustrative 3D point cloud via
reprojectImageTo3D. This is meant to show the concepts, not to produce
metrically-accurate depth (which would require a calibrated stereo rig).
"""

from __future__ import annotations

import cv2
import numpy as np


def _to_gray(image: np.ndarray) -> np.ndarray:
  if image.ndim == 2:
    return image
  return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def compute_disparity(left: np.ndarray, right: np.ndarray) -> np.ndarray:
  """Block-matching disparity between a (simulated) stereo pair.

  num_disparities must be divisible by 16; block_size must be odd.
  """
  left_gray = _to_gray(left)
  right_gray = _to_gray(right)
  if left_gray.shape != right_gray.shape:
    right_gray = cv2.resize(right_gray, (left_gray.shape[1], left_gray.shape[0]))

  stereo = cv2.StereoBM_create(numDisparities=64, blockSize=15)
  disparity = stereo.compute(left_gray, right_gray).astype(np.float32) / 16.0
  return disparity


def disparity_colormap(disparity: np.ndarray) -> np.ndarray:
  """Normalize + colorize a disparity map for visualization."""
  norm = cv2.normalize(disparity, None, 0, 255, cv2.NORM_MINMAX)
  norm = norm.astype(np.uint8)
  return cv2.applyColorMap(norm, cv2.COLORMAP_JET)


def reconstruct_3d(disparity: np.ndarray, focal_length: float = 0.8) -> np.ndarray:
  """Illustrative 3D reconstruction via reprojectImageTo3D.

  Uses a generic Q matrix (no real calibration) so the output shows relative
  structure rather than true metric depth.
  """
  h, w = disparity.shape[:2]
  f = focal_length * w
  cx, cy = w / 2.0, h / 2.0
  # Generic reprojection matrix (assumes unit baseline, uncalibrated).
  q = np.float32([
    [1, 0, 0, -cx],
    [0, -1, 0, cy],
    [0, 0, 0, f],
    [0, 0, 1, 0],
  ])
  return cv2.reprojectImageTo3D(disparity, q)


def stereo_demo(left: np.ndarray, right: np.ndarray) -> dict:
  """Run the full demo and return disparity + a colorized visualization."""
  disparity = compute_disparity(left, right)
  vis = disparity_colormap(disparity)
  points_3d = reconstruct_3d(disparity)
  valid = np.isfinite(points_3d).all(axis=2) & (disparity > disparity.min())
  return {
    "disparity": disparity,
    "disparity_vis": vis,
    "points_3d": points_3d,
    "valid_points": int(valid.sum()),
  }
