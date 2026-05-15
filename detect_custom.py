"""Minimal detection script without inventory logic or Supabase.

Used for quick model sanity checks. For the full pipeline, use app.py.
"""

from __future__ import annotations

import cv2
from ultralytics import YOLO

MODEL_PATH = "runs/detect/train-5/weights/best.pt"
WEBCAM_INDEX = 0


def main() -> None:
  model = YOLO(MODEL_PATH)
  cap = cv2.VideoCapture(WEBCAM_INDEX)

  if not cap.isOpened():
    print(f"Could not open webcam at index {WEBCAM_INDEX}.")
    return

  try:
    while True:
      success, frame = cap.read()
      if not success:
        break

      results = model(frame)
      cv2.imshow("Smart Fridge AI", results[0].plot())
      if cv2.waitKey(1) == ord("q"):
        break
  finally:
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
  main()
