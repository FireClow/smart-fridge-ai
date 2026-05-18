import { useCallback, useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext.jsx";
import { fetchInventory } from "../services/api.js";
import { subscribeInventory, supabase } from "../services/supabase.js";

export function useInventory() {
  const { user } = useAuth();
  const userId = user?.id ?? null;
  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [online, setOnline] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchInventory();
      setInventory(Array.isArray(data) ? data : []);
      setOnline(true);
    } catch {
      setInventory([]);
      setOnline(false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
    if (!supabase) return undefined;
    const unsub = subscribeInventory(() => {
      void load();
    }, userId);
    return unsub;
  }, [load, userId]);

  return { inventory, loading, online, reload: load };
}
