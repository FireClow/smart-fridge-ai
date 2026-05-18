"""Supabase database helpers for Smart Fridge AI."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv
from supabase import Client, create_client

from expiry_defaults import estimated_expires_at_utc

load_dotenv()

_PLACEHOLDER_URL = "https://your-project.supabase.co"
_PLACEHOLDER_KEY = "your-anon-or-service-role-key"


def _normalize_supabase_url(url: str) -> str:
  u = url.strip().rstrip("/")
  suffix = "/rest/v1"
  if u.endswith(suffix):
    return u[: -len(suffix)]
  return u


def _clear_invalid_ssl_bundle_env() -> None:
  for key in ("SSL_CERT_FILE", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE"):
    path = os.environ.get(key, "").strip()
    if path and not os.path.isfile(path):
      os.environ.pop(key, None)


def connect_to_supabase() -> Client:
  """Create Supabase client (service role or anon key from .env)."""
  _clear_invalid_ssl_bundle_env()
  supabase_url = _normalize_supabase_url(os.getenv("SUPABASE_URL", ""))
  supabase_key = (
    os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    or os.getenv("SUPABASE_KEY", "").strip()
  )

  if not supabase_url or not supabase_key:
    raise ValueError(
      "SUPABASE_URL and SUPABASE_KEY (or SUPABASE_SERVICE_ROLE_KEY) must be set in .env."
    )

  if supabase_url == _PLACEHOLDER_URL or supabase_key == _PLACEHOLDER_KEY:
    raise ValueError(
      "Replace placeholder SUPABASE_URL / SUPABASE_KEY in .env with your project values."
    )

  try:
    return create_client(supabase_url, supabase_key)
  except Exception as exc:
    raise ConnectionError(f"Failed to connect to Supabase: {exc}") from exc


def _first_row(response) -> dict[str, Any]:
  rows = response.data or []
  return rows[0] if rows else {}


_INVENTORY_COLUMNS = "id, item_name, quantity, updated_at, expires_at, expiry_locked"
_DETECTION_LOG_COLUMNS = "id, item_name, quantity, confidence, detected_at"


def _inventory_query(client: Client, user_id: str | None):
  columns = _INVENTORY_COLUMNS
  if user_id:
    columns = f"{_INVENTORY_COLUMNS}, user_id"
  q = client.table("inventory").select(columns)
  if user_id:
    q = q.eq("user_id", user_id)
  return q


def _inventory_row_by_name(
  client: Client, item_name: str, user_id: str | None = None
) -> dict[str, Any] | None:
  q = _inventory_query(client, user_id).eq("item_name", item_name).limit(1)
  rows = q.execute().data or []
  return rows[0] if rows else None


def insert_inventory(
  client: Client,
  item_name: str,
  quantity: int,
  user_id: str | None = None,
) -> dict[str, Any]:
  now = datetime.now(timezone.utc).isoformat()
  expires_at = estimated_expires_at_utc(item_name).isoformat()
  payload: dict[str, Any] = {
    "item_name": item_name,
    "quantity": quantity,
    "updated_at": now,
    "expires_at": expires_at,
    "expiry_locked": False,
  }
  if user_id:
    payload["user_id"] = user_id
  response = client.table("inventory").insert(payload).execute()
  return _first_row(response)


def update_inventory(
  client: Client,
  item_name: str,
  quantity: int,
  user_id: str | None = None,
) -> dict[str, Any]:
  q = (
    client.table("inventory")
    .update(
      {
        "quantity": quantity,
        "updated_at": datetime.now(timezone.utc).isoformat(),
      }
    )
    .eq("item_name", item_name)
  )
  if user_id:
    q = q.eq("user_id", user_id)
  response = q.execute()
  return _first_row(response)


def upsert_inventory_from_detection(
  client: Client,
  item_name: str,
  quantity: int,
  user_id: str | None = None,
) -> dict[str, Any]:
  now = datetime.now(timezone.utc).isoformat()
  existing = _inventory_row_by_name(client, item_name, user_id)
  locked = bool(existing and existing.get("expiry_locked"))
  if existing is None or not locked:
    expires_at = estimated_expires_at_utc(item_name).isoformat()
  else:
    expires_at = existing.get("expires_at")

  payload: dict[str, Any] = {
    "item_name": item_name,
    "quantity": quantity,
    "updated_at": now,
    "expires_at": expires_at,
    "expiry_locked": locked,
  }
  if user_id:
    payload["user_id"] = user_id

  if user_id:
    if existing:
      q = (
        client.table("inventory")
        .update(payload)
        .eq("item_name", item_name)
        .eq("user_id", user_id)
      )
      response = q.execute()
    else:
      response = client.table("inventory").insert(payload).execute()
  else:
    response = client.table("inventory").upsert(
      payload, on_conflict="item_name"
    ).execute()

  return _first_row(response)


def upsert_inventory(
  client: Client, item_name: str, quantity: int, user_id: str | None = None
) -> dict[str, Any]:
  return upsert_inventory_from_detection(client, item_name, quantity, user_id)


def update_inventory_expiry(
  client: Client,
  item_name: str,
  *,
  expires_at: datetime | str | None,
  expiry_locked: bool | None = None,
  user_id: str | None = None,
) -> dict[str, Any]:
  update_payload: dict[str, Any] = {
    "updated_at": datetime.now(timezone.utc).isoformat(),
  }
  if expires_at is not None:
    if isinstance(expires_at, datetime):
      update_payload["expires_at"] = expires_at.astimezone(timezone.utc).isoformat()
    else:
      update_payload["expires_at"] = str(expires_at)
  if expiry_locked is not None:
    update_payload["expiry_locked"] = bool(expiry_locked)

  q = client.table("inventory").update(update_payload).eq("item_name", item_name)
  if user_id:
    q = q.eq("user_id", user_id)
  response = q.execute()
  return _first_row(response)


def insert_detection_log(
  client: Client,
  item_name: str,
  quantity: int,
  confidence: float,
  user_id: str | None = None,
) -> dict[str, Any]:
  payload: dict[str, Any] = {
    "item_name": item_name,
    "quantity": quantity,
    "confidence": confidence,
    "detected_at": datetime.now(timezone.utc).isoformat(),
  }
  if user_id:
    payload["user_id"] = user_id
  response = client.table("detection_logs").insert(payload).execute()
  return _first_row(response)


def get_inventory(client: Client, user_id: str | None = None) -> list[dict[str, Any]]:
  q = _inventory_query(client, user_id).order("item_name")
  response = q.execute()
  return response.data or []


def get_detection_logs(
  client: Client, limit: int = 20, user_id: str | None = None
) -> list[dict[str, Any]]:
  columns = _DETECTION_LOG_COLUMNS
  if user_id:
    columns = f"{_DETECTION_LOG_COLUMNS}, user_id"
  q = (
    client.table("detection_logs")
    .select(columns)
    .order("detected_at", desc=True)
    .limit(limit)
  )
  if user_id:
    q = q.eq("user_id", user_id)
  response = q.execute()
  return response.data or []


def get_notifications(
  client: Client,
  limit: int = 50,
  unread_only: bool = False,
  user_id: str | None = None,
) -> list[dict[str, Any]]:
  q = (
    client.table("expiration_notifications")
    .select(
      "id, user_id, inventory_id, item_name, expires_at, days_remaining, message, read, created_at"
    )
    .order("created_at", desc=True)
    .limit(limit)
  )
  if user_id:
    q = q.eq("user_id", user_id)
  if unread_only:
    q = q.eq("read", False)
  try:
    response = q.execute()
    return response.data or []
  except Exception:
    return []


def mark_notification_read(
  client: Client,
  notification_id: int,
  user_id: str | None = None,
) -> dict[str, Any]:
  q = (
    client.table("expiration_notifications")
    .update({"read": True})
    .eq("id", notification_id)
  )
  if user_id:
    q = q.eq("user_id", user_id)
  response = q.execute()
  return _first_row(response)
