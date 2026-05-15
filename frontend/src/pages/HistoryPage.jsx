import { ActivityLog } from "../components/ActivityLog.jsx";
import { useLogs } from "../hooks/useLogs.js";

export function HistoryPage() {
  const { logs, loading, reload } = useLogs(100);

  return (
    <div>
      <div className="mb-6 flex items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl font-bold text-white">Detection history</h1>
          <p className="mt-1 text-sm text-gray-500">Recent YOLO detection events</p>
        </div>
        <button
          type="button"
          onClick={() => void reload()}
          className="rounded-lg border border-gray-600 px-3 py-1.5 text-xs text-gray-300 hover:bg-gray-800"
        >
          Refresh
        </button>
      </div>
      <ActivityLog logs={logs} loading={loading} />
    </div>
  );
}
