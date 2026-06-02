/**
 * API facade — uses Axios via http.js
 */
import { http, apiPath } from "./http.js";

export async function fetchInventory() {
  const { data } = await http.get(apiPath("/api/inventory"));
  return data;
}

export async function fetchLogs(limit = 20) {
  const { data } = await http.get(apiPath("/api/logs"), { params: { limit } });
  return data;
}

export async function fetchStats() {
  const { data } = await http.get(apiPath("/api/stats"));
  return data;
}

export async function fetchHealth() {
  const { data } = await http.get(apiPath("/api/health"));
  return data;
}

export async function fetchModelInfo() {
  const { data } = await http.get(apiPath("/api/model/info"));
  return data;
}

export async function postScanImage(file, confidence = 0.6, signal, preprocessMode = "none") {
  const form = new FormData();
  form.append("file", file, file.name || "capture.jpg");
  const { data } = await http.post(
    apiPath("/api/scan/image"),
    form,
    {
      params: { confidence, preprocess_mode: preprocessMode },
      headers: { "Content-Type": "multipart/form-data" },
      signal,
    },
  );
  return data;
}

export async function patchInventoryExpiry(itemName, body) {
  const enc = encodeURIComponent(itemName);
  const { data } = await http.patch(apiPath(`/api/inventory/${enc}`), body);
  return data;
}

export async function fetchNotifications(unreadOnly = false, limit = 50) {
  const { data } = await http.get(apiPath("/api/notifications"), {
    params: { unread_only: unreadOnly, limit },
  });
  return data;
}

export async function generateNotifications() {
  const { data } = await http.post(apiPath("/api/notifications/generate"));
  return data;
}

export async function markNotificationRead(id) {
  const { data } = await http.patch(apiPath(`/api/notifications/${id}/read`));
  return data;
}

/**
 * Stable per-browser session id so the backend can pair consecutive frames
 * for optical flow / tracking / events even when the user is not logged in.
 */
function cvSessionId() {
  let id = localStorage.getItem("sf-cv-session");
  if (!id) {
    id = `cv-${Math.random().toString(36).slice(2)}-${Date.now()}`;
    localStorage.setItem("sf-cv-session", id);
  }
  return id;
}

function cvHeaders(extra = {}) {
  return { "X-CV-Session": cvSessionId(), ...extra };
}

export async function cvAnalyze(file, preprocessMode = "none", signal) {
  const form = new FormData();
  form.append("file", file, file.name || "frame.jpg");
  const { data } = await http.post(apiPath("/api/cv/analyze"), form, {
    params: { preprocess_mode: preprocessMode },
    headers: cvHeaders({ "Content-Type": "multipart/form-data" }),
    signal,
  });
  return data;
}

export async function fetchCvMetrics() {
  const { data } = await http.get(apiPath("/api/cv/metrics"), {
    headers: cvHeaders(),
  });
  return data;
}

export async function cvMatch(file, className, signal) {
  const form = new FormData();
  form.append("file", file, file.name || "crop.jpg");
  const { data } = await http.post(apiPath("/api/cv/match"), form, {
    params: { class_name: className },
    headers: cvHeaders({ "Content-Type": "multipart/form-data" }),
    signal,
  });
  return data;
}

export async function cvHomography(file, className, warp = false, signal) {
  const form = new FormData();
  form.append("file", file, file.name || "crop.jpg");
  const { data } = await http.post(apiPath("/api/cv/homography"), form, {
    params: { class_name: className, warp },
    headers: cvHeaders({ "Content-Type": "multipart/form-data" }),
    signal,
  });
  return data;
}

export async function cvDetectEvents(file, confidence = 0.6, signal) {
  const form = new FormData();
  form.append("file", file, file.name || "frame.jpg");
  const { data } = await http.post(apiPath("/api/cv/events"), form, {
    params: { confidence },
    headers: cvHeaders({ "Content-Type": "multipart/form-data" }),
    signal,
  });
  return data;
}

export async function fetchCvEvents(limit = 50) {
  const { data } = await http.get(apiPath("/api/cv/events"), {
    params: { limit },
    headers: cvHeaders(),
  });
  return data;
}

export async function uploadReferenceImage(className, file) {
  const form = new FormData();
  form.append("file", file, file.name || "reference.jpg");
  const enc = encodeURIComponent(className);
  const { data } = await http.post(apiPath(`/api/cv/reference/${enc}`), form, {
    headers: cvHeaders({ "Content-Type": "multipart/form-data" }),
  });
  return data;
}

export async function fetchReferenceImage(className) {
  const enc = encodeURIComponent(className);
  const { data } = await http.get(apiPath(`/api/cv/reference/${enc}`), {
    headers: cvHeaders(),
  });
  return data;
}
