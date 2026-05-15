/** Demo inventory when VITE_USE_DUMMY=true or offline dev. */
export const dummyInventory = [
  {
    id: 1,
    item_name: "milk",
    quantity: 2,
    updated_at: "2026-05-13T15:17:56.155Z",
    expires_at: "2026-05-15T12:00:00.000Z",
    expiry_locked: false,
  },
  {
    id: 2,
    item_name: "egg",
    quantity: 6,
    updated_at: "2026-05-13T15:17:12.780Z",
    expires_at: "2026-05-20T12:00:00.000Z",
    expiry_locked: true,
  },
  {
    id: 3,
    item_name: "butter",
    quantity: 1,
    updated_at: "2026-05-13T15:17:23.064Z",
    expires_at: "2026-05-14T08:00:00.000Z",
    expiry_locked: false,
  },
  {
    id: 4,
    item_name: "beef",
    quantity: 1,
    updated_at: "2026-05-13T15:17:56.155Z",
    expires_at: "2026-05-13T18:00:00.000Z",
    expiry_locked: false,
  },
  {
    id: 5,
    item_name: "chocolate",
    quantity: 3,
    updated_at: "2026-05-13T15:17:34.219Z",
    expires_at: "2026-11-01T12:00:00.000Z",
    expiry_locked: false,
  },
];

/** Demo detection logs with confidence 0–1. */
export const dummyLogs = [
  {
    id: 1,
    item_name: "milk",
    quantity: 2,
    confidence: 0.94,
    detected_at: "2026-05-13T15:17:56.155Z",
  },
  {
    id: 2,
    item_name: "egg",
    quantity: 6,
    confidence: 0.91,
    detected_at: "2026-05-13T15:17:12.780Z",
  },
  {
    id: 3,
    item_name: "butter",
    quantity: 1,
    confidence: 0.88,
    detected_at: "2026-05-13T15:17:23.064Z",
  },
  {
    id: 4,
    item_name: "beef",
    quantity: 1,
    confidence: 0.93,
    detected_at: "2026-05-13T15:17:56.155Z",
  },
  {
    id: 5,
    item_name: "chocolate",
    quantity: 3,
    confidence: 0.87,
    detected_at: "2026-05-13T15:17:34.219Z",
  },
  {
    id: 6,
    item_name: "sweet_potato",
    quantity: 1,
    confidence: 0.85,
    detected_at: "2026-05-13T15:16:45.000Z",
  },
];

export const dummyStats = {
  total_items: 14,
  total_categories: 6,
  avg_confidence: 0.898,
  last_detected: "2026-05-13T15:17:56.155Z",
  fps_hint: 28.5,
  expiring_soon_count: 2,
};
