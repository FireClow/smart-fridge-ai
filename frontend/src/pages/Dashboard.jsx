import { useCallback, useEffect, useMemo, useState } from "react";
import { ActivityLog } from "../components/ActivityLog.jsx";
import { CameraFeed } from "../components/CameraFeed.jsx";
import { ExpiryAlerts } from "../components/ExpiryAlerts.jsx";
import { InventoryCard } from "../components/InventoryCard.jsx";
import { StatsCard } from "../components/StatsCard.jsx";
import { useInventory } from "../hooks/useInventory.js";
import { useLogs } from "../hooks/useLogs.js";
import { useNotifications } from "../hooks/useNotifications.js";
import { fetchStats } from "../services/api.js";

const emptyStats = {
  total_items: 0,
  total_categories: 0,
  avg_confidence: null,
  last_detected: null,
  fps_hint: null,
  expiring_soon_count: 0,
};

function latestConfidenceByItem(logs) {
  const map = {};
  const sorted = [...(logs || [])].sort(
    (a, b) => new Date(b.detected_at) - new Date(a.detected_at),
  );
  for (const log of sorted) {
    const name = log.item_name;
    if (name != null && map[name] === undefined) {
      map[name] = log.confidence;
    }
  }
  return map;
}

export function Dashboard() {
  const { inventory, loading: invLoading, reload: reloadInventory } = useInventory();
  const { logs, loading: logLoading, reload: reloadLogs } = useLogs(25);
  const {
    notifications,
    loading: notifLoading,
    reload: reloadNotifications,
  } = useNotifications(true, 10);
  const [stats, setStats] = useState(emptyStats);
  const [statsLoading, setStatsLoading] = useState(true);
  const [lastFps, setLastFps] = useState(null);

  const loadStats = useCallback(async () => {
    try {
      const s = await fetchStats();
      setStats(s);
    } catch {
      setStats(emptyStats);
    } finally {
      setStatsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadStats();
  }, [loadStats]);

  useEffect(() => {
    void loadStats();
  }, [inventory, logs, loadStats]);

  const onScanComplete = useCallback(
    (data) => {
      if (data?.fps != null) setLastFps(data.fps);
      void reloadInventory();
      void reloadLogs();
      void loadStats();
      void reloadNotifications();
    },
    [reloadInventory, reloadLogs, loadStats, reloadNotifications],
  );

  const confMap = useMemo(() => latestConfidenceByItem(logs), [logs]);
  const displayFps = lastFps ?? stats?.fps_hint;

  const avgPct =
    stats?.avg_confidence != null
      ? Math.round(Number(stats.avg_confidence) * 100)
      : null;

  return (
    <>
      <section className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        <StatsCard
          label="Total items"
          value={statsLoading ? "…" : stats?.total_items ?? "—"}
          sub="Sum of quantities in fridge"
        />
        <StatsCard
          label="Categories"
          value={statsLoading ? "…" : stats?.total_categories ?? "—"}
          sub="Distinct food classes"
          accent="blue"
        />
        <StatsCard
          label="Avg confidence"
          value={avgPct != null ? `${avgPct}%` : "—"}
          sub="From recent detection logs"
          accent="violet"
        />
        <StatsCard
          label="Expiring ≤3d"
          value={statsLoading ? "…" : stats?.expiring_soon_count ?? "—"}
          sub="Rows with expires_at in window"
        />
        <StatsCard
          label="Pipeline FPS"
          value={displayFps != null ? Number(displayFps).toFixed(1) : "—"}
          sub="Measured YOLO inference throughput"
        />
      </section>

      <section className="mb-8">
        <h2 className="mb-3 font-display text-lg font-semibold text-white">Expiration alerts</h2>
        <ExpiryAlerts notifications={notifications} loading={notifLoading} />
      </section>

      <section className="mb-10 grid gap-6 lg:grid-cols-5">
        <div className="lg:col-span-3">
          <CameraFeed onScanComplete={onScanComplete} />
        </div>
        <div className="lg:col-span-2">
          <ActivityLog logs={logs} loading={logLoading} />
        </div>
      </section>

      <section>
        <div className="mb-4 flex items-end justify-between gap-4">
          <div>
            <h2 className="font-display text-lg font-semibold text-white">Live inventory</h2>
            <p className="text-sm text-gray-500">Updates via Supabase Realtime</p>
          </div>
          {invLoading ? (
            <span className="text-xs font-medium uppercase tracking-wider text-cyan-400/80">
              Loading…
            </span>
          ) : null}
        </div>

        {!invLoading && (!inventory || inventory.length === 0) ? (
          <div className="rounded-2xl border border-dashed border-gray-700 bg-gray-900/40 py-16 text-center">
            <p className="text-gray-400">Inventory is empty.</p>
            <p className="mt-2 text-sm text-gray-500">Use Scan now or upload a photo above.</p>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {(inventory || []).map((item) => (
              <InventoryCard
                key={item.id ?? item.item_name}
                item={item}
                confidence={confMap[item.item_name] ?? null}
                onSaved={() => void reloadInventory()}
              />
            ))}
          </div>
        )}
      </section>
    </>
  );
}
