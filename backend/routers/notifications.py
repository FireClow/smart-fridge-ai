"""Expiration notification endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from backend.app.auth.deps import get_current_user_id
from backend.app.services.expiration_service import generate_notifications
from backend.schemas import ExpirationNotification
from database import connect_to_supabase, get_notifications, mark_notification_read

router = APIRouter(prefix="/notifications", tags=["notifications"])


def get_supabase():
  return connect_to_supabase()


@router.get("", response_model=list[ExpirationNotification])
def list_notifications(
  unread_only: bool = False,
  limit: int = 50,
  client=Depends(get_supabase),
  user_id: Annotated[str | None, Depends(get_current_user_id)] = None,
) -> list[dict]:
  return get_notifications(
    client, limit=min(max(limit, 1), 100), unread_only=unread_only, user_id=user_id
  )


@router.post("/generate")
def run_generate(
  client=Depends(get_supabase),
  user_id: Annotated[str | None, Depends(get_current_user_id)] = None,
) -> dict:
  try:
    created = generate_notifications(client, user_id)
    return {"created": len(created), "notifications": created}
  except Exception as exc:
    raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.patch("/{notification_id}/read", response_model=ExpirationNotification)
def mark_read(
  notification_id: int,
  client=Depends(get_supabase),
  user_id: Annotated[str | None, Depends(get_current_user_id)] = None,
) -> dict:
  row = mark_notification_read(client, notification_id, user_id=user_id)
  if not row:
    raise HTTPException(status_code=404, detail="Notification not found.")
  return row
