"""In-memory per-session state for frame-sequence CV features.

Optical flow, tracking, and event detection need consecutive frames. We keep a
small, thread-safe buffer keyed by a session key (the logged-in user_id, or an
X-CV-Session header for anonymous demo use). State resets on server restart by
design - no database churn.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Any

import numpy as np

from backend.app.cv.tracking import FeatureTracker

_MAX_SESSIONS = 64
_SESSION_TTL_SECONDS = 60 * 30


@dataclass
class SessionState:
  prev_gray: np.ndarray | None = None
  tracker: FeatureTracker = field(default_factory=FeatureTracker)
  last_detections: dict[str, int] = field(default_factory=dict)
  last_metrics: dict[str, Any] = field(default_factory=dict)
  updated_at: float = field(default_factory=time.time)


_sessions: dict[str, SessionState] = {}
_lock = Lock()


def _evict_locked() -> None:
  now = time.time()
  stale = [k for k, s in _sessions.items() if now - s.updated_at > _SESSION_TTL_SECONDS]
  for k in stale:
    _sessions.pop(k, None)
  # Hard cap: drop the oldest if we are still over the limit.
  while len(_sessions) > _MAX_SESSIONS:
    oldest = min(_sessions.items(), key=lambda kv: kv[1].updated_at)[0]
    _sessions.pop(oldest, None)


def get_session(key: str | None) -> SessionState:
  """Return (creating if needed) the state for a session key."""
  safe_key = key or "anonymous"
  with _lock:
    state = _sessions.get(safe_key)
    if state is None:
      _evict_locked()
      state = SessionState()
      _sessions[safe_key] = state
    state.updated_at = time.time()
    return state


def reset_session(key: str | None) -> None:
  with _lock:
    _sessions.pop(key or "anonymous", None)
