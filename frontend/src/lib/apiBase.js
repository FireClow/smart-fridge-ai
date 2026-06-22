/**
 * API origin for Axios/fetch. Empty string = same origin (`/api/*` on the current host).
 * Strips a trailing `/api` from VITE_API_URL so `/api/scan/image` is never doubled.
 */
export function normalizeApiOrigin(value) {
  let raw = String(value ?? "").trim().replace(/\/+$/, "");
  if (!raw) return "";
  if (raw.toLowerCase().endsWith("/api")) {
    raw = raw.slice(0, -4).replace(/\/+$/, "");
  }
  return raw;
}

export function getApiOrigin() {
  const raw = normalizeApiOrigin(import.meta.env.VITE_API_URL);
  if (!raw) {
    // Dev: Vite proxies /api → FastAPI (local :8001, Replit :8000).
    // Replit deploy / same-origin: relative /api/* on one host.
    // Vercel-only frontend: set VITE_API_URL to external API (Render, Railway, etc.).
    return "";
  }
  return raw;
}

/** @param {string} path e.g. `/api/inventory` */
export function apiUrl(path) {
  const p = path.startsWith("/") ? path : `/${path}`;
  const origin = getApiOrigin();
  if (!origin) return p;
  return `${origin}${p}`;
}
