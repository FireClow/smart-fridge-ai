"""Inventory counting and duplicate-prevention helpers."""

from __future__ import annotations

import time
from typing import Any


def count_detected_items(
  results: Any,
  model: Any,
  conf_threshold: float,
) -> dict[str, dict[str, float | int]]:
  """Count detected items and keep the highest confidence per item name."""
  inventory: dict[str, dict[str, float | int]] = {}

  if not results or results[0].boxes is None:
    return inventory

  for box in results[0].boxes:
    confidence = float(box.conf[0])
    if confidence < conf_threshold:
      continue

    class_id = int(box.cls[0])
    item_name = model.names[class_id]

    if item_name not in inventory:
      inventory[item_name] = {"count": 1, "max_confidence": confidence}
      continue

    inventory[item_name]["count"] = int(inventory[item_name]["count"]) + 1
    inventory[item_name]["max_confidence"] = max(
      float(inventory[item_name]["max_confidence"]),
      confidence,
    )

  return inventory


def filter_low_confidence(
  inventory: dict[str, dict[str, float | int]],
  threshold: float,
) -> dict[str, dict[str, float | int]]:
  """Remove items whose highest confidence is still below the threshold."""
  return {
    item_name: item_data
    for item_name, item_data in inventory.items()
    if float(item_data["max_confidence"]) >= threshold
  }


def is_cooldown_over(last_saved_time: float, cooldown_seconds: float) -> bool:
  """Return True when enough time has passed since the last database write."""
  if last_saved_time <= 0:
    return True
  return (time.time() - last_saved_time) >= cooldown_seconds


def items_changed(
  current_inventory: dict[str, dict[str, float | int]],
  last_saved_inventory: dict[str, int],
) -> bool:
  """Return True when item names or quantities changed since the last save."""
  current_counts = {
    item_name: int(item_data["count"])
    for item_name, item_data in current_inventory.items()
  }
  return current_counts != last_saved_inventory


def prevent_duplicate_detection(
  current_inventory: dict[str, dict[str, float | int]],
  last_saved_inventory: dict[str, int],
  last_saved_time: float,
  cooldown_seconds: float,
) -> bool:
  """Allow a database write only when inventory changed and cooldown expired."""
  if not items_changed(current_inventory, last_saved_inventory):
    return False
  return is_cooldown_over(last_saved_time, cooldown_seconds)


def inventory_to_counts(
  inventory: dict[str, dict[str, float | int]],
) -> dict[str, int]:
  """Convert the internal inventory structure to simple name -> quantity."""
  return {
    item_name: int(item_data["count"])
    for item_name, item_data in inventory.items()
  }
