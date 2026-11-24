"""Clean raw GPS before it is judged. Conservative: when in doubt, keep the point."""

from __future__ import annotations

from dataclasses import dataclass, replace

from .geo import haversine_m
from .track import Track, TrackPoint


@dataclass(frozen=True)
class FilterConfig:
    max_accuracy_m: float = 30.0  # drop points the device itself says are worse than this
    teleport_speed_mps: float = 15.0  # a jump faster than this from the last kept point is a glitch
    min_interval_s: float = 0.5  # collapse points closer in time than this


@dataclass(frozen=True)
class FilterReport:
    kept: int
    dropped_accuracy: int
    dropped_duplicates: int
    dropped_teleports: int

    @property
    def dropped(self) -> int:
        return self.dropped_accuracy + self.dropped_duplicates + self.dropped_teleports


def clean(track: Track, cfg: FilterConfig = FilterConfig()) -> tuple[Track, FilterReport]:
    pts = sorted(track.points, key=lambda p: p.t)
    out: list[TrackPoint] = []
    d_acc = d_dup = d_tel = 0
    streak = 0  # consecutive teleport rejections
    for p in pts:
        if p.accuracy is not None and p.accuracy > cfg.max_accuracy_m:
            d_acc += 1
            continue
        if out:
            prev = out[-1]
            dt = (p.t - prev.t).total_seconds()
            if dt < cfg.min_interval_s:
                d_dup += 1
                continue
            if haversine_m((prev.lat, prev.lon), (p.lat, p.lon)) / dt > cfg.teleport_speed_mps:
                streak += 1
                if streak < 3:
                    d_tel += 1
                    continue
                # Three rejections in a row: the last kept point was the glitch, not these.
                out.pop()
                d_tel += 1
        streak = 0
        out.append(p)
    report = FilterReport(len(out), d_acc, d_dup, d_tel)
    return replace(track, points=out), report
