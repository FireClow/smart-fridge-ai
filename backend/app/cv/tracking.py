"""Course topic: Feature-Based Tracking (Shi-Tomasi + Lucas-Kanade).

A lightweight multi-frame tracker. Shi-Tomasi seeds new corners, Lucas-Kanade
propagates them across frames, and each surviving point keeps a short
trajectory and a stable track ID. Designed to be stored per session.
"""

from __future__ import annotations

import cv2
import numpy as np

from backend.app.cv.optical_flow import to_gray

_LK_PARAMS = dict(
  winSize=(15, 15),
  maxLevel=2,
  criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03),
)

_FEATURE_PARAMS = dict(
  maxCorners=80,
  qualityLevel=0.01,
  minDistance=10,
  blockSize=7,
)

_MAX_TRAJECTORY = 20
_RESEED_BELOW = 20


class FeatureTracker:
  """Shi-Tomasi + LK tracker that maintains trajectories and track IDs."""

  def __init__(self) -> None:
    self.prev_gray: np.ndarray | None = None
    # Each track: {"id": int, "points": [(x, y), ...]}
    self.tracks: list[dict] = []
    self._next_id = 0

  def _seed(self, gray: np.ndarray) -> None:
    corners = cv2.goodFeaturesToTrack(gray, mask=None, **_FEATURE_PARAMS)
    if corners is None:
      return
    for pt in corners.reshape(-1, 2):
      self.tracks.append({"id": self._next_id, "points": [(float(pt[0]), float(pt[1]))]})
      self._next_id += 1

  def update(self, image: np.ndarray) -> dict:
    """Advance the tracker by one frame and return trajectory data."""
    gray = to_gray(image)
    if not gray.flags["C_CONTIGUOUS"]:
      gray = np.ascontiguousarray(gray)

    if self.prev_gray is None or not self.tracks:
      self.prev_gray = gray
      self.tracks = []
      self._seed(gray)
      return self._summary()

    if gray.shape != self.prev_gray.shape:
      gray = cv2.resize(gray, (self.prev_gray.shape[1], self.prev_gray.shape[0]))

    prev_pts = np.float32([t["points"][-1] for t in self.tracks]).reshape(-1, 1, 2)
    if prev_pts.size == 0:
      self.prev_gray = gray
      self._seed(gray)
      return self._summary()

    next_pts, status, _err = cv2.calcOpticalFlowPyrLK(
      self.prev_gray, gray, prev_pts, None, **_LK_PARAMS
    )

    surviving: list[dict] = []
    if next_pts is not None and status is not None:
      status = status.reshape(-1)
      for track, (x, y), ok in zip(self.tracks, next_pts.reshape(-1, 2), status):
        if not ok:
          continue
        track["points"].append((float(x), float(y)))
        if len(track["points"]) > _MAX_TRAJECTORY:
          track["points"] = track["points"][-_MAX_TRAJECTORY:]
        surviving.append(track)

    self.tracks = surviving
    self.prev_gray = gray

    # Re-seed when too few tracks remain so the demo stays lively.
    if len(self.tracks) < _RESEED_BELOW:
      self._seed(gray)

    return self._summary()

  def _summary(self) -> dict:
    return {
      "active_tracks": len(self.tracks),
      "tracks": [
        {"id": t["id"], "points": [(int(x), int(y)) for x, y in t["points"]]}
        for t in self.tracks
      ],
    }


def track_still_pair(first: np.ndarray, second: np.ndarray) -> dict:
  """Two-step tracking demo for a single uploaded image (frame A → frame B)."""
  if first.shape != second.shape:
    second = cv2.resize(second, (first.shape[1], first.shape[0]))
  tracker = FeatureTracker()
  tracker.update(first)
  return tracker.update(second)
