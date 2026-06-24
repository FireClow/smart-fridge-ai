import { Outlet } from "react-router-dom";
import { AppNav } from "../components/AppNav.jsx";
import { useHealth } from "../hooks/useHealth.js";
import { getApiOrigin, usesLocalApiProxy } from "../lib/apiBase.js";

export function AppLayout() {
  const { online, health } = useHealth();
  const apiDown = !online && health == null;

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <AppNav online={online} yoloLoaded={health?.yolo_loaded} apiDown={apiDown} />
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {apiDown ? (
          <div className="mb-6 rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
            {usesLocalApiProxy() ? (
              <>
                Backend API tidak berjalan. Dari root project jalankan{" "}
                <code className="text-rose-100">.\scripts\dev.ps1</code> (API + frontend) atau{" "}
                <code className="text-rose-100">.\scripts\start-api.ps1</code>, tunggu pesan
                &quot;Application startup complete&quot; (~20 detik, port{" "}
                <code className="text-rose-100">8001</code>), lalu refresh.
              </>
            ) : (
              <>
                Tidak dapat menghubungi API di{" "}
                <code className="text-rose-100">{getApiOrigin()}</code>. Untuk dev lokal, kosongkan{" "}
                <code className="text-rose-100">VITE_API_URL</code> di{" "}
                <code className="text-rose-100">frontend/.env</code> dan jalankan API lokal. Untuk
                production, set variabel Railway: <code className="text-rose-100">SUPABASE_URL</code>,{" "}
                <code className="text-rose-100">SUPABASE_KEY</code>, dan{" "}
                <code className="text-rose-100">ALLOWED_ORIGINS</code>.
              </>
            )}
          </div>
        ) : null}
        {health?.status === "ok" && health.supabase_configured === false ? (
          <div className="mb-6 rounded-xl border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
            API aktif tetapi Supabase belum dikonfigurasi di server (
            {usesLocalApiProxy() ? "root .env" : getApiOrigin()}). Isi{" "}
            <code className="text-amber-100">SUPABASE_URL</code> dan{" "}
            <code className="text-amber-100">SUPABASE_KEY</code>
            {usesLocalApiProxy() ? (
              <> di root <code className="text-amber-100">.env</code></>
            ) : (
              <> di Railway Variables</>
            )}
            , lalu restart API.
          </div>
        ) : null}
        {health?.status === "ok" && !("yolo_loaded" in health) ? (
          <div className="mb-6 rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
            Outdated API detected — stop old servers and run{" "}
            <code className="text-rose-100">.\scripts\start-api.ps1</code> (port{" "}
            <code className="text-rose-100">8001</code>), then restart{" "}
            <code className="text-rose-100">npm run dev</code> in{" "}
            <code className="text-rose-100">frontend</code>.
          </div>
        ) : null}
        {health && health.yolo_loaded === false ? (
          <div className="mb-6 rounded-xl border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
            YOLO model not loaded
            {health.model_exists ? (
              <>
                {" "}
                — restart the API from the project root so it loads{" "}
                <code className="text-amber-100">{health.model_path}</code>.
              </>
            ) : (
              <>
                {" "}
                — set <code className="text-amber-100">MODEL_PATH</code> in root{" "}
                <code className="text-amber-100">.env</code> to your trained{" "}
                <code className="text-amber-100">best.pt</code> and restart the API.
              </>
            )}
            {health.yolo_load_error ? (
              <span className="mt-1 block text-xs text-amber-200/80">{health.yolo_load_error}</span>
            ) : null}
          </div>
        ) : null}
        <Outlet />
      </main>
      <footer className="border-t border-gray-800/80 py-6 text-center text-xs text-gray-600">
        Smart Refrigerator · Computer Vision · {new Date().getFullYear()}
      </footer>
    </div>
  );
}
