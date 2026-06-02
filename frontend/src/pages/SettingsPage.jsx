import { useAuth } from "../context/AuthContext.jsx";
import { PREPROCESS_MODES, useSettings } from "../context/SettingsContext.jsx";
import { fetchHealth, fetchModelInfo } from "../services/api.js";
import { useEffect, useState } from "react";

const PREPROCESS_LABELS = {
  none: "None (raw frame)",
  gaussian: "Gaussian Blur (denoise)",
  bilateral: "Bilateral (edge-preserving)",
  clahe: "CLAHE (contrast enhance)",
};

export function SettingsPage() {
  const { user, signOut } = useAuth();
  const {
    confidence,
    setConfidence,
    defaultAutoScan,
    setDefaultAutoScan,
    preprocessMode,
    setPreprocessMode,
  } = useSettings();
  const [health, setHealth] = useState(null);
  const [modelInfo, setModelInfo] = useState(null);

  useEffect(() => {
    void (async () => {
      try {
        const [h, m] = await Promise.all([fetchHealth(), fetchModelInfo()]);
        setHealth(h);
        setModelInfo(m);
      } catch {
        /* ignore */
      }
    })();
  }, []);

  return (
    <div className="max-w-lg space-y-8">
      <div>
        <h1 className="font-display text-2xl font-bold text-white">Settings</h1>
        <p className="mt-1 text-sm text-gray-500">Detection and account preferences</p>
      </div>

      <section className="rounded-xl border border-gray-800 bg-gray-900/50 p-5">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-400">
          Detection
        </h2>
        <label className="mt-4 block text-sm text-gray-300">
          Confidence threshold ({confidence.toFixed(2)})
          <input
            type="range"
            min="0.05"
            max="0.99"
            step="0.05"
            value={confidence}
            onChange={(e) => setConfidence(Number(e.target.value))}
            className="mt-2 w-full accent-cyan-500"
          />
        </label>
        <label className="mt-4 flex items-center gap-2 text-sm text-gray-300">
          <input
            type="checkbox"
            checked={defaultAutoScan}
            onChange={(e) => setDefaultAutoScan(e.target.checked)}
          />
          Enable auto-scan by default (3s interval)
        </label>

        <label className="mt-4 block text-sm text-gray-300">
          Preprocessing filter (before YOLO)
          <select
            value={preprocessMode}
            onChange={(e) => setPreprocessMode(e.target.value)}
            className="mt-2 w-full rounded-lg border border-gray-700 bg-gray-950 px-3 py-2 text-sm text-white"
          >
            {PREPROCESS_MODES.map((m) => (
              <option key={m} value={m}>
                {PREPROCESS_LABELS[m] ?? m}
              </option>
            ))}
          </select>
          <span className="mt-1 block text-xs text-gray-500">
            Image Filtering &amp; Enhancement applied to each frame before detection.
          </span>
        </label>
      </section>

      <section className="rounded-xl border border-gray-800 bg-gray-900/50 p-5 text-sm text-gray-400">
        <h2 className="font-semibold uppercase tracking-wider text-gray-400">System</h2>
        <p className="mt-2">
          API: {health?.status ?? "unknown"} · YOLO:{" "}
          {health?.yolo_loaded ? "loaded" : "not loaded"}
        </p>
        {modelInfo?.loaded ? (
          <p className="mt-1">Classes: {modelInfo.num_classes}</p>
        ) : null}
        {health?.model_path ? (
          <p className="mt-1 break-all text-xs text-gray-500">{health.model_path}</p>
        ) : null}
      </section>

      {user ? (
        <section className="rounded-xl border border-gray-800 bg-gray-900/50 p-5">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-400">
            Account
          </h2>
          <p className="mt-2 text-sm text-gray-300">{user.email}</p>
          <button
            type="button"
            onClick={() => void signOut()}
            className="mt-4 rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-2 text-sm text-red-300 hover:bg-red-500/20"
          >
            Sign out
          </button>
        </section>
      ) : null}
    </div>
  );
}
