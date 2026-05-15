import { useCallback, useEffect, useState } from "react";
import { dummyInventory } from "../data/dummyData.js";
import { fetchInventory } from "../services/api.js";
import { subscribeInventory, supabase } from "../services/supabase.js";

const useDummy = import.meta.env.VITE_USE_DUMMY === "true";

export function useInventory() {
  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [online, setOnline] = useState(false);

  const load = useCallback(async () => {
    if (useDummy) {
      setInventory(dummyInventory);
      setOnline(true);
      setLoading(false);
      return;
    }
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
    if (useDummy) return undefined;
    if (!supabase) return undefined;
    const unsub = subscribeInventory(() => {
      void load();
    });
    return unsub;
  }, [load]);

  return { inventory, loading, online, reload: load };
}
