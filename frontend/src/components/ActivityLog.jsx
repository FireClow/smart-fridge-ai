import { formatDateTime } from "../lib/format.js";

export function ActivityLog({ logs, loading }) {
  if (loading && (!logs || logs.length === 0)) {
    return (
      <section className="flex h-full min-h-[280px] flex-col rounded-2xl border border-gray-800 bg-gray-900/50 p-4">
        <h2 className="mb-4 font-display text-sm font-semibold uppercase tracking-wider text-gray-400">
          Activity log
        </h2>
        <div className="flex flex-1 flex-col gap-2">
          {[1, 2, 3, 4, 5].map((i) => (
            <div
              key={i}
              className="h-10 animate-pulse rounded-lg bg-gray-800/80"
            />
          ))}
        </div>
      </section>
    );
  }

  return (
    <section className="flex max-h-[420px] min-h-[280px] flex-col overflow-hidden rounded-2xl border border-gray-800 bg-gray-900/50 shadow-inner">
      <div className="border-b border-gray-800/80 px-4 py-3">
        <h2 className="font-display text-sm font-semibold uppercase tracking-wider text-gray-300">
          Detection history
        </h2>
        <p className="text-xs text-gray-500">Latest events from AI pipeline</p>
      </div>
      <div className="flex-1 overflow-y-auto p-2">
        {!logs || logs.length === 0 ? (
          <p className="p-4 text-center text-sm text-gray-500">
            No detections yet. Run the Python detector to populate logs.
          </p>
        ) : (
          <ul className="space-y-1">
            {logs.map((row, idx) => (
              <li
                key={`${row.id}-${idx}`}
                className="animate-fade-in rounded-xl border border-transparent bg-gray-950/40 px-3 py-2.5 text-sm transition hover:border-cyan-500/20 hover:bg-gray-800/60"
                style={{ animationDelay: `${idx * 40}ms` }}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-medium capitalize text-cyan-100/90">
                    {String(row.item_name || "").replace(/_/g, " ")}
                  </span>
                  <span className="tabular-nums text-gray-400">
                    ×{row.quantity}
                  </span>
                </div>
                <div className="mt-1 flex justify-between text-xs text-gray-500">
                  <span>
                    {row.confidence != null
                      ? `${Math.round(Number(row.confidence) * 100)}% conf.`
                      : "—"}
                  </span>
                  <span>{formatDateTime(row.detected_at)}</span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
