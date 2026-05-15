-- Run this script in the Supabase SQL Editor before starting the app.

-- Current inventory snapshot (one row per food item).
CREATE TABLE IF NOT EXISTS inventory (
    id             BIGSERIAL PRIMARY KEY,
    item_name      TEXT UNIQUE NOT NULL,
    quantity       INT NOT NULL DEFAULT 0,
    updated_at     TIMESTAMPTZ DEFAULT NOW(),
    expires_at     TIMESTAMPTZ,
    expiry_locked  BOOLEAN NOT NULL DEFAULT false
);

-- Historical log for each saved detection event.
CREATE TABLE IF NOT EXISTS detection_logs (
    id          BIGSERIAL PRIMARY KEY,
    item_name   TEXT NOT NULL,
    quantity    INT NOT NULL,
    confidence  FLOAT NOT NULL,
    detected_at TIMESTAMPTZ DEFAULT NOW()
);

-- Optional indexes for faster reads and log filtering.
CREATE INDEX IF NOT EXISTS idx_inventory_item_name ON inventory (item_name);
CREATE INDEX IF NOT EXISTS idx_detection_logs_detected_at ON detection_logs (detected_at DESC);

-- Row Level Security for use with publishable / anon API keys from the Data API.
ALTER TABLE inventory ENABLE ROW LEVEL SECURITY;
ALTER TABLE detection_logs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "inventory_anon_all" ON inventory;
CREATE POLICY "inventory_anon_all"
  ON inventory
  FOR ALL
  TO anon
  USING (true)
  WITH CHECK (true);

DROP POLICY IF EXISTS "detection_logs_anon_all" ON detection_logs;
CREATE POLICY "detection_logs_anon_all"
  ON detection_logs
  FOR ALL
  TO anon
  USING (true)
  WITH CHECK (true);
