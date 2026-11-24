"""Decide whether an activity is a valid attempt on a route, and how long it took.

The server is the only judge. Every source (phone, watch, file) arrives here as a `Track`.
"""

from __future__ import annotations

import bisect
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .filtering import FilterConfig, FilterReport, clean
from .geo import (
    LocalProjection,
    closest_on_segment,
    planar_length,
    point_to_polyline_m,
    polyline_point_at,
)
from .track import Track

LatLon = tuple[float, float]


@dataclass(frozen=True)
class RouteSpec:
    path: list[LatLon]  # route line, in running direction
    start: LatLon
    finish: LatLon
    checkpoints: list[LatLon]  # in running order, excluding start and finish
    distance_m: float


@dataclass(frozen=True)
class ValidatorConfig:
    gate_radius_m: float = 25.0
    checkpoint_radius_m: float = 30.0
    corridor_m: float = 40.0
    min_corridor_ratio: float = 0.90  # share of the runner's points near the route
    min_route_coverage: float = 0.95  # share of the route the runner actually passed near
    coverage_step_m: float = 25.0
    distance_min_ratio: float = 0.95
    distance_max_ratio: float = 1.15
    max_sustained_mps: float = 7.0  # ~2:23 /km; faster than any human 5K pace for 30 s+
    sustained_window_s: float = 30.0
    max_gap_s: float = 60.0
    max_teleport_ratio: float = 0.05
    min_points: int = 10
    gate_slack_m: float = 3.0  # how near the closest approach counts as "at the line"


@dataclass
class AttemptResult:
    valid: bool
    reasons: list[str] = field(default_factory=list)
    elapsed_s: float | None = None
    start_time: datetime | None = None
    finish_time: datetime | None = None
    distance_m: float | None = None
    corridor_ratio: float | None = None
    route_coverage: float | None = None
    max_sustained_mps: float | None = None
    checkpoints_hit: int = 0
    splits_s: list[float] = field(default_factory=list)  # seconds per full km
    filter_report: FilterReport | None = None

    @property
    def pace_s_per_km(self) -> float | None:
        if not self.elapsed_s or not self.distance_m:
            return None
        return self.elapsed_s / (self.distance_m / 1000)


class _Prepared:
    """Track projected to meters with cumulative distance and relative times."""

    def __init__(self, track: Track, proj: LocalProjection):
        self.t0 = track.points[0].t
        self.xy = [proj.to_xy(p.lat, p.lon) for p in track.points]
        self.ts = [(p.t - self.t0).total_seconds() for p in track.points]
        self.seglen = [math.dist(self.xy[i], self.xy[i + 1]) for i in range(len(self.xy) - 1)]
        self.cum = [0.0]
        for s in self.seglen:
            self.cum.append(self.cum[-1] + s)

    @property
    def nseg(self) -> int:
        return len(self.seglen)

    def seg_dist(self, k: int, target: tuple[float, float]) -> tuple[float, float]:
        return closest_on_segment(target, self.xy[k], self.xy[k + 1])

    def time_at(self, k: int, f: float) -> float:
        return self.ts[k] + f * (self.ts[k + 1] - self.ts[k])

    def dist_at(self, k: int, f: float) -> float:
        return self.cum[k] + f * self.seglen[k]

    def abs_time(self, rel: float) -> datetime:
        return self.t0 + timedelta(seconds=rel)


@dataclass
class _Pass:
    first_seg: int
    last_seg: int
    seg: int  # chosen segment (start: last near-minimum; finish: first near-minimum)
    frac: float


def _gate_passes(tr: _Prepared, target, radius, slack, *, pick: str, from_seg: int = 0) -> list[_Pass]:
    passes: list[_Pass] = []
    k = from_seg
    while k < tr.nseg:
        d, _ = tr.seg_dist(k, target)
        if d > radius:
            k += 1
            continue
        first = k
        dists = []
        while k < tr.nseg:
            d, f = tr.seg_dist(k, target)
            if d > radius:
                break
            dists.append((k, d, f))
            k += 1
        dmin = min(d for _, d, _ in dists)
        near = [x for x in dists if x[1] <= dmin + slack]
        chosen = near[-1] if pick == "last" else near[0]
        passes.append(_Pass(first, k - 1, chosen[0], chosen[2]))
    return passes


def _first_hit(tr: _Prepared, target, radius, from_seg: int) -> int | None:
    for k in range(from_seg, tr.nseg):
        if tr.seg_dist(k, target)[0] <= radius:
            return k
    return None


def _max_sustained_speed(tr: _Prepared, i0: int, i1: int, window: float) -> float:
    best = 0.0
    j = i0
    for i in range(i0, i1 + 1):
        if j < i:
            j = i
        while j <= i1 and tr.ts[j] - tr.ts[i] < window:
            j += 1
        if j > i1:
            break
        best = max(best, (tr.cum[j] - tr.cum[i]) / (tr.ts[j] - tr.ts[i]))
    return best


def _splits(tr: _Prepared, start_d: float, start_t: float, end_d: float) -> list[float]:
    out, prev_t, km = [], start_t, 1
    while start_d + km * 1000 <= end_d:
        target = start_d + km * 1000
        i = bisect.bisect_left(tr.cum, target)
        i = max(1, min(i, len(tr.cum) - 1))
        seg = tr.cum[i] - tr.cum[i - 1]
        f = 0.0 if seg == 0 else (target - tr.cum[i - 1]) / seg
        t = tr.ts[i - 1] + f * (tr.ts[i] - tr.ts[i - 1])
        out.append(round(t - prev_t, 1))
        prev_t, km = t, km + 1
    return out


def validate_attempt(
    track: Track,
    route: RouteSpec,
    cfg: ValidatorConfig = ValidatorConfig(),
    filter_cfg: FilterConfig = FilterConfig(),
) -> AttemptResult:
    if track.manual:
        return AttemptResult(False, ["manual_activity"])

    cleaned, report = clean(track, filter_cfg)
    if len(cleaned.points) < cfg.min_points:
        return AttemptResult(False, ["too_few_points"], filter_report=report)
    total = report.kept + report.dropped_teleports
    if total and report.dropped_teleports / total > cfg.max_teleport_ratio:
        return AttemptResult(False, ["gps_unreliable"], filter_report=report)

    proj = LocalProjection.around(route.path)
    tr = _Prepared(cleaned, proj)
    route_xy = [proj.to_xy(*p) for p in route.path]
    start_xy, finish_xy = proj.to_xy(*route.start), proj.to_xy(*route.finish)
    cps_xy = [proj.to_xy(*c) for c in route.checkpoints]

    starts = _gate_passes(tr, start_xy, cfg.gate_radius_m, cfg.gate_slack_m, pick="last")
    if not starts:
        return AttemptResult(False, ["no_start"], filter_report=report)

    best_valid: AttemptResult | None = None
    best_invalid: AttemptResult | None = None

    for sp in starts:
        res = _evaluate(tr, sp, cps_xy, finish_xy, route_xy, route, cfg)
        res.filter_report = report
        if res.valid:
            if best_valid is None or res.elapsed_s < best_valid.elapsed_s:
                best_valid = res
        elif (
            best_invalid is None
            or res.checkpoints_hit > best_invalid.checkpoints_hit
            or (res.checkpoints_hit == best_invalid.checkpoints_hit and len(res.reasons) < len(best_invalid.reasons))
        ):
            best_invalid = res

    return best_valid or best_invalid  # type: ignore[return-value]


def _evaluate(tr, sp: _Pass, cps_xy, finish_xy, route_xy, route: RouteSpec, cfg: ValidatorConfig) -> AttemptResult:
    # Checkpoints, in order, after leaving the start gate.
    cursor = sp.seg
    hit = 0
    for n, cp in enumerate(cps_xy, start=1):
        k = _first_hit(tr, cp, cfg.checkpoint_radius_m, cursor)
        if k is None:
            return AttemptResult(False, [f"missed_checkpoint:{n}"], checkpoints_hit=hit)
        hit += 1
        cursor = k

    # Finish: first pass through the finish gate after the last checkpoint (and after leaving the start).
    search_from = max(cursor, sp.last_seg + 1) if not cps_xy else cursor
    fins = _gate_passes(tr, finish_xy, cfg.gate_radius_m, cfg.gate_slack_m, pick="first", from_seg=search_from)
    if not fins:
        return AttemptResult(False, ["no_finish"], checkpoints_hit=hit)
    fp = fins[0]

    start_t = tr.time_at(sp.seg, sp.frac)
    finish_t = tr.time_at(fp.seg, fp.frac)
    start_d = tr.dist_at(sp.seg, sp.frac)
    finish_d = tr.dist_at(fp.seg, fp.frac)
    elapsed = finish_t - start_t
    dist = finish_d - start_d

    reasons: list[str] = []
    if elapsed <= 0:
        reasons.append("bad_timing")
    if dist < route.distance_m * cfg.distance_min_ratio:
        reasons.append("distance_short")
    if dist > route.distance_m * cfg.distance_max_ratio:
        reasons.append("distance_long")

    i0, i1 = sp.seg, fp.seg + 1
    inner = range(i0, i1 + 1)
    inside = sum(1 for i in inner if point_to_polyline_m(tr.xy[i], route_xy) <= cfg.corridor_m)
    corridor_ratio = inside / max(1, len(inner))

    # Coverage: walk the route every 25 m and check the runner passed near each sample.
    # This catches shortcuts between checkpoints that keep most points near the route.
    run_xy = tr.xy[i0 : i1 + 1]
    rlen = planar_length(route_xy)
    n_samples = max(2, int(rlen // cfg.coverage_step_m))
    samples = [polyline_point_at(route_xy, rlen * s / n_samples) for s in range(n_samples + 1)]
    covered = sum(1 for p in samples if point_to_polyline_m(p, run_xy) <= cfg.corridor_m)
    coverage = covered / len(samples)
    if corridor_ratio < cfg.min_corridor_ratio or coverage < cfg.min_route_coverage:
        reasons.append("off_route")

    max_gap = max((tr.ts[i + 1] - tr.ts[i]) for i in range(i0, i1)) if i1 > i0 else 0
    if max_gap > cfg.max_gap_s:
        reasons.append("gps_gap")

    vmax = _max_sustained_speed(tr, i0, i1, cfg.sustained_window_s)
    if vmax > cfg.max_sustained_mps:
        reasons.append("too_fast")

    return AttemptResult(
        valid=not reasons,
        reasons=reasons,
        elapsed_s=round(elapsed, 1),
        start_time=tr.abs_time(start_t),
        finish_time=tr.abs_time(finish_t),
        distance_m=round(dist, 1),
        corridor_ratio=round(corridor_ratio, 3),
        route_coverage=round(coverage, 3),
        max_sustained_mps=round(vmax, 2),
        checkpoints_hit=hit,
        splits_s=_splits(tr, start_d, start_t, finish_d),
    )
