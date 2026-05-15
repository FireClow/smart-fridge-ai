import { createClient } from "@supabase/supabase-js";

const url = import.meta.env.VITE_SUPABASE_URL || "";
const key = import.meta.env.VITE_SUPABASE_KEY || "";

export const supabase =
  url && key ? createClient(url, key) : null;

/**
 * Subscribe to inventory table changes (INSERT/UPDATE/DELETE).
 * Requires Realtime enabled for `inventory` in Supabase dashboard.
 */
export function subscribeInventory(onChange) {
  if (!supabase) return () => {};

  const channel = supabase
    .channel("inventory-changes")
    .on(
      "postgres_changes",
      { event: "*", schema: "public", table: "inventory" },
      () => {
        onChange?.();
      },
    )
    .subscribe();

  return () => {
    supabase.removeChannel(channel);
  };
}

/**
 * Subscribe to detection_logs table changes.
 */
export function subscribeLogs(onChange) {
  if (!supabase) return () => {};

  const channel = supabase
    .channel("logs-changes")
    .on(
      "postgres_changes",
      { event: "*", schema: "public", table: "detection_logs" },
      () => {
        onChange?.();
      },
    )
    .subscribe();

  return () => {
    supabase.removeChannel(channel);
  };
}
