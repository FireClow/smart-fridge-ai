import { useCallback, useEffect, useState } from "react";
import {
  fetchNotifications,
  generateNotifications,
  markNotificationRead,
} from "../services/api.js";

export function NotificationsPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterUnread, setFilterUnread] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      await generateNotifications().catch(() => {});
      const data = await fetchNotifications(filterUnread, 50);
      setItems(Array.isArray(data) ? data : []);
    } catch {
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [filterUnread]);

  useEffect(() => {
    void load();
  }, [load]);

  const onMarkRead = async (id) => {
    try {
      await markNotificationRead(id);
      setItems((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n)));
    } catch {
      /* ignore */
    }
  };

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl font-bold text-white">Notifications</h1>
          <p className="mt-1 text-sm text-gray-500">Food expiration warnings</p>
        </div>
        <label className="flex items-center gap-2 text-sm text-gray-400">
          <input
            type="checkbox"
            checked={filterUnread}
            onChange={(e) => setFilterUnread(e.target.checked)}
          />
          Unread only
        </label>
      </div>

      {loading ? (
        <p className="text-sm text-gray-500">Loading…</p>
      ) : items.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-gray-700 py-16 text-center text-gray-500">
          No notifications.
        </div>
      ) : (
        <ul className="space-y-3">
          {items.map((n) => (
            <li
              key={n.id}
              className={`flex items-center justify-between gap-4 rounded-xl border px-4 py-3 ${
                n.read
                  ? "border-gray-800 bg-gray-900/40 opacity-70"
                  : "border-amber-500/30 bg-amber-500/10"
              }`}
            >
              <div>
                <p className="text-sm font-medium text-gray-100">{n.message}</p>
                <p className="mt-0.5 text-xs text-gray-500">
                  {n.created_at ? new Date(n.created_at).toLocaleString() : ""}
                </p>
              </div>
              {!n.read ? (
                <button
                  type="button"
                  onClick={() => void onMarkRead(n.id)}
                  className="shrink-0 rounded-lg border border-gray-600 px-2 py-1 text-xs text-gray-300 hover:bg-gray-800"
                >
                  Mark read
                </button>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
