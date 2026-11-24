"""Payloads the STRYDE app uploads after reading Apple Health or Health Connect on the phone.

The phone reads the workout + its GPS route + heart rate and sends this JSON shape:

    {
      "workout": {"id": "...", "start": ISO8601, "end": ISO8601, "activity": "running",
                  "source_name": "Apple Watch", "device": "Watch7,1", "was_user_entered": false},
      "route":   [{"t": ISO8601, "lat": 30.26, "lon": -97.77, "alt": 150.2, "acc": 4.0}, ...],
      "heart_rate": [{"t": ISO8601, "bpm": 151}, ...]
    }

Both platforms use the same shape so the backend has one code path.
"""

from __future__ import annotations

import bisect
from datetime import datetime

from ..track import Source, Track, TrackPoint, utc

RUNNING = {"running", "run", "trail_running", "running_treadmill", "walking", "hiking"}


def _t(s: str) -> datetime:
    return utc(datetime.fromisoformat(s.replace("Z", "+00:00")))


def _payload_to_track(payload: dict, source: Source) -> Track:
    w = payload.get("workout") or {}
    hr = sorted(((_t(h["t"]), int(h["bpm"])) for h in payload.get("heart_rate") or []), key=lambda x: x[0])
    hr_times = [h[0] for h in hr]

    def nearest_hr(t: datetime) -> int | None:
        if not hr:
            return None
        i = bisect.bisect_left(hr_times, t)
        best = min((j for j in (i - 1, i) if 0 <= j < len(hr)), key=lambda j: abs((hr_times[j] - t).total_seconds()))
        return hr[best][1] if abs((hr_times[best] - t).total_seconds()) <= 10 else None

    points = []
    for p in payload.get("route") or []:
        t = _t(p["t"])
        points.append(TrackPoint(t, float(p["lat"]), float(p["lon"]), p.get("alt"), nearest_hr(t), p.get("acc")))

    activity = str(w.get("activity", "running")).lower()
    return Track(
        points,
        source=source,
        external_id=w.get("id"),
        device=w.get("source_name") or w.get("device"),
        sport="running" if activity in RUNNING else activity,
        manual=bool(w.get("was_user_entered")),
        meta={"device_model": w.get("device")},
    )


def from_healthkit(payload: dict) -> Track:
    return _payload_to_track(payload, Source.HEALTHKIT)


def from_health_connect(payload: dict) -> Track:
    return _payload_to_track(payload, Source.HEALTH_CONNECT)
