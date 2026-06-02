import { createClient } from "@supabase/supabase-js";

const url = import.meta.env.VITE_SUPABASE_URL || "";
const key = import.meta.env.VITE_SUPABASE_KEY || "";

export const supabase =
  url && key ? createClient(url, key) : null;

const isDev = import.meta.env.DEV;

function logChannelStatus(channelName, status, err) {
  if (!isDev) return;
  if (status === "SUBSCRIBED") return;
  if (status === "CHANNEL_ERROR" || status === "TIMED_OUT" || status === "CLOSED") {
    console.warn(
      `[supabase realtime] ${channelName}: ${status}`,
      err?.message || "Enable Realtime for this table in Supabase (see supabase_migration_realtime.sql).",
    );
  }
}

/**
 * Subscribe to postgres_changes on a public table.
 * Pass userId to filter events to the logged-in user's rows (RLS-aligned).
 */
export function subscribePostgresChanges(table, onChange, userId = null) {
  if (!supabase) return () => {};

  const channelName = `${table}-changes${userId ? `-${userId.slice(0, 8)}` : ""}`;
  const config = {
    event: "*",
    schema: "public",
    table,
  };
  if (userId) {
    config.filter = `user_id=eq.${userId}`;
  }

  const channel = supabase
    .channel(channelName)
    .on("postgres_changes", config, () => {
      onChange?.();
    })
    .subscribe((status, err) => {
      logChannelStatus(channelName, status, err);
    });

  return () => {
    supabase.removeChannel(channel);
  };
}

/** Subscribe to inventory table changes. Requires Realtime enabled in Supabase. */
export function subscribeInventory(onChange, userId = null) {
  return subscribePostgresChanges("inventory", onChange, userId);
}

/** Subscribe to detection_logs table changes. */
export function subscribeLogs(onChange, userId = null) {
  return subscribePostgresChanges("detection_logs", onChange, userId);
}

/** Subscribe to expiration_notifications table changes. */
export function subscribeNotifications(onChange, userId = null) {
  return subscribePostgresChanges("expiration_notifications", onChange, userId);
}

/** Subscribe to cv_events table changes (smart inventory events). */
export function subscribeCvEvents(onChange, userId = null) {
  return subscribePostgresChanges("cv_events", onChange, userId);
}
