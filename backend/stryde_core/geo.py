"""Small, dependency-free geometry helpers for running-scale distances (< 50 km)."""

from __future__ import annotations

import math
from dataclasses import dataclass

EARTH_RADIUS_M = 6_371_008.8


def haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(min(1.0, math.sqrt(h)))


def path_length_m(latlons: list[tuple[float, float]]) -> float:
    return sum(haversine_m(latlons[i], latlons[i + 1]) for i in range(len(latlons) - 1))


@dataclass(frozen=True)
class LocalProjection:
    """Equirectangular projection around an origin. Error is negligible over a few km."""

    lat0: float
    lon0: float

    @classmethod
    def around(cls, latlons: list[tuple[float, float]]) -> "LocalProjection":
        lat = sum(p[0] for p in latlons) / len(latlons)
        lon = sum(p[1] for p in latlons) / len(latlons)
        return cls(lat, lon)

    def to_xy(self, lat: float, lon: float) -> tuple[float, float]:
        x = math.radians(lon - self.lon0) * EARTH_RADIUS_M * math.cos(math.radians(self.lat0))
        y = math.radians(lat - self.lat0) * EARTH_RADIUS_M
        return x, y

    def to_latlon(self, x: float, y: float) -> tuple[float, float]:
        lat = self.lat0 + math.degrees(y / EARTH_RADIUS_M)
        lon = self.lon0 + math.degrees(x / (EARTH_RADIUS_M * math.cos(math.radians(self.lat0))))
        return lat, lon


def closest_on_segment(p: tuple[float, float], a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
    """Closest point on segment ab to p (planar xy). Returns (distance, fraction along ab in [0,1])."""
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    seg2 = dx * dx + dy * dy
    if seg2 == 0:
        return math.hypot(px - ax, py - ay), 0.0
    f = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / seg2))
    cx, cy = ax + f * dx, ay + f * dy
    return math.hypot(px - cx, py - cy), f


def point_to_polyline_m(p: tuple[float, float], line: list[tuple[float, float]]) -> float:
    """Distance from planar point p to planar polyline."""
    if len(line) == 1:
        return math.hypot(p[0] - line[0][0], p[1] - line[0][1])
    return min(closest_on_segment(p, line[i], line[i + 1])[0] for i in range(len(line) - 1))


def polyline_point_at(line: list[tuple[float, float]], distance: float) -> tuple[float, float]:
    """Planar point at a given distance along a planar polyline."""
    remaining = distance
    for i in range(len(line) - 1):
        (ax, ay), (bx, by) = line[i], line[i + 1]
        seg = math.hypot(bx - ax, by - ay)
        if remaining <= seg and seg > 0:
            f = remaining / seg
            return ax + f * (bx - ax), ay + f * (by - ay)
        remaining -= seg
    return line[-1]


def planar_length(line: list[tuple[float, float]]) -> float:
    return sum(math.hypot(line[i + 1][0] - line[i][0], line[i + 1][1] - line[i][1]) for i in range(len(line) - 1))


def simplify(line: list[tuple[float, float]], tolerance: float) -> list[tuple[float, float]]:
    """Douglas-Peucker simplification on planar points (iterative, no recursion limit)."""
    if len(line) < 3:
        return list(line)
    keep = [False] * len(line)
    keep[0] = keep[-1] = True
    stack = [(0, len(line) - 1)]
    while stack:
        start, end = stack.pop()
        max_d, idx = 0.0, -1
        for i in range(start + 1, end):
            d, _ = closest_on_segment(line[i], line[start], line[end])
            if d > max_d:
                max_d, idx = d, i
        if max_d > tolerance and idx > 0:
            keep[idx] = True
            stack.append((start, idx))
            stack.append((idx, end))
    return [pt for pt, k in zip(line, keep) if k]


def hausdorff(a: list[tuple[float, float]], b: list[tuple[float, float]]) -> float:
    """Symmetric Hausdorff distance between two planar polylines (vertices vs. segments)."""

    def directed(x, y):
        return max(point_to_polyline_m(p, y) for p in x)

    return max(directed(a, b), directed(b, a))
