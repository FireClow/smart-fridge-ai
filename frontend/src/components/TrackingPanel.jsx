/**
 * Course topic: Feature-Based Tracking (Shi-Tomasi + Lucas-Kanade).
 * Trajectory polylines with track IDs and active-track count.
 */
export function TrackingPanel({ image, activeTracks }) {
  return (
    <section className="rounded-2xl border border-gray-800 bg-gray-900/50 p-4">
      <h3 className="mb-3 font-display text-sm font-semibold text-white">Feature tracking</h3>
      {image ? (
        <img
          src={`data:image/jpeg;base64,${image}`}
          alt="Feature trajectories"
          className="w-full rounded-lg border border-gray-800 object-contain"
        />
      ) : (
        <div className="flex h-40 items-center justify-center rounded-lg border border-dashed border-gray-700 text-xs text-gray-500">
          Waiting for frames…
        </div>
      )}
      <div className="mt-3 rounded-lg border border-gray-800 bg-gray-950/60 p-3 text-sm">
        <p className="text-xs uppercase tracking-wider text-gray-500">Active tracks</p>
        <p className="mt-1 font-display text-2xl font-bold text-white tabular-nums">
          {activeTracks ?? "—"}
        </p>
      </div>
    </section>
  );
}
