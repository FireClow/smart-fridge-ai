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
      "Alternatively, paste supabase_schema.sql into the Supabase SQL Editor and run it.",
      file=sys.stderr,
    )
    return 1

  try:
    import psycopg2
  except ImportError as exc:
    print("Install psycopg2-binary: pip install psycopg2-binary", file=sys.stderr)
    raise SystemExit(1) from exc

  root = Path(__file__).resolve().parents[1]
  sql_path = root / "supabase_schema.sql"
  sql = sql_path.read_text(encoding="utf-8")

  conn = psycopg2.connect(db_url)
  conn.autocommit = True
  try:
    with conn.cursor() as cur:
      cur.execute(sql)
  finally:
    conn.close()

  print("Schema applied successfully.")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
