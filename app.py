"""
Smart Fridge AI entry point.

Setup (Windows):
1. Create and activate a virtual environment.
2. Install dependencies: pip install -r requirements.txt
3. Copy .env.example to .env and fill SUPABASE_URL and SUPABASE_KEY (publishable or anon key from Data API).
4. Run supabase_schema.sql in the Supabase SQL Editor (or set SUPABASE_DB_URL and run scripts/apply_supabase_schema.py).
5. Start detection: python app.py
   Smoke test (no webcam): set SKIP_WEBCAM=1 then python app.py
"""

from detect import run_detection


if __name__ == "__main__":
  try:
    run_detection()
  except (FileNotFoundError, ValueError, ConnectionError, RuntimeError) as exc:
    print(f"Startup error: {exc}")
