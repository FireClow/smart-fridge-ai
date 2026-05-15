"""Detection logs and aggregate stats."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from statistics import mean
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from backend.app.auth.deps import get_current_user_id
from backend.app.metrics import average_fps
from backend.schemas import DetectionLog, Stats
from database import connect_to_supabase, get_detection_logs, get_inventory

router = APIRouter(prefix="/logs", tags=["logs"])
stats_router = APIRouter(tags=["stats"])


def _parse_expires_at(value: object) -> datetime | None:
  if value is None:
    return None
  if isinstance(value, datetime):
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
  text = str(value).replace("Z", "+00:00")
  parsed = datetime.fromisoformat(text)
  if parsed.tzinfo is None:
    return parsed.replace(tzinfo=timezone.utc)
  return parsed.astimezone(timezone.utc)


def get_supabase():
  try:
    return connect_to_supabase()
  except (ValueError, ConnectionError) as exc:
    raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("", response_model=list[DetectionLog])
def list_logs(
  limit: int = 20,
  client=Depends(get_supabase),
  user_id: Annotated[str | None, Depends(get_current_user_id)] = None,
) -> list[dict]:
  return get_detection_logs(client, limit=min(max(limit, 1), 100), user_id=user_id)


@stats_router.get("/stats", response_model=Stats)
def get_stats(
  client=Depends(get_supabase),
  user_id: Annotated[str | None, Depends(get_current_user_id)] = None,
) -> Stats:
  inv = get_inventory(client, user_id=user_id)
  logs = get_detection_logs(client, limit=500, user_id=user_id)

  total_items = sum(int(r.get("quantity", 0)) for r in inv)
  total_categories = len(inv)

  confidences = [float(r["confidence"]) for r in logs if r.get("confidence") is not None]
  avg_confidence = mean(confidences) if confidences else None

  last_detected = None
  for row in logs:
    dt = row.get("detected_at")
    if dt is not None:
      last_detected = dt
      break

  now = datetime.now(timezone.utc)
  soon = now + timedelta(days=3)
  expiring_soon_count = 0
  for row in inv:
    exp = _parse_expires_at(row.get("expires_at"))
    if exp is None:
      continue
    if now <= exp <= soon:
      expiring_soon_count += 1

  return Stats(
    total_items=total_items,
    total_categories=total_categories,
    avg_confidence=avg_confidence,
    last_detected=last_detected,
    fps_hint=average_fps(),
    expiring_soon_count=expiring_soon_count,
  )
