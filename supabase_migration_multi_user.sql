-- Multi-user schema, RLS, and expiration notifications.
-- Run in Supabase SQL Editor after supabase_schema.sql.

-- Profiles linked to Supabase Auth users
CREATE TABLE IF NOT EXISTS profiles (
    id          UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    display_name TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "profiles_select_own" ON profiles;
CREATE POLICY "profiles_select_own"
  ON profiles FOR SELECT TO authenticated
  USING (auth.uid() = id);

DROP POLICY IF EXISTS "profiles_insert_own" ON profiles;
CREATE POLICY "profiles_insert_own"
  ON profiles FOR INSERT TO authenticated
  WITH CHECK (auth.uid() = id);

DROP POLICY IF EXISTS "profiles_update_own" ON profiles;
CREATE POLICY "profiles_update_own"
  ON profiles FOR UPDATE TO authenticated
  USING (auth.uid() = id);

-- Add user_id to inventory (nullable for legacy rows; new writes should set it)
ALTER TABLE inventory ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
-- Legacy rows may have NULL user_id until backfilled.

-- Replace global unique item_name with per-user uniqueness
ALTER TABLE inventory DROP CONSTRAINT IF EXISTS inventory_item_name_key;
CREATE UNIQUE INDEX IF NOT EXISTS inventory_user_item_unique
  ON inventory (user_id, item_name)
  WHERE user_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_inventory_user_id ON inventory (user_id);
CREATE INDEX IF NOT EXISTS idx_inventory_user_expires ON inventory (user_id, expires_at);

-- Add user_id to detection_logs
ALTER TABLE detection_logs ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
-- NULL allowed for legacy logs.
CREATE INDEX IF NOT EXISTS idx_detection_logs_user_detected
  ON detection_logs (user_id, detected_at DESC);

-- Expiration notifications
CREATE TABLE IF NOT EXISTS expiration_notifications (
    id              BIGSERIAL PRIMARY KEY,
    user_id         UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    inventory_id    BIGINT REFERENCES inventory(id) ON DELETE CASCADE,
    item_name       TEXT NOT NULL,
    expires_at      TIMESTAMPTZ,
    days_remaining  INT,
    message         TEXT NOT NULL,
    read            BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_expiration_notifications_user
  ON expiration_notifications (user_id, created_at DESC);

ALTER TABLE expiration_notifications ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "expiration_notifications_own" ON expiration_notifications;
CREATE POLICY "expiration_notifications_own"
  ON expiration_notifications FOR ALL TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Authenticated RLS for inventory
DROP POLICY IF EXISTS "inventory_authenticated_all" ON inventory;
CREATE POLICY "inventory_authenticated_select"
  ON inventory FOR SELECT TO authenticated
  USING (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "inventory_authenticated_insert"
  ON inventory FOR INSERT TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "inventory_authenticated_update"
  ON inventory FOR UPDATE TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "inventory_authenticated_delete"
  ON inventory FOR DELETE TO authenticated
  USING (auth.uid() = user_id);

-- Authenticated RLS for detection_logs
DROP POLICY IF EXISTS "detection_logs_authenticated_all" ON detection_logs;
CREATE POLICY "detection_logs_authenticated_select"
  ON detection_logs FOR SELECT TO authenticated
  USING (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "detection_logs_authenticated_insert"
  ON detection_logs FOR INSERT TO authenticated
  WITH CHECK (auth.uid() = user_id);

-- Optional: keep anon policies for backward-compatible demo (comment out in production)
-- DROP POLICY IF EXISTS "inventory_anon_all" ON inventory;
-- DROP POLICY IF EXISTS "detection_logs_anon_all" ON detection_logs;

-- Auto-create profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, display_name)
  VALUES (NEW.id, COALESCE(NEW.raw_user_meta_data->>'display_name', split_part(NEW.email, '@', 1)))
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
