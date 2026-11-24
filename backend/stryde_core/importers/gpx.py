"""GPX files: exported by almost every watch platform and running app."""

from __future__ import annotations

import gpxpy

from ..track import Source, Track, TrackPoint, utc


def _hr(point) -> int | None:
    # Garmin TrackPointExtension: <gpxtpx:TrackPointExtension><gpxtpx:hr>150</gpxtpx:hr>
    for ext in point.extensions or []:
        for el in ext.iter():
            if el.tag.lower().endswith("}hr") or el.tag.lower() == "hr":
                try:
                    return int(float(el.text))
                except (TypeError, ValueError):
                    return None
    return None


def from_gpx(data: bytes | str, source: Source = Source.FILE, external_id: str | None = None) -> Track:
    text = data.decode("utf-8", errors="replace") if isinstance(data, bytes) else data
    gpx = gpxpy.parse(text)
    points: list[TrackPoint] = []
    for trk in gpx.tracks:
        for seg in trk.segments:
            for p in seg.points:
                if p.time is None:
                    continue
                points.append(TrackPoint(utc(p.time), p.latitude, p.longitude, p.elevation, _hr(p)))
    device = gpx.creator or None
    return Track(points, source=source, external_id=external_id, device=device)
