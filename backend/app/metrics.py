"""In-memory inference metrics for dashboard FPS display."""

from __future__ import annotations

from collections import deque
from threading import Lock

_MAX_SAMPLES = 30
_samples: deque[float] = deque(maxlen=_MAX_SAMPLES)
_lock = Lock()


def record_inference_seconds(elapsed: float) -> None:
  if elapsed <= 0:
    return
  with _lock:
    _samples.append(elapsed)


def average_fps() -> float | None:
  with _lock:
    if not _samples:
      return None
    avg_elapsed = sum(_samples) / len(_samples)
  if avg_elapsed <= 0:
    return None
  return round(1.0 / avg_elapsed, 2)


def last_fps() -> float | None:
  with _lock:
    if not _samples:
      return None
    elapsed = _samples[-1]
  if elapsed <= 0:
    return None
  return round(1.0 / elapsed, 2)
