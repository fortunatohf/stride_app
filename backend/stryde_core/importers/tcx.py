"""TCX files (Garmin Training Center XML), still exported by Garmin, Polar and others."""

from __future__ import annotations

from datetime import datetime
from xml.etree import ElementTree as ET

from ..track import Source, Track, TrackPoint, utc

NS = {"t": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"}


def _parse_time(s: str) -> datetime:
    return utc(datetime.fromisoformat(s.replace("Z", "+00:00")))


def from_tcx(data: bytes | str, source: Source = Source.FILE, external_id: str | None = None) -> Track:
    root = ET.fromstring(data if isinstance(data, bytes) else data.encode())
    points: list[TrackPoint] = []
    sport = "running"
    act = root.find(".//t:Activity", NS)
    if act is not None and act.get("Sport"):
        sport = act.get("Sport", "running").lower()
    for tp in root.iterfind(".//t:Trackpoint", NS):
        time_el = tp.find("t:Time", NS)
        lat_el = tp.find("t:Position/t:LatitudeDegrees", NS)
        lon_el = tp.find("t:Position/t:LongitudeDegrees", NS)
        if time_el is None or lat_el is None or lon_el is None:
            continue
        ele_el = tp.find("t:AltitudeMeters", NS)
        hr_el = tp.find("t:HeartRateBpm/t:Value", NS)
        points.append(
            TrackPoint(
                _parse_time(time_el.text),
                float(lat_el.text),
                float(lon_el.text),
                float(ele_el.text) if ele_el is not None else None,
                int(hr_el.text) if hr_el is not None else None,
            )
        )
    creator = root.find(".//t:Creator/t:Name", NS)
    return Track(
        points, source=source, external_id=external_id, sport=sport, device=creator.text if creator is not None else None
    )
