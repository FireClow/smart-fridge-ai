/**
 * API origin for fetch(). In Vite dev, empty string = same origin so /api/* is proxied to FastAPI.
 * Strips a trailing `/api` from VITE_API_URL so paths like `/api/scan/image` are not doubled.
 */
export function getApiOrigin() {
  let raw = (import.meta.env.VITE_API_URL ?? "").trim().replace(/\/+$/, "");
  if (raw.toLowerCase().endsWith("/api")) {
    raw = raw.slice(0, -4).replace(/\/+$/, "");
  }
  if (!raw) {
    // Dev: Vite proxies /api → FastAPI (local :8001, Replit :8000).
    // Replit deploy / same-origin: empty origin → relative /api/* on one host.
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
