/**
 * Course topics: Harris Corner Detection + Shi-Tomasi Good Features To Track
 * (with Non-Maximum Suppression inside the backend corners module).
 * Red = Harris, Green = Shi-Tomasi.
 */
export function CornerPanel({ image, harrisCount, shiTomasiCount }) {
  return (
    <section className="rounded-2xl border border-gray-800 bg-gray-900/50 p-4">
      <h3 className="mb-3 font-display text-sm font-semibold text-white">
        Corner detection (Harris vs Shi-Tomasi)
      </h3>
      {image ? (
        <img
          src={`data:image/jpeg;base64,${image}`}
          alt="Detected corners"
          className="w-full rounded-lg border border-gray-800 object-contain"
        />
      ) : (
        <div className="flex h-40 items-center justify-center rounded-lg border border-dashed border-gray-700 text-xs text-gray-500">
          Waiting for frame…
        </div>
      )}
      <table className="mt-3 w-full text-sm">
        <thead>
          <tr className="text-left text-xs uppercase tracking-wider text-gray-500">
            <th className="py-1">Method</th>
            <th className="py-1 text-right">Corner count</th>
          </tr>
        </thead>
        <tbody className="text-gray-300">
          <tr className="border-t border-gray-800">
            <td className="py-1.5">
              <span className="mr-2 inline-block h-2 w-2 rounded-full bg-red-500" />
              Harris
            </td>
            <td className="py-1.5 text-right tabular-nums">{harrisCount ?? "—"}</td>
          </tr>
          <tr className="border-t border-gray-800">
            <td className="py-1.5">
              <span className="mr-2 inline-block h-2 w-2 rounded-full bg-green-500" />
              Shi-Tomasi
            </td>
            <td className="py-1.5 text-right tabular-nums">{shiTomasiCount ?? "—"}</td>
          </tr>
        </tbody>
      </table>
    </section>
  );
}
