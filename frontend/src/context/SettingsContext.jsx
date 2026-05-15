import { createContext, useContext, useMemo, useState } from "react";

const SettingsContext = createContext(null);

const CONF_KEY = "sf-confidence";
const AUTO_KEY = "sf-auto-scan";

function readNum(key, fallback) {
  const v = localStorage.getItem(key);
  if (v == null) return fallback;
  const n = Number(v);
  return Number.isFinite(n) ? n : fallback;
}

export function SettingsProvider({ children }) {
  const [confidence, setConfidenceState] = useState(() => readNum(CONF_KEY, 0.6));
  const [defaultAutoScan, setDefaultAutoScanState] = useState(
    () => localStorage.getItem(AUTO_KEY) === "true",
  );

  const setConfidence = (v) => {
    setConfidenceState(v);
    localStorage.setItem(CONF_KEY, String(v));
  };

  const setDefaultAutoScan = (v) => {
    setDefaultAutoScanState(v);
    localStorage.setItem(AUTO_KEY, v ? "true" : "false");
  };

  const value = useMemo(
    () => ({
      confidence,
      setConfidence,
      defaultAutoScan,
      setDefaultAutoScan,
    }),
    [confidence, defaultAutoScan],
  );

  return (
    <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>
  );
}

export function useSettings() {
  const ctx = useContext(SettingsContext);
  if (!ctx) throw new Error("useSettings must be used within SettingsProvider");
  return ctx;
}
