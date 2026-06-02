-- Computer Vision upgrade: smart-inventory events + reference image storage.
-- Run in the Supabase SQL Editor after supabase_migration_multi_user.sql.

-- Phase 8: smart inventory events (added / removed / moved)
CREATE TABLE IF NOT EXISTS cv_events (
    id          BIGSERIAL PRIMARY KEY,
    user_id     UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    item_name   TEXT NOT NULL,
    event_type  TEXT NOT NULL CHECK (event_type IN ('added', 'removed', 'moved')),
    magnitude   FLOAT NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cv_events_user_created
  ON cv_events (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_cv_events_created_at
  ON cv_events (created_at DESC);

ALTER TABLE cv_events ENABLE ROW LEVEL SECURITY;

-- Authenticated users see/manage their own events (NULL user_id = legacy/demo).
DROP POLICY IF EXISTS "cv_events_authenticated_select" ON cv_events;
CREATE POLICY "cv_events_authenticated_select"
  ON cv_events FOR SELECT TO authenticated
  USING (auth.uid() = user_id OR user_id IS NULL);

DROP POLICY IF EXISTS "cv_events_authenticated_insert" ON cv_events;
CREATE POLICY "cv_events_authenticated_insert"
  ON cv_events FOR INSERT TO authenticated
  WITH CHECK (auth.uid() = user_id);

-- Optional anon policy for the backward-compatible demo (service role bypasses RLS).
DROP POLICY IF EXISTS "cv_events_anon_all" ON cv_events;
CREATE POLICY "cv_events_anon_all"
  ON cv_events FOR ALL TO anon
  USING (true)
  WITH CHECK (true);

-- Realtime so the CV analytics dashboard updates live.
ALTER PUBLICATION supabase_realtime ADD TABLE cv_events;

-- Phase 4: reference image bucket for ORB feature matching.
-- Storage buckets cannot be created with plain CREATE TABLE; use the helper.
INSERT INTO storage.buckets (id, name, public)
VALUES ('food-references', 'food-references', true)
ON CONFLICT (id) DO NOTHING;

-- Allow authenticated users to manage reference images (service role bypasses RLS).
DROP POLICY IF EXISTS "food_references_read" ON storage.objects;
CREATE POLICY "food_references_read"
  ON storage.objects FOR SELECT TO public
  USING (bucket_id = 'food-references');

DROP POLICY IF EXISTS "food_references_write" ON storage.objects;
CREATE POLICY "food_references_write"
  ON storage.objects FOR ALL TO authenticated
  USING (bucket_id = 'food-references')
  WITH CHECK (bucket_id = 'food-references');
