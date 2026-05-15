"""Inventory REST endpoints."""

from __future__ import annotations

from typing import Annotated
from urllib.parse import unquote

from fastapi import APIRouter, Depends, HTTPException

from backend.app.auth.deps import get_current_user_id
from backend.app.services.expiration_service import generate_notifications
from backend.schemas import InventoryExpiryPatch, InventoryItem
from database import connect_to_supabase, get_inventory, update_inventory_expiry

router = APIRouter(prefix="/inventory", tags=["inventory"])


def get_supabase():
  try:
    return connect_to_supabase()
  except (ValueError, ConnectionError) as exc:
    raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("", response_model=list[InventoryItem])
def list_inventory(
  client=Depends(get_supabase),
  user_id: Annotated[str | None, Depends(get_current_user_id)] = None,
) -> list[dict]:
  return get_inventory(client, user_id=user_id)


@router.patch("/{item_name}", response_model=InventoryItem)
def patch_inventory(
  item_name: str,
  body: InventoryExpiryPatch,
  client=Depends(get_supabase),
  user_id: Annotated[str | None, Depends(get_current_user_id)] = None,
) -> dict:
  decoded = unquote(item_name)
  if body.expires_at is None and body.expiry_locked is None:
    raise HTTPException(
      status_code=400,
      detail="Provide at least one of expires_at or expiry_locked.",
    )

  existing = [
    r for r in get_inventory(client, user_id=user_id) if r.get("item_name") == decoded
  ]
  if not existing:
    raise HTTPException(status_code=404, detail="Inventory item not found.")

  row = update_inventory_expiry(
    client,
    decoded,
    expires_at=body.expires_at,
    expiry_locked=body.expiry_locked,
    user_id=user_id,
  )
  if row:
    try:
      generate_notifications(client, user_id)
    except Exception:
      pass
    return row

  refreshed = [
    r for r in get_inventory(client, user_id=user_id) if r.get("item_name") == decoded
  ]
  if not refreshed:
    raise HTTPException(status_code=404, detail="Inventory item not found.")
  return refreshed[0]
