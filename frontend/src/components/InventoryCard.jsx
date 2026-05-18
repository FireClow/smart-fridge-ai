import { useState } from "react";
import {
  daysUntilExpiry,
  expiryTone,
  foodEmoji,
  formatDateTime,
  formatTime,
  toDateTimeLocalValue,
} from "../lib/format.js";
import { patchInventoryExpiry } from "../services/api.js";

const toneClass = {
  expired: "border-red-500/40 bg-red-500/15 text-red-200",
  critical: "border-red-500/30 bg-red-500/10 text-red-100",
  warn: "border-amber-500/40 bg-amber-500/10 text-amber-100",
  ok: "border-emerald-500/30 bg-emerald-500/10 text-emerald-100",
  neutral: "border-gray-600 bg-gray-800/60 text-gray-300",
};

function expiryLabel(days) {
  if (days == null) return "No expiry set";
  if (days < 0) return `Expired ${Math.abs(days)}d ago`;
  if (days === 0) return "Expires today";
  if (days === 1) return "1 day left";
  return `${days} days left`;
}

export function InventoryCard({ item, confidence, onSaved }) {
  const pct =
    confidence != null && !Number.isNaN(confidence)
      ? Math.round(Number(confidence) * 100)
      : null;

  const days = daysUntilExpiry(item.expires_at);
  const tone = expiryTone(days);
  const badgeClass = toneClass[tone] ?? toneClass.neutral;

  const [open, setOpen] = useState(false);
  const [localExpiry, setLocalExpiry] = useState(toDateTimeLocalValue(item.expires_at));
  const [locked, setLocked] = useState(Boolean(item.expiry_locked));
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState(null);

  const openModal = () => {
    setLocalExpiry(toDateTimeLocalValue(item.expires_at));
    setLocked(Boolean(item.expiry_locked));
    setErr(null);
    setOpen(true);
  };

  const saveExpiry = async () => {
    setSaving(true);
    setErr(null);
    try {
      const iso = new Date(localExpiry).toISOString();
      await patchInventoryExpiry(item.item_name, {
        expires_at: iso,
        expiry_locked: locked,
      });
      setOpen(false);
      onSaved?.();
    } catch (e) {
      setErr(e?.message || "Save failed");
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <article className="group relative overflow-hidden rounded-2xl border border-gray-800 bg-gradient-to-b from-gray-900/90 to-gray-950/90 p-5 shadow-lg transition duration-300 hover:-translate-y-0.5 hover:border-cyan-500/50 hover:shadow-glow">
        <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent opacity-0 transition group-hover:opacity-100" />
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <span className="text-3xl drop-shadow-md" aria-hidden>
              {foodEmoji(item.item_name)}
            </span>
            <div>
              <h3 className="font-display text-lg font-semibold capitalize text-white">
                {String(item.item_name || "").replace(/_/g, " ")}
              </h3>
              <p className="text-xs text-gray-500">Last update</p>
              <p className="text-sm text-cyan-300/90">{formatTime(item.updated_at)}</p>
            </div>
          </div>
          <span className="rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3 py-1 text-sm font-bold text-cyan-200">
            ×{item.quantity ?? 0}
          </span>
        </div>

        <div className={`mt-3 rounded-xl border px-3 py-2 text-xs ${badgeClass}`}>
          <p className="font-medium">{expiryLabel(days)}</p>
          <p className="mt-0.5 text-[11px] opacity-90">
            {item.expires_at ? formatDateTime(item.expires_at) : "—"}
            {item.expiry_locked ? " · locked" : ""}
          </p>
        </div>

        <div className="mt-4">
          <div className="mb-1 flex justify-between text-xs text-gray-400">
            <span>Confidence</span>
            <span>{pct != null ? `${pct}%` : "—"}</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-gray-800">
            <div
              className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-blue-500 transition-all duration-500"
              style={{ width: pct != null ? `${Math.min(pct, 100)}%` : "0%" }}
            />
          </div>
        </div>

        <button
          type="button"
          onClick={openModal}
          className="mt-4 w-full rounded-lg border border-gray-700 bg-gray-800/50 py-2 text-xs font-medium text-gray-200 hover:border-cyan-500/40 hover:bg-gray-800"
        >
          Set expiry
        </button>
      </article>

      {open ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="expiry-dialog-title"
          onClick={() => setOpen(false)}
        >
          <div
            className="w-full max-w-md rounded-2xl border border-gray-700 bg-gray-900 p-5 shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 id="expiry-dialog-title" className="font-display text-lg font-semibold text-white">
              Expiry — {String(item.item_name || "").replace(/_/g, " ")}
            </h2>
            <label className="mt-4 block text-xs text-gray-400" htmlFor="expiry-dt">
              Expires at (local)
            </label>
            <input
              id="expiry-dt"
              type="datetime-local"
              className="mt-1 w-full rounded-lg border border-gray-600 bg-gray-950 px-3 py-2 text-sm text-white"
              value={localExpiry}
              onChange={(e) => setLocalExpiry(e.target.value)}
            />
            <label className="mt-3 flex items-center gap-2 text-sm text-gray-300">
              <input
                type="checkbox"
                checked={locked}
                onChange={(e) => setLocked(e.target.checked)}
              />
              Lock date (scans won&apos;t overwrite expiry)
            </label>
            {err ? <p className="mt-2 text-xs text-red-400">{err}</p> : null}
            <div className="mt-5 flex justify-end gap-2">
              <button
                type="button"
                className="rounded-lg border border-gray-600 px-3 py-1.5 text-sm text-gray-300 hover:bg-gray-800"
                onClick={() => setOpen(false)}
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={saving || !localExpiry}
                className="rounded-lg border border-cyan-600/50 bg-cyan-600/25 px-3 py-1.5 text-sm font-medium text-cyan-100 hover:bg-cyan-600/35 disabled:opacity-40"
                onClick={() => void saveExpiry()}
              >
                {saving ? "Saving…" : "Save"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
