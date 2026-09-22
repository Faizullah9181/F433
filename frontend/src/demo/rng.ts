/**
 * Deterministic pseudo-randomness for the demo dataset.
 *
 * Every value in the demo world is derived from a fixed seed, so the site looks
 * identical on every load and across every visitor. That matters more than it
 * sounds: a timeline that reshuffles on refresh reads as broken, not as live.
 */

/** mulberry32 — small, fast, good enough for fixture data. */
export function rng(seed: number): () => number {
  let a = seed >>> 0;
  return function () {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Stable 32-bit hash of a string, for seeding from names/paths. */
export function hash(str: string): number {
  let h = 2166136261 >>> 0;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

export class Rand {
  private next: () => number;

  constructor(seed: number | string) {
    this.next = rng(typeof seed === "string" ? hash(seed) : seed);
  }

  /** Float in [0, 1). */
  float(): number {
    return this.next();
  }

  /** Integer in [min, max] inclusive. */
  int(min: number, max: number): number {
    return min + Math.floor(this.next() * (max - min + 1));
  }

  /** True with probability p. */
  chance(p: number): boolean {
    return this.next() < p;
  }

  pick<T>(list: readonly T[]): T {
    return list[Math.floor(this.next() * list.length)];
  }

  /** n distinct items, or the whole list if n exceeds its length. */
  sample<T>(list: readonly T[], n: number): T[] {
    return this.shuffle(list).slice(0, Math.min(n, list.length));
  }

  shuffle<T>(list: readonly T[]): T[] {
    const out = [...list];
    for (let i = out.length - 1; i > 0; i--) {
      const j = Math.floor(this.next() * (i + 1));
      [out[i], out[j]] = [out[j], out[i]];
    }
    return out;
  }

  /** Skews low — good for karma, vote counts, anything long-tailed. */
  weighted(min: number, max: number, power = 2): number {
    return min + Math.floor(Math.pow(this.next(), power) * (max - min + 1));
  }
}

/** Build a list of n items, each with its own derived seed. */
export function generate<T>(n: number, seed: string, fn: (r: Rand, i: number) => T): T[] {
  return Array.from({ length: n }, (_, i) => fn(new Rand(`${seed}:${i}`), i));
}
