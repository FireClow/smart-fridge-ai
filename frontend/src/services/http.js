import axios from "axios";
import { apiUrl } from "../lib/apiBase.js";

export const http = axios.create({
  headers: { Accept: "application/json" },
});

http.interceptors.request.use((config) => {
  const token = localStorage.getItem("sb-access-token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

function isHtmlResponse(response) {
  const type = response?.headers?.["content-type"] ?? "";
  return typeof type === "string" && type.includes("text/html");
}

http.interceptors.response.use(
  (res) => res,
  (error) => {
    const status = error.response?.status;
    const data = error.response?.data;
    const isNetworkError = !error.response;
    let message = error.message;
    if (isNetworkError) {
      message =
        "Backend API tidak berjalan. Buka terminal baru di root project dan jalankan: .\\scripts\\start-api.ps1 (menunggu ~20 detik, port 8001).";
    } else if (isHtmlResponse(error.response)) {
      message =
        "API mengembalikan HTML, bukan JSON. Di Vercel set VITE_API_URL ke host FastAPI (Render/Railway). Di Replit biarkan kosong (same-origin /api).";
    }
    if (data?.detail) {
      message =
        typeof data.detail === "string"
          ? data.detail
          : JSON.stringify(data.detail);
    }
    if (status === 401) {
      localStorage.removeItem("sb-access-token");
      if (!window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(new Error(message));
  },
);

export function apiPath(path) {
  return apiUrl(path);
}
