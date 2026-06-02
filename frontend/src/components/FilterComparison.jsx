/**
 * Course topic: Image Filtering & Enhancement.
 * Shows the original frame next to the filtered frame sent into YOLO.
 */
export function FilterComparison({ original, filtered, mode }) {
  if (!original && !filtered) return null;

  return (
    <section className="rounded-2xl border border-gray-800 bg-gray-900/50 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-display text-sm font-semibold text-white">
          Filtering comparison
        </h3>
        <span className="rounded-full border border-cyan-500/40 bg-cyan-500/10 px-2.5 py-0.5 text-xs font-medium uppercase tracking-wider text-cyan-300">
          {mode ?? "none"}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <figure>
          <img
            src={`data:image/jpeg;base64,${original}`}
            alt="Original frame"
            className="w-full rounded-lg border border-gray-800 object-contain"
          />
          <figcaption className="mt-1 text-center text-xs text-gray-500">Original</figcaption>
        </figure>
        <figure>
          {filtered ? (
            <img
              src={`data:image/jpeg;base64,${filtered}`}
              alt="Filtered frame"
              className="w-full rounded-lg border border-cyan-800/50 object-contain"
            />
          ) : (
            <div className="flex h-full min-h-[120px] items-center justify-center rounded-lg border border-dashed border-gray-700 text-xs text-gray-500">
              No filter applied
            </div>
          )}
          <figcaption className="mt-1 text-center text-xs text-gray-500">
            Filtered ({mode ?? "none"})
          </figcaption>
        </figure>
      </div>
    </section>
  );
}
