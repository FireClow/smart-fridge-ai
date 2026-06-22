/**
 * Canonical REST paths for the FastAPI backend.
 * Keep in sync with backend routers and scripts/validate_api_contract.py.
 */
export const API = {
  inventory: "/api/inventory",
  inventoryItem: (itemName) => `/api/inventory/${encodeURIComponent(itemName)}`,
  logs: "/api/logs",
  stats: "/api/stats",
  health: "/api/health",
  modelInfo: "/api/model/info",
  scanImage: "/api/scan/image",
  notifications: "/api/notifications",
  notificationsGenerate: "/api/notifications/generate",
  notificationRead: (id) => `/api/notifications/${id}/read`,
  cvAnalyze: "/api/cv/analyze",
  cvMetrics: "/api/cv/metrics",
  cvReset: "/api/cv/reset",
  cvMatch: "/api/cv/match",
  cvHomography: "/api/cv/homography",
  cvEvents: "/api/cv/events",
  cvReference: (className) => `/api/cv/reference/${encodeURIComponent(className)}`,
};

/** @typedef {typeof API} ApiRoutes */
