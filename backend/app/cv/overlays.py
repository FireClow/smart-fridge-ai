"""Drawing + base64-encode helpers for CV visualizations.

Mirrors the JPEG/base64 approach used by `_encode_preview` in
backend/app/services/scan_service.py so the frontend can render overlays as
<img src="data:image/jpeg;base64,...">.
"""

from __future__ import annotations

import base64

import cv2
import numpy as np


def encode_jpeg_base64(image: np.ndarray, quality: int = 82) -> str | None:
  ok, encoded = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
  if not ok:
    return None
  return base64.b64encode(encoded.tobytes()).decode("ascii")


def draw_corners(
  image: np.ndarray,
  points: list[tuple[int, int]],
  color: tuple[int, int, int],
  radius: int = 3,
) -> np.ndarray:
  out = image.copy()
  for x, y in points:
    cv2.circle(out, (int(x), int(y)), radius, color, 1, lineType=cv2.LINE_AA)
  return out


def draw_corner_comparison(
  image: np.ndarray,
  harris: list[tuple[int, int]],
  shi_tomasi: list[tuple[int, int]],
) -> np.ndarray:
  """Harris in red, Shi-Tomasi in green, for the comparison panel."""
  out = draw_corners(image, harris, (0, 0, 255), radius=4)
  out = draw_corners(out, shi_tomasi, (0, 255, 0), radius=2)
  return out


def draw_keypoints(image: np.ndarray, keypoints) -> np.ndarray:
  """Rich ORB keypoint drawing (size + orientation)."""
  return cv2.drawKeypoints(
    image, keypoints, None, color=(0, 255, 255),
    flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS,
  )


def draw_flow_vectors(
  image: np.ndarray,
  vectors: list[tuple[tuple[int, int], tuple[int, int]]],
) -> np.ndarray:
  out = image.copy()
  for (x0, y0), (x1, y1) in vectors:
    cv2.arrowedLine(out, (x0, y0), (x1, y1), (0, 200, 255), 1, tipLength=0.3)
    cv2.circle(out, (x1, y1), 2, (0, 0, 255), -1)
  return out


def draw_tracks(image: np.ndarray, tracks: list[dict]) -> np.ndarray:
  """Trajectory polylines + track IDs at the latest point."""
  out = image.copy()
  for track in tracks:
    pts = track.get("points", [])
    if len(pts) >= 2:
      cv2.polylines(
        out, [np.int32(pts)], isClosed=False, color=(0, 255, 0), thickness=1,
        lineType=cv2.LINE_AA,
      )
    if pts:
      x, y = pts[-1]
      cv2.circle(out, (int(x), int(y)), 2, (0, 0, 255), -1)
      cv2.putText(
        out, str(track.get("id")), (int(x) + 3, int(y) - 3),
        cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 0), 1, cv2.LINE_AA,
      )
  return out
