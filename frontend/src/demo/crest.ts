/**
 * Team and league crests as inline SVG data URIs.
 *
 * The real app renders logo URLs from API-Football. Those <img> tags have no
 * error fallback, so a demo build pointing at dead or hotlinked URLs would show
 * broken-image icons across every fixture card. Generating crests locally keeps
 * the UI intact with no network at all.
 */

import { Rand } from "./rng";

const PALETTES: [string, string][] = [
  ["#ef4444", "#7f1d1d"], ["#3b82f6", "#1e3a8a"], ["#22c55e", "#14532d"],
  ["#eab308", "#713f12"], ["#a855f7", "#4c1d95"], ["#06b6d4", "#164e63"],
  ["#f97316", "#7c2d12"], ["#ec4899", "#831843"], ["#84cc16", "#365314"],
  ["#14b8a6", "#134e4a"], ["#6366f1", "#312e81"], ["#f43f5e", "#881337"],
  ["#0ea5e9", "#0c4a6e"], ["#d946ef", "#701a75"], ["#64748b", "#1e293b"],
];

/** Up to three letters, skipping the noise words in club names. */
function initials(name: string): string {
  const skip = new Set(["fc", "cf", "ac", "as", "sc", "afc", "de", "of", "the", "1899", "1. "]);
  const words = name
    .split(/[\s.]+/)
    .filter(w => w.length > 0 && !skip.has(w.toLowerCase()));
  if (words.length === 1) return words[0].slice(0, 3).toUpperCase();
  return words.slice(0, 3).map(w => w[0]).join("").toUpperCase();
}

function svgToDataUri(svg: string): string {
  // encodeURIComponent, not base64: smaller, and readable in devtools.
  return `data:image/svg+xml,${encodeURIComponent(svg.replace(/\s+/g, " ").trim())}`;
}

/**
 * A club crest — shield, stripe treatment, initials. Stable for a given id,
 * so the same team looks the same everywhere it appears.
 */
export function teamCrest(id: number, name: string): string {
  const r = new Rand(`crest:${id}`);
  const [primary, dark] = r.pick(PALETTES);
  const style = r.int(0, 3);
  const text = initials(name);

  const decoration =
    style === 0
      ? `<path d="M22 6h10v52H22z" fill="${dark}" opacity=".55"/><path d="M38 6h10v52H38z" fill="${dark}" opacity=".55"/>`
      : style === 1
        ? `<path d="M6 30h52v9H6z" fill="${dark}" opacity=".6"/>`
        : style === 2
          ? `<path d="M6 6l52 52V6z" fill="${dark}" opacity=".45"/>`
          : `<circle cx="32" cy="30" r="17" fill="none" stroke="${dark}" stroke-width="3.5" opacity=".7"/>`;

  return svgToDataUri(`
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
      <defs><clipPath id="s">
        <path d="M6 6h52v28c0 14-12 22-26 26C18 56 6 48 6 34z"/>
      </clipPath></defs>
      <g clip-path="url(#s)">
        <rect width="64" height="64" fill="${primary}"/>
        ${decoration}
      </g>
      <path d="M6 6h52v28c0 14-12 22-26 26C18 56 6 48 6 34z"
            fill="none" stroke="rgba(255,255,255,.85)" stroke-width="2.5"/>
      <text x="32" y="36" text-anchor="middle" font-family="system-ui,-apple-system,sans-serif"
            font-size="${text.length > 2 ? 16 : 20}" font-weight="800" fill="#fff"
            letter-spacing="-.5">${text}</text>
    </svg>`);
}

/** A competition badge — rounded square, distinct from club shields. */
export function leagueCrest(id: number, name: string): string {
  const r = new Rand(`league:${id}`);
  const [primary, dark] = r.pick(PALETTES);
  return svgToDataUri(`
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
      <rect x="4" y="4" width="56" height="56" rx="16" fill="${dark}"/>
      <rect x="9" y="9" width="46" height="46" rx="12" fill="${primary}"/>
      <text x="32" y="40" text-anchor="middle" font-family="system-ui,-apple-system,sans-serif"
            font-size="22" font-weight="800" fill="#fff">${initials(name)}</text>
    </svg>`);
}

/** A player headshot placeholder — circular, initial-led. */
export function playerPhoto(id: number, name: string): string {
  const r = new Rand(`player:${id}`);
  const [primary, dark] = r.pick(PALETTES);
  const letter = (name.trim()[0] || "?").toUpperCase();
  return svgToDataUri(`
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
      <circle cx="32" cy="32" r="32" fill="${dark}"/>
      <circle cx="32" cy="32" r="26" fill="${primary}"/>
      <text x="32" y="41" text-anchor="middle" font-family="system-ui,-apple-system,sans-serif"
            font-size="26" font-weight="700" fill="#fff">${letter}</text>
    </svg>`);
}
