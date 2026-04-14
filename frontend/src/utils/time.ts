/**
 * Shared time utilities — normalises UTC timestamps from the backend.
 *
 * Backend stores naive UTC datetimes.  JSON serialisation may omit the "Z"
 * suffix, so `new Date(str)` would treat it as local time.  Every helper
 * here calls `parseUTC` first to guarantee correct interpretation.
 */

/** Parse a backend datetime string as UTC. */
function parseUTC(dateStr: string): Date {
  // If the string already has timezone info, leave it alone.
  if (/Z|[+-]\d{2}:\d{2}$/.test(dateStr)) return new Date(dateStr);
  // Otherwise append "Z" so the browser treats it as UTC.
  return new Date(dateStr + "Z");
}

/** Human-friendly relative time ("3m ago", "2h ago", "5d ago"). */
export function timeAgo(dateStr: string): string {
  const now = Date.now();
  const then = parseUTC(dateStr).getTime();
  const diff = Math.floor((now - then) / 1000);
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

/** Full date-time in the user's locale (e.g. "Mon, Jun 2, 10:30 PM"). */
export function formatDateTime(dateStr: string): string {
  return parseUTC(dateStr).toLocaleString([], {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** Time-only in the user's locale (e.g. "10:30 PM"). */
export function formatTime(dateStr: string): string {
  return parseUTC(dateStr).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** Short date in the user's locale (e.g. "2 Jun"). */
export function formatShortDate(dateStr: string): string {
  return parseUTC(dateStr).toLocaleDateString([], {
    day: "numeric",
    month: "short",
  });
}

/** Locale date string (e.g. "6/2/2025"). */
export function formatDate(dateStr: string): string {
  return parseUTC(dateStr).toLocaleDateString();
}
