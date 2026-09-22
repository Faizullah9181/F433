/**
 * Demo mode.
 *
 * The backend and the upstream football API are switched off for cost reasons,
 * which left every page rendering an empty state or an error box. This module
 * serves a generated dataset in their place.
 *
 * Two ways in:
 *   - forced, via `VITE_DEMO_MODE=true` at build time (what the hosted site uses)
 *   - automatic, when a real request fails because the API isn't reachable
 *
 * The automatic path means the site repairs itself if the backend goes down,
 * and goes straight back to live data the moment it returns.
 */

import { parse, route } from "./router";

export const DEMO_FORCED = import.meta.env.VITE_DEMO_MODE === "true";

/** Flipped once a real request has failed and demo data was served instead. */
let fellBack = false;
const listeners = new Set<(active: boolean) => void>();

export function isDemoActive(): boolean {
  return DEMO_FORCED || fellBack;
}

export function onDemoChange(fn: (active: boolean) => void): () => void {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

function markFellBack() {
  if (fellBack) return;
  fellBack = true;
  for (const fn of listeners) fn(true);
}

/**
 * A touch of latency so skeletons and spinners still get their moment —
 * instantly-resolved promises make the UI flash in a way that reads as broken.
 */
function settle<T>(value: T): Promise<T> {
  return new Promise(resolve => setTimeout(() => resolve(value), 60 + Math.random() * 180));
}

/** Serve a request from the demo world. Throws if the path has no mapping. */
export function demoFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const req = parse(path, options?.method ?? "GET", options?.body as BodyInit | null | undefined);
  return settle(route(req) as T);
}

/**
 * Serve from the demo world after a real request failed.
 * Returns null when the path has no demo mapping, so the caller can rethrow
 * the original network error rather than masking it with a bogus one.
 */
export async function demoFallback<T>(path: string, options?: RequestInit): Promise<T | null> {
  try {
    const value = await demoFetch<T>(path, options);
    markFellBack();
    return value;
  } catch {
    return null;
  }
}
