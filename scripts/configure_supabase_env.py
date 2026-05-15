"""Write or update .env with Supabase credentials (no secrets printed)."""

from __future__ import annotations

import argparse
from pathlib import Path

from dotenv import dotenv_values


def _normalize_supabase_url(url: str) -> str:
  u = url.strip().rstrip("/")
  suffix = "/rest/v1"
  if u.endswith(suffix):
    return u[: -len(suffix)]
  return u


def _parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(
    description="Update .env with SUPABASE_URL and SUPABASE_KEY (and optional SUPABASE_DB_URL).",
  )
  parser.add_argument("--url", required=True, help="Supabase project URL (Data API).")
  parser.add_argument("--key", required=True, help="Supabase anon (public) API key.")
  parser.add_argument(
    "--database-url",
    default="",
    help="Optional Postgres URI for scripts/apply_supabase_schema.py (Session pooler or direct).",
  )
  parser.add_argument(
    "--env-file",
    default=".env",
    help="Path to .env file (default: .env in project root).",
  )
  return parser.parse_args()


def _merge_env(root: Path, env_path: Path, updates: dict[str, str]) -> None:
  example = root / ".env.example"
  base: dict[str, str | None] = {}
  if example.exists():
    base = {k: v for k, v in dotenv_values(example).items()}
  if env_path.exists():
    existing = {k: v for k, v in dotenv_values(env_path).items()}
    for k, v in existing.items():
      if v is not None and str(v).strip() != "":
        base[k] = v
  for k, v in updates.items():
    if v.strip():
      base[k] = v

  lines: list[str] = []
  for key, val in base.items():
    if val is None or str(val).strip() == "":
      lines.append(f"{key}=\n")
    else:
      lines.append(f"{key}={val}\n")

  env_path.write_text("".join(lines), encoding="utf-8")


def main() -> None:
  args = _parse_args()
  root = Path(__file__).resolve().parents[1]
  env_path = (root / args.env_file).resolve() if not Path(args.env_file).is_absolute() else Path(args.env_file)

  updates = {
    "SUPABASE_URL": _normalize_supabase_url(args.url.strip()),
    "SUPABASE_KEY": args.key.strip(),
  }
  if args.database_url.strip():
    updates["SUPABASE_DB_URL"] = args.database_url.strip()

  _merge_env(root, env_path, updates)
  print(f"Updated {env_path.relative_to(root)} (credentials not echoed).")


if __name__ == "__main__":
  main()
