/**
 * Phase 8: smart inventory events (Added / Removed / Moved) derived from
 * YOLO detections + optical flow + feature tracking.
 */
const TYPE_STYLE = {
  added: "border-emerald-500/40 bg-emerald-500/10 text-emerald-200",
  removed: "border-red-500/40 bg-red-500/10 text-red-200",
  moved: "border-amber-500/40 bg-amber-500/10 text-amber-200",
};

function formatTime(value) {
  if (!value) return "";
  try {
    return new Date(value).toLocaleTimeString();
  } catch {
    return "";
  }
}

export function EventsPanel({ events = [], busy, onDetect }) {
  return (
    <section className="rounded-2xl border border-gray-800 bg-gray-900/50 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-display text-sm font-semibold text-white">Inventory events</h3>
        <button
          type="button"
          disabled={busy}
          onClick={onDetect}
          className="rounded-lg border border-cyan-600/50 bg-cyan-600/20 px-3 py-1.5 text-xs font-semibold text-cyan-200 hover:bg-cyan-600/30 disabled:opacity-40"
        >
          {busy ? "Detecting…" : "Detect events"}
        </button>
      </div>

      {events.length === 0 ? (
        <p className="rounded-lg border border-dashed border-gray-700 py-6 text-center text-xs text-gray-500">
          No events yet. Add or remove an item in front of the camera, then detect.
        </p>
      ) : (
        <ul className="space-y-2">
          {events.map((ev, idx) => (
            <li
              key={ev.id ?? `${ev.item_name}-${ev.created_at ?? idx}`}
              className={`flex items-center justify-between rounded-lg border px-3 py-2 text-sm ${
                TYPE_STYLE[ev.event_type] ?? "border-gray-700 bg-gray-800/60 text-gray-300"
              }`}
            >
              <span className="font-medium capitalize">
                {ev.event_type} · {String(ev.item_name || "").replace(/_/g, " ")}
              </span>
              <span className="text-xs opacity-80">
                {ev.magnitude != null ? `×${ev.magnitude}` : ""} {formatTime(ev.created_at)}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
