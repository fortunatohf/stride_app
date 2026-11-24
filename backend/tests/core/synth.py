"""Synthetic GPS tracks for tests: an honest runner and the ways people cheat or GPS fails.

All tracks are generated on a ~5.1 km elliptical loop in Zilker Park, Austin.
"""

from __future__ import annotations

import math
import random
from datetime import datetime, timedelta, timezone

from stryde_core.geo import LocalProjection
from stryde_core.track import Source, Track, TrackPoint

ORIGIN = (30.2669, -97.7729)
PROJ = LocalProjection(*ORIGIN)
T0 = datetime(2026, 3, 8, 12, 0, tzinfo=timezone.utc)


def ellipse_xy(n: int = 400, a: float = 1000, b: float = 600, reverse: bool = False) -> list[tuple[float, float]]:
    """Closed loop, starting at the bottom, counter-clockwise (or clockwise if reverse)."""
    pts = []
    for i in range(n + 1):
        th = -math.pi / 2 + (2 * math.pi * i / n) * (-1 if reverse else 1)
        pts.append((a * math.cos(th), b * math.sin(th)))
    return pts


def _walk(xy, speed_mps: float, interval_s: float):
    """Yield (time_offset, x, y) moving along polyline xy at constant speed."""
    seg = [math.dist(xy[i], xy[i + 1]) for i in range(len(xy) - 1)]
    total = sum(seg)
    t, d = 0.0, 0.0
    out = []
    while d <= total:
        rem, k = d, 0
        while k < len(seg) - 1 and rem > seg[k]:
            rem -= seg[k]
            k += 1
        f = 0 if seg[k] == 0 else min(1.0, rem / seg[k])
        x = xy[k][0] + f * (xy[k + 1][0] - xy[k][0])
        y = xy[k][1] + f * (xy[k + 1][1] - xy[k][1])
        out.append((t, x, y))
        t += interval_s
        d += speed_mps * interval_s
    return out


def make_track(
    xy,
    *,
    speed_mps: float = 3.0,
    interval_s: float = 1.0,
    noise_m: float = 3.0,
    seed: int = 1,
    t0: datetime = T0,
    source: Source = Source.APP,
    accuracy: float | None = 5.0,
) -> Track:
    # Real GPS error drifts slowly (it is correlated), so model it as an AR(1) process, not white noise.
    rnd = random.Random(seed)
    rho = 0.97**interval_s
    ex = ey = 0.0
    pts = []
    for t, x, y in _walk(xy, speed_mps, interval_s):
        ex = rho * ex + rnd.gauss(0, noise_m * math.sqrt(1 - rho * rho))
        ey = rho * ey + rnd.gauss(0, noise_m * math.sqrt(1 - rho * rho))
        lat, lon = PROJ.to_latlon(x + ex, y + ey)
        pts.append(TrackPoint(t0 + timedelta(seconds=t), lat, lon, accuracy=accuracy))
    return Track(pts, source=source)


def join(*tracks: Track) -> Track:
    pts = [p for tr in tracks for p in tr.points]
    return Track(pts, source=tracks[0].source)


def straight(a, b, n=40):
    return [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n + 1)]
