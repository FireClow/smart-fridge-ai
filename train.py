"""YOLOv8 training script for Smart Fridge food detection.

Lihat docs/PANDUAN_TRAINING.md untuk meningkatkan akurasi (data, model, epoch, imgsz).
"""

from __future__ import annotations

import argparse

from ultralytics import YOLO


def main() -> None:
  parser = argparse.ArgumentParser(description="Train YOLOv8 on Smart Fridge dataset")
  parser.add_argument(
    "--data",
    default="dataset_2/data.yaml",
    help="Path to data.yaml (Ultralytics format)",
  )
  parser.add_argument(
    "--model",
    default="yolov8n.pt",
    help="Starting weights: yolov8n.pt, yolov8s.pt, yolov8m.pt, ... (larger = often more accurate, slower)",
  )
  parser.add_argument("--epochs", type=int, default=30, help="Max training epochs")
  parser.add_argument("--imgsz", type=int, default=640, help="Train image size (e.g. 640, 768, 1024)")
  parser.add_argument(
    "--batch",
    type=int,
    default=-1,
    help="Batch size (-1 = auto). Lower if CUDA OOM",
  )
  parser.add_argument(
    "--patience",
    type=int,
    default=0,
    help="Early stopping patience (0 = disabled). Try 20–50 with epochs 80+",
  )
  parser.add_argument(
    "--device",
    default=None,
    help="cuda, cpu, or 0,1,... (default: Ultralytics auto)",
  )
  parser.add_argument(
    "--name",
    default=None,
    help="Run name under runs/detect/ (default: Ultralytics auto)",
  )
  args = parser.parse_args()

  model = YOLO(args.model)
  train_kw: dict = {
    "data": args.data,
    "epochs": args.epochs,
    "imgsz": args.imgsz,
  }
  if args.batch > 0:
    train_kw["batch"] = args.batch
  if args.patience > 0:
    train_kw["patience"] = args.patience
  if args.device:
    train_kw["device"] = args.device
  if args.name:
    train_kw["name"] = args.name

  model.train(**train_kw)


if __name__ == "__main__":
  main()
