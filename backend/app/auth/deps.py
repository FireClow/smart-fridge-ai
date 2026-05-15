"""JWT verification via Supabase Auth."""

from __future__ import annotations

import os
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from database import connect_to_supabase

_bearer = HTTPBearer(auto_error=False)
_AUTH_REQUIRED = os.getenv("REQUIRE_AUTH", "false").lower() in ("1", "true", "yes")


def user_id_from_token(token: str) -> str | None:
  """Validate JWT and return user id, or None if invalid."""
  try:
    client = connect_to_supabase()
    response = client.auth.get_user(token)
    user = getattr(response, "user", None)
    if user is None and isinstance(response, dict):
      user = response.get("user")
    if user is None:
      return None
    return str(getattr(user, "id", None) or user.get("id"))
  except Exception:
    return None


async def get_current_user_id(
  request: Request,
  credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> str | None:
  if credentials and credentials.credentials:
    uid = user_id_from_token(credentials.credentials)
    if uid:
      request.state.user_id = uid
      return uid
  if hasattr(request.state, "user_id") and request.state.user_id:
    return request.state.user_id
  if _AUTH_REQUIRED:
    raise HTTPException(status_code=401, detail="Authentication required.")
  return None


async def require_user_id(
  user_id: Annotated[str | None, Depends(get_current_user_id)],
) -> str:
  if not user_id:
    raise HTTPException(status_code=401, detail="Authentication required.")
  return user_id
