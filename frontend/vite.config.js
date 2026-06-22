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

/** Same-origin /api on Replit deploy; external host on Vercel + Render split. */
function resolveApiEnv(mode) {
  const fromRoot = loadEnv(mode, rootDir, "");
  const fromFrontend = loadEnv(mode, __dirname, "");
  const env = { ...fromRoot, ...fromFrontend, ...process.env };

  if (
    process.env.REPLIT_DEPLOYMENT ||
    process.env.REPL_ID ||
    env.REPLIT_DEPLOYMENT
  ) {
    return "";
  }

  let url = (env.VITE_API_URL || env.API_URL || "").trim().replace(/\/+$/, "");
  if (url.toLowerCase().endsWith("/api")) {
    url = url.slice(0, -4).replace(/\/+$/, "");
  }
  return url;
}

export default defineConfig(({ mode }) => {
  const { url: supabaseUrl, key: supabaseKey } = resolveSupabaseEnv(mode);
  const apiOrigin = resolveApiEnv(mode);
  const apiPort = process.env.API_PORT || "8001";
  const devPort = process.env.REPL_ID ? 5000 : 5173;

  return {
    plugins: [react()],
    envDir: rootDir,
    define: {
      "import.meta.env.VITE_SUPABASE_URL": JSON.stringify(supabaseUrl),
      "import.meta.env.VITE_SUPABASE_KEY": JSON.stringify(supabaseKey),
      "import.meta.env.VITE_API_URL": JSON.stringify(apiOrigin),
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
