import { useCallback, useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext.jsx";
import { fetchNotifications, generateNotifications } from "../services/api.js";
import { subscribeNotifications, supabase } from "../services/supabase.js";

export function useNotifications(unreadOnly = false, limit = 50) {
  const { user } = useAuth();
  const userId = user?.id ?? null;
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      await generateNotifications().catch(() => {});
      const data = await fetchNotifications(unreadOnly, limit);
      setNotifications(Array.isArray(data) ? data : []);
    } catch {
      setNotifications([]);
    } finally {
      setLoading(false);
    }
  }, [unreadOnly, limit]);

  useEffect(() => {
    void load();
    if (!supabase) return undefined;
    const unsub = subscribeNotifications(() => {
      void load();
    }, userId);
    return unsub;
  }, [load, userId]);

  return { notifications, loading, reload: load };
}
