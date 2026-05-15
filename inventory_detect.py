"""Standalone detection prototype (no Supabase integration).

Useful for quickly testing the trained YOLOv8 model with a webcam.
For the full pipeline with database sync, use app.py instead.
"""

from __future__ import annotations

import time

import cv2
from ultralytics import YOLO

MODEL_PATH = "runs/detect/train-5/weights/best.pt"
CONFIDENCE_THRESHOLD = 0.6
PRINT_INTERVAL_SECONDS = 2.0
WEBCAM_INDEX = 0


def main() -> None:
  model = YOLO(MODEL_PATH)
  cap = cv2.VideoCapture(WEBCAM_INDEX, cv2.CAP_DSHOW)

  if not cap.isOpened():
    print(f"Could not open webcam at index {WEBCAM_INDEX}.")
    return

  last_print_time = 0.0

  try:
    while True:
      success, frame = cap.read()
      if not success:
        print("Cannot access camera.")
        break

      results = model(frame, verbose=False)
      inventory: dict[str, int] = {}

      for box in results[0].boxes:
        confidence = float(box.conf[0])
        if confidence < CONFIDENCE_THRESHOLD:
          continue
        item_name = model.names[int(box.cls[0])]
        inventory[item_name] = inventory.get(item_name, 0) + 1

      current_time = time.time()
      if current_time - last_print_time >= PRINT_INTERVAL_SECONDS:
        print("Inventory:", inventory)
        last_print_time = current_time

      cv2.imshow("Smart Fridge — Prototype", results[0].plot())
      if cv2.waitKey(1) == ord("q"):
        break
  finally:
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
  main()
