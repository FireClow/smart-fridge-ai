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
