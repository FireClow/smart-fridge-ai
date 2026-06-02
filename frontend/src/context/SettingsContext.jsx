import { createContext, useContext, useMemo, useState } from "react";

const SettingsContext = createContext(null);

const CONF_KEY = "sf-confidence";
const AUTO_KEY = "sf-auto-scan";
const PREPROCESS_KEY = "sf-preprocess-mode";

export const PREPROCESS_MODES = ["none", "gaussian", "bilateral", "clahe"];

function readNum(key, fallback) {
  const v = localStorage.getItem(key);
  if (v == null) return fallback;
  const n = Number(v);
  return Number.isFinite(n) ? n : fallback;
}

function readPreprocess() {
  const v = localStorage.getItem(PREPROCESS_KEY);
  return PREPROCESS_MODES.includes(v) ? v : "none";
}

export function SettingsProvider({ children }) {
  const [confidence, setConfidenceState] = useState(() => readNum(CONF_KEY, 0.6));
  const [defaultAutoScan, setDefaultAutoScanState] = useState(
    () => localStorage.getItem(AUTO_KEY) === "true",
  );
  const [preprocessMode, setPreprocessModeState] = useState(readPreprocess);

  const setConfidence = (v) => {
    setConfidenceState(v);
    localStorage.setItem(CONF_KEY, String(v));
  };

  const setDefaultAutoScan = (v) => {
    setDefaultAutoScanState(v);
    localStorage.setItem(AUTO_KEY, v ? "true" : "false");
  };

  const setPreprocessMode = (v) => {
    const mode = PREPROCESS_MODES.includes(v) ? v : "none";
    setPreprocessModeState(mode);
    localStorage.setItem(PREPROCESS_KEY, mode);
  };

  const value = useMemo(
    () => ({
      confidence,
      setConfidence,
      defaultAutoScan,
      setDefaultAutoScan,
      preprocessMode,
      setPreprocessMode,
    }),
    [confidence, defaultAutoScan, preprocessMode],
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
