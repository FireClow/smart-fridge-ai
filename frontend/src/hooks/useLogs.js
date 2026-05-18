import { useCallback, useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext.jsx";
import { fetchLogs } from "../services/api.js";
import { subscribeLogs, supabase } from "../services/supabase.js";

export function useLogs(limit = 20) {
  const { user } = useAuth();
  const userId = user?.id ?? null;
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
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
    if (!supabase) return undefined;
    const unsub = subscribeLogs(() => {
      void load();
    }, userId);
    return unsub;
  }, [load, userId]);

  return { logs, loading, reload: load };
}
