/**
 * Course topic: ORB descriptors (Oriented FAST + Rotated BRIEF).
 * Shows rich keypoints (size + orientation) and counts.
 */
export function OrbPanel({ image, keypointCount, descriptorCount, loading = false }) {
  return (
    <section className="rounded-2xl border border-gray-800 bg-gray-900/50 p-4">
      <h3 className="mb-3 font-display text-sm font-semibold text-white">ORB features</h3>
      {loading ? (
        <div className="flex h-40 items-center justify-center rounded-lg border border-dashed border-gray-700 text-xs text-gray-400">
          Analyzing uploaded image…
        </div>
      ) : image ? (
        <img
          src={`data:image/jpeg;base64,${image}`}
          alt="ORB keypoints"
          className="w-full rounded-lg border border-gray-800 object-contain"
        />
      ) : (
        <div className="flex h-40 items-center justify-center rounded-lg border border-dashed border-gray-700 text-xs text-gray-500">
          Waiting for frame…
        </div>
      )}
      <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
        <div className="rounded-lg border border-gray-800 bg-gray-950/60 p-3">
          <p className="text-xs uppercase tracking-wider text-gray-500">Keypoints</p>
          <p className="mt-1 font-display text-2xl font-bold text-white tabular-nums">
            {keypointCount ?? "—"}
          </p>
        </div>
        <div className="rounded-lg border border-gray-800 bg-gray-950/60 p-3">
          <p className="text-xs uppercase tracking-wider text-gray-500">Descriptors</p>
          <p className="mt-1 font-display text-2xl font-bold text-white tabular-nums">
            {descriptorCount ?? "—"}
          </p>
        </div>
      </div>
    </section>
  );
}
