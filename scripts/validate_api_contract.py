"""Validate frontend API paths against FastAPI routes (no 404 for registered calls)."""

from __future__ import annotations

import sys
from pathlib import Path

from starlette.testclient import TestClient

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
  sys.path.insert(0, str(_ROOT))

from backend.main import app  # noqa: E402

# Fallback contract — keep aligned with frontend/src/lib/apiRoutes.js
FRONTEND_CONTRACT = [
  ("GET", "/api/inventory"),
  ("GET", "/api/logs"),
  ("GET", "/api/stats"),
  ("GET", "/api/health"),
  ("GET", "/api/model/info"),
  ("POST", "/api/scan/image"),
  ("PATCH", "/api/inventory/{item_name}"),
  ("GET", "/api/notifications"),
  ("POST", "/api/notifications/generate"),
  ("PATCH", "/api/notifications/{notification_id}/read"),
  ("POST", "/api/cv/analyze"),
  ("GET", "/api/cv/metrics"),
  ("POST", "/api/cv/reset"),
  ("POST", "/api/cv/match"),
  ("POST", "/api/cv/homography"),
  ("POST", "/api/cv/events"),
  ("GET", "/api/cv/events"),
  ("POST", "/api/cv/reference/{class_name}"),
  ("GET", "/api/cv/reference/{class_name}"),
]


def load_routes_from_frontend() -> list[tuple[str, str]]:
  """Contract aligned with frontend/src/lib/apiRoutes.js and frontend/src/services/api.js."""
  return FRONTEND_CONTRACT


def collect_backend_routes() -> set[tuple[str, str]]:
  out: set[tuple[str, str]] = set()
  for route in app.routes:
    if not hasattr(route, "methods") or not hasattr(route, "path"):
      continue
    if not route.path.startswith("/api"):
      continue
    for method in route.methods - {"HEAD", "OPTIONS"}:
      out.add((method, route.path))
  return out


def path_matches(template: str, concrete: str) -> bool:
  t_parts = template.strip("/").split("/")
  c_parts = concrete.strip("/").split("/")
  if len(t_parts) != len(c_parts):
    return False
  for t, c in zip(t_parts, c_parts):
    if t.startswith("{") and t.endswith("}"):
      continue
    if t != c:
      return False
  return True


def find_route(method: str, path_template: str, backend: set[tuple[str, str]]) -> str | None:
  for bm, bp in backend:
    if bm == method and path_matches(bp, path_template):
      return bp
  return None


def main() -> int:
  contract = load_routes_from_frontend()
  backend = collect_backend_routes()
  print("Backend /api routes:")
  for m, p in sorted(backend, key=lambda x: x[1]):
    print(f"  {m:6} {p}")

  print("\nContract validation:")
  errors: list[str] = []
  seen: set[tuple[str, str]] = set()
  for method, template in contract:
    key = (method, template)
    if key in seen:
      continue
    seen.add(key)
    hit = find_route(method, template, backend)
    if hit:
      print(f"  OK   {method:6} {template} -> {hit}")
    else:
      print(f"  FAIL {method:6} {template}")
      errors.append(f"Missing backend route for {method} {template}")

  client = TestClient(app)
  get_probes = [
    "/api/health",
    "/api/model/info",
    "/api/inventory",
    "/api/logs?limit=5",
    "/api/stats",
    "/api/notifications?limit=5",
    "/api/cv/metrics",
    "/api/cv/events?limit=5",
    "/api/cv/reference/apple",
  ]
  print("\nHTTP probes (must not be 404):")
  for url in get_probes:
    status = client.get(url).status_code
    ok = status != 404
    mark = "OK" if ok else "FAIL"
    print(f"  {mark} {status} GET {url}")
    if not ok:
      errors.append(f"GET {url} returned 404")

  reset_status = client.post("/api/cv/reset").status_code
  print(f"  {'OK' if reset_status != 404 else 'FAIL'} {reset_status} POST /api/cv/reset")
  if reset_status == 404:
    errors.append("POST /api/cv/reset returned 404")

  if errors:
    print("\nErrors:")
    for e in errors:
      print(f"  - {e}")
    return 1

  print("\nAll contract checks passed.")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
