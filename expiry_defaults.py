"""Default shelf-life estimates (days) for YOLO class names."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

_CACHE: dict[str, int] | None = None


def _load_map() -> dict[str, int]:
  global _CACHE
  if _CACHE is not None:
    return _CACHE
  path = Path(__file__).resolve().parent / "shelf_life_days.json"
  with path.open(encoding="utf-8") as handle:
    raw = json.load(handle)
  _CACHE = {str(k).lower(): int(v) for k, v in raw.items()}
  return _CACHE


def shelf_life_days_for_item(item_name: str) -> int:
  """Return default fridge shelf life in days for a class name."""
  key = (item_name or "").strip().lower()
  table = _load_map()
  if key in table:
    return table[key]
  return int(table.get("__default__", 5))


def estimated_expires_at_utc(item_name: str) -> datetime:
  """UTC instant = now + default shelf life for this item."""
  days = shelf_life_days_for_item(item_name)
  return datetime.now(timezone.utc) + timedelta(days=days)
