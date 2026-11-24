"""The one GPS track format every activity source is converted into."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class Source(str, Enum):
    APP = "app"  # recorded by the STRYDE app (native recorder)
    HEALTHKIT = "healthkit"  # Apple Health (Apple Watch and brands syncing into it)
    HEALTH_CONNECT = "health_connect"  # Android Health Connect
    GARMIN = "garmin"
    COROS = "coros"
    POLAR = "polar"
    SUUNTO = "suunto"
    FILE = "file"  # uploaded FIT / GPX / TCX


@dataclass(frozen=True, slots=True)
class TrackPoint:
    t: datetime  # timezone-aware UTC
    lat: float
    lon: float
    ele: float | None = None  # meters
    hr: int | None = None  # beats per minute
    accuracy: float | None = None  # horizontal accuracy in meters, if the source gives it

    def __post_init__(self) -> None:
        if self.t.tzinfo is None:
            raise ValueError("TrackPoint.t must be timezone-aware (UTC)")
        if not (-90 <= self.lat <= 90 and -180 <= self.lon <= 180):
            raise ValueError(f"invalid coordinate {self.lat},{self.lon}")


@dataclass(slots=True)
class Track:
    points: list[TrackPoint]
    source: Source = Source.APP
    external_id: str | None = None  # id in the source system (workout UUID, Garmin activity id...)
    device: str | None = None  # "Apple Watch Series 10", "Forerunner 265"...
    sport: str = "running"
    manual: bool = False  # entered or edited by hand: never eligible for titles
    meta: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.points.sort(key=lambda p: p.t)

    @property
    def started_at(self) -> datetime | None:
        return self.points[0].t if self.points else None

    @property
    def ended_at(self) -> datetime | None:
        return self.points[-1].t if self.points else None

    @property
    def duration_s(self) -> float:
        if len(self.points) < 2:
            return 0.0
        return (self.points[-1].t - self.points[0].t).total_seconds()

    def latlons(self) -> list[tuple[float, float]]:
        return [(p.lat, p.lon) for p in self.points]


def utc(dt: datetime) -> datetime:
    """Return dt as timezone-aware UTC (naive values are assumed to already be UTC)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
