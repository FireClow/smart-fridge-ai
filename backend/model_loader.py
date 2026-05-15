"""Load YOLOv8 weights once for the FastAPI process."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from ultralytics import YOLO

_LOG_PATH = Path(__file__).resolve().parent.parent / "debug-51eb5f.log"


def _debug_log(location: str, message: str, data: dict, hypothesis_id: str) -> None:
  # #region agent log
  try:
    payload = {
      "sessionId": "51eb5f",
      "timestamp": int(time.time() * 1000),
      "location": location,
      "message": message,
      "data": data,
      "hypothesisId": hypothesis_id,
    }
    with _LOG_PATH.open("a", encoding="utf-8") as f:
      f.write(json.dumps(payload) + "\n")
  except OSError:
    pass
  # #endregion


def _project_root() -> Path:
  return Path(__file__).resolve().parent.parent


def _discover_best_pt() -> Path | None:
  """Pick newest runs/detect/train-*/weights/best.pt if configured path is missing."""
  runs = _project_root() / "runs" / "detect"
  if not runs.is_dir():
    return None
  candidates: list[Path] = []
  for train_dir in runs.iterdir():
    if not train_dir.is_dir():
      continue
    candidate = train_dir / "weights" / "best.pt"
    if candidate.is_file():
      candidates.append(candidate)
  if not candidates:
    return None
  return max(candidates, key=lambda p: p.stat().st_mtime)


def resolve_model_path() -> Path:
  raw = os.getenv("MODEL_PATH", "runs/detect/train-5/weights/best.pt")
  path = Path(raw)
  if not path.is_absolute():
    path = (_project_root() / path).resolve()

  if path.is_file():
    _debug_log(
      "model_loader.py:resolve_model_path",
      "resolved configured path",
      {"path": str(path), "exists": True},
      "B",
    )
    return path

  fallback = _discover_best_pt()
  if fallback is not None:
    _debug_log(
      "model_loader.py:resolve_model_path",
      "using discovered fallback",
      {"configured": str(path), "fallback": str(fallback)},
      "A",
    )
    return fallback.resolve()

  root_pt = _project_root() / "yolov8n.pt"
  if root_pt.is_file():
    _debug_log(
      "model_loader.py:resolve_model_path",
      "using yolov8n.pt fallback",
      {"path": str(root_pt)},
      "A",
    )
    return root_pt.resolve()

  _debug_log(
    "model_loader.py:resolve_model_path",
    "no model file found",
    {"configured": str(path)},
    "A",
  )
  return path


def load_yolo_model() -> YOLO:
  """Load YOLO from MODEL_PATH (with auto-discovery fallbacks)."""
  path = resolve_model_path()
  if not path.is_file():
    raise FileNotFoundError(
      f"Model file not found: {path}. Set MODEL_PATH in .env or train with train.py.",
    )
  try:
    model = YOLO(str(path))
    _debug_log(
      "model_loader.py:load_yolo_model",
      "YOLO loaded",
      {"path": str(path), "num_classes": len(getattr(model, "names", {}) or {})},
      "C",
    )
    return model
  except Exception as exc:
    _debug_log(
      "model_loader.py:load_yolo_model",
      "YOLO load failed",
      {"path": str(path), "error": type(exc).__name__, "detail": str(exc)[:300]},
      "C",
    )
    raise
