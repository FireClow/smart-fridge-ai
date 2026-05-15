"""YOLOv8 training script for Smart Fridge food detection."""

from __future__ import annotations

from ultralytics import YOLO


def main() -> None:
  model = YOLO("yolov8n.pt")
  model.train(
    data="dataset_2/data.yaml",
    epochs=30,
    imgsz=640,
  )


if __name__ == "__main__":
  main()
