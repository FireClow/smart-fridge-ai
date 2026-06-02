"""Course-applied module: Inventory Event Detection.

Combines three signals to classify fridge activity:
  - YOLO detection deltas (item counts changed between frames)
  - Optical flow magnitude (was there motion?)
  - Feature tracking (active tracks / movement)

Emitted events: 'added', 'removed', 'moved'.
"""

from __future__ import annotations

# Motion above this average LK magnitude (pixels) counts as "movement".
_MOTION_THRESHOLD = 2.5


def detect_events(
  prev_counts: dict[str, int],
  curr_counts: dict[str, int],
  avg_motion: float,
) -> list[dict]:
  """Compare detection counts + motion and return a list of events.

  Each event: {"item_name", "event_type", "magnitude"}.
  """
  events: list[dict] = []
  names = set(prev_counts) | set(curr_counts)

  for name in names:
    before = int(prev_counts.get(name, 0))
    after = int(curr_counts.get(name, 0))
    delta = after - before

    if delta > 0:
      events.append({"item_name": name, "event_type": "added", "magnitude": float(delta)})
    elif delta < 0:
      events.append({"item_name": name, "event_type": "removed", "magnitude": float(-delta)})
    elif after > 0 and avg_motion >= _MOTION_THRESHOLD:
      # Same count but significant motion -> item rearranged/moved.
      events.append({"item_name": name, "event_type": "moved", "magnitude": round(avg_motion, 2)})

  return events
