/** Shared image upload validation for CV / scan flows. */

export const ALLOWED_IMAGE_TYPES = new Set([
  "image/jpeg",
  "image/jpg",
  "image/png",
  "image/webp",
]);

export const ALLOWED_IMAGE_ACCEPT =
  "image/jpeg,image/jpg,image/png,image/webp,.jpg,.jpeg,.png,.webp";

export const MAX_IMAGE_BYTES = 5 * 1024 * 1024;

/**
 * @param {File | null | undefined} file
 * @returns {{ ok: true, file: File } | { ok: false, message: string }}
 */
export function validateImageFile(file) {
  if (!file) {
    return { ok: false, message: "No file selected." };
  }
  if (file.size === 0) {
    return { ok: false, message: "File is empty." };
  }
  if (file.size > MAX_IMAGE_BYTES) {
    return { ok: false, message: "Image too large (max 5 MB)." };
  }
  const type = (file.type || "").toLowerCase();
  if (type && !ALLOWED_IMAGE_TYPES.has(type)) {
    return {
      ok: false,
      message: "Unsupported format. Use JPG, JPEG, PNG, or WEBP.",
    };
  }
  const ext = file.name.split(".").pop()?.toLowerCase() ?? "";
  const allowedExt = new Set(["jpg", "jpeg", "png", "webp"]);
  if (!type && ext && !allowedExt.has(ext)) {
    return {
      ok: false,
      message: "Unsupported format. Use JPG, JPEG, PNG, or WEBP.",
    };
  }
  return { ok: true, file };
}
