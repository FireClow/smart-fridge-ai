"""One-off check: connect_to_supabase + SELECT inventory. Run from project root."""

from __future__ import annotations

import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
  sys.path.insert(0, str(_root))

from database import connect_to_supabase, get_inventory  # noqa: E402

try:
  from postgrest.exceptions import APIError
except ImportError:  # pragma: no cover
  APIError = Exception  # type: ignore[misc, assignment]


def main() -> int:
  try:
    client = connect_to_supabase()
  except (ValueError, ConnectionError) as exc:
    print(f"connect_to_supabase: FAILED — {exc}", file=sys.stderr)
    return 1

  print("connect_to_supabase: OK")

  try:
    rows = get_inventory(client)
  except APIError as exc:
    print(f"get_inventory: FAILED — {exc}", file=sys.stderr)
    print(
      "Hint: run supabase_schema.sql in the Supabase SQL Editor "
      "(Table Editor should then show inventory / detection_logs).",
      file=sys.stderr,
    )
    return 2
  except Exception as exc:  # pragma: no cover
    print(f"get_inventory: FAILED — {exc}", file=sys.stderr)
    return 2

  print(f"get_inventory: OK ({len(rows)} row(s))")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
