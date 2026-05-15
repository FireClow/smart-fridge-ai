import { Link } from "react-router-dom";

export function ExpiryAlerts({ notifications, loading }) {
  if (loading) {
    return (
      <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-4 text-sm text-gray-500">
        Loading alerts…
      </div>
    );
  }

  const unread = (notifications || []).filter((n) => !n.read).slice(0, 3);

  if (unread.length === 0) {
    return (
      <div className="rounded-xl border border-gray-800 bg-gray-900/40 p-4 text-sm text-gray-500">
        No expiration warnings right now.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {unread.map((n) => (
        <div
          key={n.id}
          className="flex items-start justify-between gap-3 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3"
        >
          <div>
            <p className="text-sm font-medium text-amber-100">{n.message}</p>
            {n.days_remaining != null ? (
              <p className="mt-0.5 text-xs text-amber-200/70">
                {n.days_remaining} day{n.days_remaining === 1 ? "" : "s"} remaining
              </p>
            ) : null}
          </div>
        </div>
      ))}
      <Link
        to="/notifications"
        className="inline-block text-xs font-medium text-cyan-400 hover:text-cyan-300"
      >
        View all notifications →
      </Link>
    </div>
  );
}
