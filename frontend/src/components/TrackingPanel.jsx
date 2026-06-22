/**
 * Course topic: Feature-Based Tracking (Shi-Tomasi + Lucas-Kanade).
 * Trajectory polylines with track IDs and active-track count.
 */
export function TrackingPanel({ image, activeTracks, unavailable, loading = false, message }) {
  return (
    <section className="rounded-2xl border border-gray-800 bg-gray-900/50 p-4">
      <h3 className="mb-3 font-display text-sm font-semibold text-white">Feature tracking</h3>
      {loading ? (
        <div className="flex h-40 items-center justify-center rounded-lg border border-dashed border-gray-700 text-xs text-gray-400">
          {message || "Analyzing uploaded image…"}
        </div>
      ) : unavailable ? (
        <div className="flex h-40 items-center justify-center rounded-lg border border-dashed border-amber-700/50 bg-amber-950/20 px-4 text-center text-xs text-amber-200/90">
          {message || "Feature Tracking requires video or webcam input."}
        </div>
      ) : image ? (
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
          {unavailable || loading ? "—" : (activeTracks ?? "—")}
        </p>
      </div>
    </section>
  );
}
