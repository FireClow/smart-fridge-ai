"""Expiration notification generation."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

from supabase import Client

_WARNING_DAYS = int(os.getenv("EXPIRY_WARNING_DAYS", "3"))


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


def _days_remaining(expires_at: datetime, now: datetime) -> int:
  delta = expires_at.date() - now.date()
  return max(0, delta.days)


def generate_notifications(
  client: Client,
  user_id: str | None,
) -> list[dict[str, Any]]:
  """Create in-app notifications for items expiring within the warning window."""
  now = datetime.now(timezone.utc)
  soon = now + timedelta(days=_WARNING_DAYS)

  query = client.table("inventory").select(
    "id, item_name, expires_at, user_id"
  )
  if user_id:
    query = query.eq("user_id", user_id)
  rows = query.execute().data or []

  created: list[dict[str, Any]] = []
  for row in rows:
    exp = _parse_expires_at(row.get("expires_at"))
    if exp is None or exp < now or exp > soon:
      continue

    days = _days_remaining(exp, now)
    item_name = row["item_name"]
    if days == 0:
      message = f"{item_name} expires today"
    elif days == 1:
      message = f"{item_name} expires in 1 day"
    else:
      message = f"{item_name} expires in {days} days"

    payload: dict[str, Any] = {
      "inventory_id": row["id"],
      "item_name": item_name,
      "expires_at": exp.isoformat(),
      "days_remaining": days,
      "message": message,
      "read": False,
    }
    if user_id:
      payload["user_id"] = user_id

    try:
      existing = (
        client.table("expiration_notifications")
        .select("id")
        .eq("inventory_id", row["id"])
        .gte("created_at", now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat())
        .limit(1)
        .execute()
      )
      if existing.data:
        continue
      if user_id:
        existing = (
          client.table("expiration_notifications")
          .select("id")
          .eq("user_id", user_id)
          .eq("inventory_id", row["id"])
          .gte(
            "created_at",
            now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat(),
          )
          .limit(1)
          .execute()
        )
        if existing.data:
          continue

      response = client.table("expiration_notifications").insert(payload).execute()
      if response.data:
        created.append(response.data[0])
    except Exception:
      continue

  return created
