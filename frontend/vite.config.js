import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, "..");

/** Accept root .env (SUPABASE_*) or frontend VITE_* — matches Vercel env naming users often set. */
function resolveSupabaseEnv(mode) {
  const fromRoot = loadEnv(mode, rootDir, "");
  const fromFrontend = loadEnv(mode, __dirname, "");
  const env = { ...fromRoot, ...fromFrontend, ...process.env };

  const url = (env.VITE_SUPABASE_URL || env.SUPABASE_URL || "")
    .trim()
    .replace(/\/rest\/v1\/?$/i, "")
    .replace(/\/+$/, "");

  const key = (
    env.VITE_SUPABASE_KEY ||
    env.VITE_SUPABASE_ANON_KEY ||
    env.SUPABASE_KEY ||
    ""
  ).trim();

  return { url, key };
}

export default defineConfig(({ mode }) => {
  const { url: supabaseUrl, key: supabaseKey } = resolveSupabaseEnv(mode);
  const apiPort = process.env.API_PORT || "8001";
  const devPort = process.env.REPL_ID ? 5000 : 5173;

  return {
    plugins: [react()],
    envDir: rootDir,
    define: {
      "import.meta.env.VITE_SUPABASE_URL": JSON.stringify(supabaseUrl),
      "import.meta.env.VITE_SUPABASE_KEY": JSON.stringify(supabaseKey),
    },
    server: {
      port: Number(devPort),
      host: process.env.REPL_ID ? "0.0.0.0" : undefined,
      strictPort: true,
      proxy: {
        "/api": {
          target: `http://127.0.0.1:${apiPort}`,
          changeOrigin: true,
        },
      },
    },
  };
});
