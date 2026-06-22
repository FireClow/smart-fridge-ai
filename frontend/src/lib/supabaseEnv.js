/** Resolve Supabase URL + browser key from Vite-injected env (see vite.config.js). */
export function getSupabaseConfig() {
  const url = (import.meta.env.VITE_SUPABASE_URL || "")
    .trim()
    .replace(/\/rest\/v1\/?$/i, "")
    .replace(/\/+$/, "");

  const key = (
    import.meta.env.VITE_SUPABASE_KEY ||
    import.meta.env.VITE_SUPABASE_ANON_KEY ||
    ""
  ).trim();

  return { url, key };
}

export function isSupabaseConfigured() {
  const { url, key } = getSupabaseConfig();
  if (!url || !key) return false;
  if (url.includes("your-project")) return false;
  if (key.includes("your-anon") || key.includes("your-publishable")) return false;
  return true;
}

export const SUPABASE_CONFIG_HINT =
  "Set VITE_SUPABASE_URL + VITE_SUPABASE_KEY on Vercel (or SUPABASE_URL + SUPABASE_KEY), then redeploy.";
