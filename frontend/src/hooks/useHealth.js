import { useCallback, useEffect, useState } from "react";
import { fetchHealth } from "../services/api.js";

export function useHealth() {
  const [health, setHealth] = useState(null);
  const [online, setOnline] = useState(false);

  const load = useCallback(async () => {
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
    const id = setInterval(() => void load(), 30000);
    return () => clearInterval(id);
  }, [load]);

  return { health, online, reload: load };
}
