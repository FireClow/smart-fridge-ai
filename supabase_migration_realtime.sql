-- Enable Supabase Realtime (postgres_changes) for app tables.
-- Run in Supabase SQL Editor after supabase_migration_multi_user.sql.
-- Or: Database → Replication → enable Realtime per table in the dashboard.

ALTER PUBLICATION supabase_realtime ADD TABLE inventory;
ALTER PUBLICATION supabase_realtime ADD TABLE detection_logs;
ALTER PUBLICATION supabase_realtime ADD TABLE expiration_notifications;
