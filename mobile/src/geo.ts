export type Pt = { lat: number; lon: number };

const R = 6_371_008.8;
const rad = (d: number) => (d * Math.PI) / 180;

export function haversine(a: Pt, b: Pt): number {
  const dLat = rad(b.lat - a.lat);
  const dLon = rad(b.lon - a.lon);
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(rad(a.lat)) * Math.cos(rad(b.lat)) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.min(1, Math.sqrt(h)));
}

/** Live distance on the phone (display only — the server recomputes everything). Skips poor fixes and jitter. */
export function liveDistance(points: (Pt & { acc?: number | null })[], maxAcc = 30, minStep = 2): number {
  let total = 0;
  let last: Pt | null = null;
  for (const p of points) {
    if (p.acc != null && p.acc > maxAcc) continue;
    if (last) {
      const d = haversine(last, p);
      if (d < minStep) continue;
      total += d;
    }
    last = p;
  }
  return total;
}

/**
 * Attempt-mode helper: how many checkpoints the runner has passed, in order. Display only.
 * Uses the same radii as the server validator (start/finish 25 m, checkpoints 30 m).
 */
export function checkpointProgress(points: Pt[], start: Pt, checkpoints: Pt[], finish: Pt) {
  let started = false;
  let next = 0;
  let finished = false;
  for (const p of points) {
    if (!started) {
      if (haversine(p, start) <= 25) started = true;
      continue;
    }
    if (next < checkpoints.length) {
      if (haversine(p, checkpoints[next]) <= 30) next += 1;
    } else if (haversine(p, finish) <= 25) {
      finished = true;
      break;
    }
  }
  return { started, passed: next, total: checkpoints.length, finished };
}
