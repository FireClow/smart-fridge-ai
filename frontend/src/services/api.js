/**
 * API facade — uses Axios via http.js
 */
import { API } from "../lib/apiRoutes.js";
import { http, apiPath } from "./http.js";

export async function fetchInventory() {
  const { data } = await http.get(apiPath(API.inventory));
  return data;
}

export async function fetchLogs(limit = 20) {
  const { data } = await http.get(apiPath(API.logs), { params: { limit } });
  return data;
}

export async function fetchStats() {
  const { data } = await http.get(apiPath(API.stats));
  return data;
}

export async function fetchHealth() {
  const { data } = await http.get(apiPath(API.health));
  return data;
}

export async function fetchModelInfo() {
  const { data } = await http.get(apiPath(API.modelInfo));
  return data;
}

export async function postScanImage(file, confidence = 0.6, signal, preprocessMode = "none") {
  const form = new FormData();
  form.append("file", file, file.name || "capture.jpg");
  const { data } = await http.post(
    apiPath(API.scanImage),
    form,
    {
      params: { confidence, preprocess_mode: preprocessMode },
      signal,
    },
  );
  return data;
}

export async function patchInventoryExpiry(itemName, body) {
  const { data } = await http.patch(apiPath(API.inventoryItem(itemName)), body);
  return data;
}

export async function fetchNotifications(unreadOnly = false, limit = 50) {
  const { data } = await http.get(apiPath(API.notifications), {
    params: { unread_only: unreadOnly, limit },
  });
  return data;
}

export async function generateNotifications() {
  const { data } = await http.post(apiPath(API.notificationsGenerate));
  return data;
}

export async function markNotificationRead(id) {
  const { data } = await http.patch(apiPath(API.notificationRead(id)));
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

function multipartConfig(extra = {}) {
  return {
    headers: cvHeaders(extra),
    // Let axios/browser set multipart boundary; do not set Content-Type manually.
  };
}

export async function cvAnalyze(file, preprocessMode = "none", signal, sourceMode = "webcam") {
  const form = new FormData();
  form.append("file", file, file.name || "frame.jpg");
  const { data } = await http.post(apiPath(API.cvAnalyze), form, {
    params: { preprocess_mode: preprocessMode, source_mode: sourceMode },
    ...multipartConfig(),
    signal,
  });
  return data;
}

export async function fetchCvMetrics() {
  const { data } = await http.get(apiPath(API.cvMetrics), {
    headers: cvHeaders(),
  });
  return data;
}

export async function cvReset() {
  const { data } = await http.post(apiPath(API.cvReset), null, {
    headers: cvHeaders(),
  });
  return data;
}

export async function cvMatch(file, className, signal) {
  const form = new FormData();
  form.append("file", file, file.name || "crop.jpg");
  const { data } = await http.post(apiPath(API.cvMatch), form, {
    params: { class_name: className },
    ...multipartConfig(),
    signal,
  });
  return data;
}

export async function cvHomography(file, className, warp = false, signal) {
  const form = new FormData();
  form.append("file", file, file.name || "crop.jpg");
  const { data } = await http.post(apiPath(API.cvHomography), form, {
    params: { class_name: className, warp },
    ...multipartConfig(),
    signal,
  });
  return data;
}

export async function cvDetectEvents(file, confidence = 0.6, signal) {
  const form = new FormData();
  form.append("file", file, file.name || "frame.jpg");
  const { data } = await http.post(apiPath(API.cvEvents), form, {
    params: { confidence },
    ...multipartConfig(),
    signal,
  });
  return data;
}

export async function fetchCvEvents(limit = 50) {
  const { data } = await http.get(apiPath(API.cvEvents), {
    params: { limit },
    headers: cvHeaders(),
  });
  return data;
}

export async function uploadReferenceImage(className, file) {
  const form = new FormData();
  form.append("file", file, file.name || "reference.jpg");
  const { data } = await http.post(apiPath(API.cvReference(className)), form, {
    ...multipartConfig(),
  });
  return data;
}

export async function fetchReferenceImage(className) {
  const { data } = await http.get(apiPath(API.cvReference(className)), {
    headers: cvHeaders(),
  });
  return data;
}
