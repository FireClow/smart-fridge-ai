"""Apply supabase_schema.sql using a direct Postgres connection (optional path)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def main() -> int:
  db_url = os.getenv("SUPABASE_DB_URL", "").strip()
  if not db_url:
    print(
      "SUPABASE_DB_URL is not set. Add it to .env (Postgres URI from Supabase "
      "Project Settings -> Database), then re-run this script.\n"
      "Alternatively, paste the SQL files into the Supabase SQL Editor and run them.",
      file=sys.stderr,
    )
    return 1

  try:
    import psycopg2
  except ImportError as exc:
    print("Install psycopg2-binary: pip install psycopg2-binary", file=sys.stderr)
    raise SystemExit(1) from exc

  root = Path(__file__).resolve().parents[1]
  sql_files = [
    root / "supabase_schema.sql",
    root / "supabase_migration_inventory_expiry.sql",
    root / "supabase_migration_multi_user.sql",
    root / "supabase_migration_realtime.sql",
  ]

  conn = psycopg2.connect(db_url)
  conn.autocommit = True
  try:
    with conn.cursor() as cur:
      for sql_path in sql_files:
        if not sql_path.is_file():
          print(f"Skip missing: {sql_path.name}", file=sys.stderr)
          continue
        print(f"Applying {sql_path.name}...")
        try:
          cur.execute(sql_path.read_text(encoding="utf-8"))
        except Exception as exc:
          if sql_path.name == "supabase_migration_realtime.sql" and "already member" in str(
            exc
          ).lower():
            print(f"  (already in publication, skipping: {exc})")
          else:
            raise
  finally:
    conn.close()

  print("Schema and migrations applied successfully.")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
