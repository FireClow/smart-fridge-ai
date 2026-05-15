"""Realtime webcam detection loop with Supabase inventory sync."""

from __future__ import annotations

import os
import time
from pathlib import Path

import cv2
from dotenv import load_dotenv
from ultralytics import YOLO

from database import (
  connect_to_supabase,
  get_inventory,
  insert_detection_log,
  upsert_inventory_from_detection,
)
from inventory_manager import (
  count_detected_items,
  filter_low_confidence,
  inventory_to_counts,
  prevent_duplicate_detection,
)

# Load environment variables before reading configuration values.
load_dotenv()


def _get_float_env(name: str, default: float) -> float:
  """Read a float value from the environment with a safe fallback."""
  try:
    return float(os.getenv(name, str(default)))
  except ValueError:
    return default


def _get_int_env(name: str, default: int) -> int:
  """Read an integer value from the environment with a safe fallback."""
  try:
    return int(os.getenv(name, str(default)))
  except ValueError:
    return default


def _truthy_env(name: str) -> bool:
  return os.getenv(name, "").strip().lower() in ("1", "true", "yes", "on")


def _run_supabase_smoke_test(model_path: str) -> None:
  """Connect to Supabase, read inventory, load YOLO once, then exit (no webcam)."""
  import numpy as np

  client = connect_to_supabase()
  rows = get_inventory(client)
  print(f"Supabase OK. inventory rows: {len(rows)}")
  model = load_model(model_path)
  frame = np.zeros((640, 640, 3), dtype=np.uint8)
  model(frame, verbose=False)
  print("YOLO dry-run OK. Set SKIP_WEBCAM=0 (or unset) for full webcam mode.")


def load_model(model_path: str) -> YOLO:
  """Load the YOLO model and raise a clear error when the file is missing."""
  resolved_path = Path(model_path)
  if not resolved_path.exists():
    raise FileNotFoundError(
      f"Model file not found: {resolved_path}. "
      "Check MODEL_PATH in your .env file."
    )

  return YOLO(str(resolved_path))


def open_webcam(webcam_index: int) -> cv2.VideoCapture:
  """Open the webcam using DirectShow on Windows for better compatibility."""
  capture = cv2.VideoCapture(webcam_index, cv2.CAP_DSHOW)
  if not capture.isOpened():
    capture.release()
    raise RuntimeError(
      f"Webcam not detected at index {webcam_index}. "
      "Close other camera apps and try another WEBCAM_INDEX."
    )
  return capture


def save_inventory_snapshot(
  client,
  inventory: dict[str, dict[str, float | int]],
) -> None:
  """Write the current inventory snapshot and one log row per detected item."""
  for item_name, item_data in inventory.items():
    quantity = int(item_data["count"])
    confidence = float(item_data["max_confidence"])
    upsert_inventory_from_detection(client, item_name, quantity)
    insert_detection_log(client, item_name, quantity, confidence)


def run_detection() -> None:
  """Run realtime detection, print inventory, and sync changes to Supabase."""
  model_path = os.getenv("MODEL_PATH", "runs/detect/train-5/weights/best.pt")
  confidence_threshold = _get_float_env("CONFIDENCE_THRESHOLD", 0.6)
  cooldown_seconds = _get_float_env("COOLDOWN_SECONDS", 5.0)
  print_interval_seconds = _get_float_env("PRINT_INTERVAL_SECONDS", 2.0)
  webcam_index = _get_int_env("WEBCAM_INDEX", 0)

  if _truthy_env("SKIP_WEBCAM"):
    _run_supabase_smoke_test(model_path)
    return

  model = load_model(model_path)
  supabase_client = connect_to_supabase()
  capture = open_webcam(webcam_index)

  last_print_time = 0.0
  last_saved_time = 0.0
  last_saved_inventory: dict[str, int] = {}

  print("Smart Fridge AI started. Press Q in the camera window to quit.")

  try:
    while True:
      success, frame = capture.read()
      if not success:
        print("Cannot read from webcam. Stopping detection loop.")
        break

      results = model(frame, verbose=False)

      inventory = count_detected_items(results, model, confidence_threshold)
      inventory = filter_low_confidence(inventory, confidence_threshold)

      if prevent_duplicate_detection(
        inventory,
        last_saved_inventory,
        last_saved_time,
        cooldown_seconds,
      ):
        try:
          save_inventory_snapshot(supabase_client, inventory)
          last_saved_inventory = inventory_to_counts(inventory)
          last_saved_time = time.time()
        except Exception as exc:
          print(f"Supabase save failed: {exc}")

      current_time = time.time()
      if current_time - last_print_time >= print_interval_seconds:
        counts = inventory_to_counts(inventory)
        print(f"Current Inventory: {counts}")
        try:
          stored_inventory = get_inventory(supabase_client)
          print(f"Stored Inventory: {stored_inventory}")
        except Exception as exc:
          print(f"Could not read inventory from Supabase: {exc}")
        last_print_time = current_time

      annotated_frame = results[0].plot()
      cv2.imshow("Smart Fridge Inventory", annotated_frame)

      if cv2.waitKey(1) & 0xFF == ord("q"):
        break
  finally:
    capture.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
  run_detection()
