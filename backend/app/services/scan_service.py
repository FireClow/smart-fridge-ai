"""YOLO scan pipeline with validation, timing, and safe DB writes."""

from __future__ import annotations

import asyncio
import base64
import os
from time import perf_counter
from typing import Any

import cv2
import numpy as np
from fastapi import HTTPException
from supabase import Client

from backend.app.metrics import last_fps, record_inference_seconds
from backend.app.services.expiration_service import generate_notifications
from database import connect_to_supabase, insert_detection_log, upsert_inventory_from_detection
from inventory_manager import count_detected_items, filter_low_confidence

_MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(5 * 1024 * 1024)))
_ALLOWED_CONTENT_TYPES = frozenset(
  {"image/jpeg", "image/jpg", "image/png", "image/pjpeg", "application/octet-stream"}
)


def _decode_image(raw: bytes) -> np.ndarray:
  if len(raw) > _MAX_UPLOAD_BYTES:
    raise HTTPException(
      status_code=413,
      detail=f"Image too large (max {_MAX_UPLOAD_BYTES // (1024 * 1024)} MB).",
    )
  if not raw:
    raise HTTPException(status_code=400, detail="Empty file body.")

  buffer = np.frombuffer(raw, dtype=np.uint8)
  image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
  if image is None:
    raise HTTPException(status_code=400, detail="Could not decode image (use JPEG or PNG).")
  return image


def _run_yolo(model, image: np.ndarray, confidence: float) -> tuple[Any, dict]:
  t0 = perf_counter()
  try:
    results = model(image, verbose=False)
  except Exception as exc:
    raise HTTPException(
      status_code=500,
      detail=f"YOLO inference failed: {exc}",
    ) from exc
  elapsed = perf_counter() - t0
  record_inference_seconds(elapsed)

  inventory = count_detected_items(results, model, confidence)
  inventory = filter_low_confidence(inventory, confidence)
  return results, inventory


def _encode_preview(results) -> str | None:
  annotated = results[0].plot()
  ok, encoded = cv2.imencode(".jpg", annotated, [int(cv2.IMWRITE_JPEG_QUALITY), 82])
  if not ok:
    return None
  return base64.b64encode(encoded.tobytes()).decode("ascii")


def _persist_detections(
  client: Client,
  inventory: dict,
  user_id: str | None,
) -> list[dict[str, Any]]:
  items: list[dict[str, Any]] = []
  for item_name, item_data in inventory.items():
    quantity = int(item_data["count"])
    conf_val = float(item_data["max_confidence"])
    try:
      row = upsert_inventory_from_detection(
        client, item_name, quantity, user_id=user_id
      )
      insert_detection_log(client, item_name, quantity, conf_val, user_id=user_id)
    except Exception as exc:
      detail = str(exc)
      if "expires_at" in detail and "does not exist" in detail:
        detail = (
          f"{detail} — Run supabase_migration_inventory_expiry.sql in Supabase "
          "SQL Editor (adds inventory.expires_at / expiry_locked), then retry scan."
        )
      elif "user_id" in detail and "does not exist" in detail:
        detail = (
          f"{detail} — Run supabase_migration_multi_user.sql, or scan without logging in."
        )
      raise HTTPException(
        status_code=502,
        detail=f"Database write failed: {detail}",
      ) from exc
    items.append(
      {
        "item_name": item_name,
        "quantity": quantity,
        "confidence": conf_val,
        "expires_at": row.get("expires_at"),
        "expiry_locked": row.get("expiry_locked"),
      }
    )
  return items


async def process_scan(
  *,
  raw: bytes,
  content_type: str | None,
  confidence: float,
  model,
  user_id: str | None = None,
) -> dict[str, Any]:
  if content_type and content_type.split(";")[0].strip().lower() not in _ALLOWED_CONTENT_TYPES:
    raise HTTPException(
      status_code=400,
      detail=f"Unsupported content type: {content_type}. Use JPEG or PNG.",
    )

  image = _decode_image(raw)

  results, inventory = await asyncio.to_thread(_run_yolo, model, image, confidence)

  try:
    client = connect_to_supabase()
  except ValueError as exc:
    raise HTTPException(status_code=503, detail=str(exc)) from exc
  except ConnectionError as exc:
    raise HTTPException(status_code=503, detail=str(exc)) from exc

  items = _persist_detections(client, inventory, user_id)

  try:
    generate_notifications(client, user_id)
  except Exception:
    pass

  fps_val = last_fps() or 0.0
  inference_ms = round(1000.0 / fps_val, 2) if fps_val > 0 else 0.0
  fps = fps_val
  preview = _encode_preview(results)

  return {
    "items": items,
    "annotated_image_base64": preview,
    "inference_ms": inference_ms,
    "fps": fps,
    "detected_count": len(items),
  }
