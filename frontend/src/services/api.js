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

export async function postScanImage(file, confidence = 0.6, signal) {
  const form = new FormData();
  form.append("file", file, file.name || "capture.jpg");
  const { data } = await http.post(
    apiPath("/api/scan/image"),
    form,
    {
      params: { confidence },
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
