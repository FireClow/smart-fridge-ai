import { useCallback, useEffect, useState } from "react";
import { fetchHealth } from "../services/api.js";

const useDummy = import.meta.env.VITE_USE_DUMMY === "true";

export function useHealth() {
  const [health, setHealth] = useState(null);
  const [online, setOnline] = useState(useDummy);

  const load = useCallback(async () => {
    if (useDummy) {
      setHealth({ status: "ok", yolo_loaded: true, supabase_configured: true });
      setOnline(true);
      return;
    }
    try {
      const data = await fetchHealth();
      // #region agent log
      fetch("http://127.0.0.1:7473/ingest/ab1a7fbe-0ea8-4c96-b77b-f5a196c26570", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "51eb5f" },
        body: JSON.stringify({
          sessionId: "51eb5f",
          location: "useHealth.js:load",
          message: "health fetched",
          data: {
            status: data?.status,
            yolo_loaded: data?.yolo_loaded,
            has_yolo_loaded_key: data != null && "yolo_loaded" in data,
          },
          timestamp: Date.now(),
          hypothesisId: "D",
        }),
      }).catch(() => {});
      // #endregion
      setHealth(data);
      setOnline(data?.status === "ok");
    } catch {
      setHealth(null);
      setOnline(false);
    }
  }, []);

  useEffect(() => {
    void load();
    if (useDummy) return undefined;
    const id = setInterval(() => void load(), 30000);
    return () => clearInterval(id);
  }, [load]);

  return { health, online, reload: load };
}
