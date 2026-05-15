-- Run in Supabase SQL Editor on an existing project that already has `inventory`.
-- Adds expiry columns used by the dashboard and detection pipelines.

ALTER TABLE inventory
  ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ;

ALTER TABLE inventory
  ADD COLUMN IF NOT EXISTS expiry_locked BOOLEAN NOT NULL DEFAULT false;

COMMENT ON COLUMN inventory.expires_at IS 'Estimated or user-set expiry instant (UTC).';
COMMENT ON COLUMN inventory.expiry_locked IS 'When true, automated scans do not overwrite expires_at.';
