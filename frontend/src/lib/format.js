export function foodEmoji(name) {
  const n = (name || "").toLowerCase().replace(/_/g, " ");
  const map = {
    milk: "🥛",
    egg: "🥚",
    eggs: "🥚",
    butter: "🧈",
    ground_beef: "🥩",
    beef: "🥩",
    chocolate: "🍫",
    sweet_potato: "🍠",
    potato: "🥔",
    cheese: "🧀",
    apple: "🍎",
    banana: "🍌",
    bread: "🍞",
    water: "💧",
    juice: "🧃",
    yogurt: "🥣",
    chicken: "🍗",
    fish: "🐟",
    tomato: "🍅",
    carrot: "🥕",
  };
  const keys = Object.keys(map).sort((a, b) => b.length - a.length);
  for (const k of keys) {
    if (n.includes(k.replace(/_/g, " "))) return map[k];
  }
  return "🍽️";
}

export function formatTime(iso) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString(undefined, {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return "—";
  }
}

export function formatDateTime(iso) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return "—";
  }
}

/** Whole days until expiry; negative if expired; null if unknown. */
export function daysUntilExpiry(iso) {
  if (!iso) return null;
  try {
    const exp = new Date(iso).getTime();
    const now = Date.now();
    return Math.ceil((exp - now) / 86400000);
  } catch {
    return null;
  }
}

/** Value for datetime-local input (local timezone). */
export function toDateTimeLocalValue(iso) {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    const pad = (n) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
  } catch {
    return "";
  }
}

/** Tailwind-ish class hints for expiry badge background. */
export function expiryTone(days) {
  if (days == null) return "neutral";
  if (days < 0) return "expired";
  if (days <= 1) return "critical";
  if (days <= 3) return "warn";
  return "ok";
}
