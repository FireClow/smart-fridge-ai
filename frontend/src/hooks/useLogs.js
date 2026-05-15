import { useCallback, useEffect, useState } from "react";
import { dummyLogs } from "../data/dummyData.js";
import { fetchLogs } from "../services/api.js";
import { subscribeLogs, supabase } from "../services/supabase.js";

const useDummy = import.meta.env.VITE_USE_DUMMY === "true";

export function useLogs(limit = 20) {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (useDummy) {
      setLogs(dummyLogs);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const data = await fetchLogs(limit);
      setLogs(Array.isArray(data) ? data : []);
    } catch {
      setLogs([]);
    } finally {
      setLoading(false);
    }
  }, [limit]);

  useEffect(() => {
    void load();
    if (useDummy) return undefined;
    if (!supabase) return undefined;
    const unsub = subscribeLogs(() => {
      void load();
    });
    return unsub;
  }, [load]);

  return { logs, loading, reload: load };
}
