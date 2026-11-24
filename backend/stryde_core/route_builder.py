"""Turn a recorded run into a publishable route, and check it is safe and new."""

from __future__ import annotations

from dataclasses import dataclass, field

from .filtering import clean
from .geo import (
    LocalProjection,
    hausdorff,
    haversine_m,
    planar_length,
    polyline_point_at,
    simplify,
)
from .track import Track
from .validator import RouteSpec

LatLon = tuple[float, float]


@dataclass(frozen=True)
class RouteRules:
    min_length_m: float = 3000
    max_length_m: float = 10000
    simplify_tolerance_m: float = 5.0
    loop_close_m: float = 50.0  # start and finish this close = loop
    checkpoint_every_m: float = 1000.0
    min_checkpoints: int = 2
    duplicate_hausdorff_m: float = 30.0
    duplicate_length_ratio: float = 0.15
    privacy_buffer_m: float = 300.0  # start/finish must be this far outside any privacy zone
    max_dropped_ratio: float = 0.10  # GPS quality: at most this share of points discarded


@dataclass(frozen=True)
class PrivacyZone:
    center: LatLon
    radius_m: float


@dataclass
class RouteDraft:
    path: list[LatLon]
    start: LatLon
    finish: LatLon
    checkpoints: list[LatLon]
    distance_m: float
    is_loop: bool
    problems: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems

    def spec(self) -> RouteSpec:
        return RouteSpec(self.path, self.start, self.finish, self.checkpoints, self.distance_m)


def build_route(
    track: Track,
    *,
    existing: list[list[LatLon]] | None = None,
    privacy_zones: list[PrivacyZone] | None = None,
    rules: RouteRules = RouteRules(),
) -> RouteDraft:
    """Build a route draft from a run. `problems` lists every rule it breaks (empty = publishable)."""
    cleaned, report = clean(track)
    pts = cleaned.latlons()
    problems: list[str] = []
    if track.manual:
        problems.append("manual_activity")
    if len(pts) < 10:
        return RouteDraft(pts, pts[0] if pts else (0, 0), pts[-1] if pts else (0, 0), [], 0, False, ["too_few_points"])

    total = report.kept + report.dropped
    if total and report.dropped / total > rules.max_dropped_ratio:
        problems.append("poor_gps")

    proj = LocalProjection.around(pts)
    xy = simplify(_smooth([proj.to_xy(*p) for p in pts]), rules.simplify_tolerance_m)
    length = planar_length(xy)
    path = [proj.to_latlon(*p) for p in xy]
    start, finish = path[0], path[-1]
    is_loop = haversine_m(start, finish) <= rules.loop_close_m
    if is_loop:
        finish = start

    if length < rules.min_length_m:
        problems.append("too_short")
    if length > rules.max_length_m:
        problems.append("too_long")

    n_cp = max(rules.min_checkpoints, round(length / rules.checkpoint_every_m) - 1)  # ~1 per km, excluding the finish
    step = length / (n_cp + 1)
    checkpoints = [proj.to_latlon(*polyline_point_at(xy, step * i)) for i in range(1, n_cp + 1)]

    for zone in privacy_zones or []:
        for label, p in (("start", start), ("finish", finish)):
            if haversine_m(p, zone.center) < zone.radius_m + rules.privacy_buffer_m:
                problems.append(f"near_privacy_zone:{label}")

    for other in existing or []:
        if is_duplicate(path, other, rules):
            problems.append("duplicate_route")
            break

    return RouteDraft(path, start, finish, checkpoints, round(length, 1), is_loop, sorted(set(problems)))


def _smooth(xy: list[tuple[float, float]], window: int = 5) -> list[tuple[float, float]]:
    """Centered moving average; keeps the first and last point so start/finish stay put."""
    if len(xy) <= window:
        return xy
    h = window // 2
    out = [xy[0]]
    for i in range(1, len(xy) - 1):
        lo, hi = max(0, i - h), min(len(xy), i + h + 1)
        n = hi - lo
        out.append((sum(p[0] for p in xy[lo:hi]) / n, sum(p[1] for p in xy[lo:hi]) / n))
    out.append(xy[-1])
    return out


def is_duplicate(a: list[LatLon], b: list[LatLon], rules: RouteRules = RouteRules()) -> bool:
    proj = LocalProjection.around(a + b)
    ax = [proj.to_xy(*p) for p in a]
    bx = [proj.to_xy(*p) for p in b]
    la, lb = planar_length(ax), planar_length(bx)
    if abs(la - lb) / max(la, lb) > rules.duplicate_length_ratio:
        return False
    return hausdorff(ax, bx) <= rules.duplicate_hausdorff_m
