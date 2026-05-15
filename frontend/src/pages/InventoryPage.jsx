import { useMemo } from "react";
import { InventoryCard } from "../components/InventoryCard.jsx";
import { useInventory } from "../hooks/useInventory.js";
import { useLogs } from "../hooks/useLogs.js";

function latestConfidenceByItem(logs) {
  const map = {};
  for (const log of [...(logs || [])].sort(
    (a, b) => new Date(b.detected_at) - new Date(a.detected_at),
  )) {
    if (log.item_name != null && map[log.item_name] === undefined) {
      map[log.item_name] = log.confidence;
    }
  }
  return map;
}

export function InventoryPage() {
  const { inventory, loading, reload } = useInventory();
  const { logs } = useLogs(100);
  const confMap = useMemo(() => latestConfidenceByItem(logs), [logs]);

  return (
    <div>
      <h1 className="font-display text-2xl font-bold text-white">Inventory</h1>
      <p className="mt-1 text-sm text-gray-500">All items in your smart fridge</p>

      {loading ? (
        <p className="mt-8 text-sm text-gray-400">Loading inventory…</p>
      ) : !inventory?.length ? (
        <div className="mt-8 rounded-2xl border border-dashed border-gray-700 py-16 text-center text-gray-500">
          No items yet. Run a scan from the dashboard.
        </div>
      ) : (
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {inventory.map((item) => (
            <InventoryCard
              key={item.id ?? item.item_name}
              item={item}
              confidence={confMap[item.item_name] ?? null}
              onSaved={() => void reload()}
            />
          ))}
        </div>
      )}
    </div>
  );
}
