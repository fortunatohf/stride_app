"""FIT files: the native format of Garmin, COROS, Polar, Suunto, Wahoo and most watches."""

from __future__ import annotations

import io

import fitparse

from ..track import Source, Track, TrackPoint, utc

SEMICIRCLE = 180 / 2**31

# FIT "sport" values we accept for titles. Anything else is imported but not eligible.
RUNNING_SPORTS = {"running", "walking", "hiking", "generic"}


def from_fit(data: bytes, source: Source = Source.FILE, external_id: str | None = None) -> Track:
    fit = fitparse.FitFile(io.BytesIO(data))
    points: list[TrackPoint] = []
    sport = "running"
    device = None
    manual = False

    for msg in fit.get_messages():
        name = msg.name
        if name == "record":
            v = {f.name: f.value for f in msg.fields}
            lat, lon, ts = v.get("position_lat"), v.get("position_long"), v.get("timestamp")
            if lat is None or lon is None or ts is None:
                continue
            ele = v.get("enhanced_altitude", v.get("altitude"))
            points.append(
                TrackPoint(
                    t=utc(ts),
                    lat=lat * SEMICIRCLE,
                    lon=lon * SEMICIRCLE,
                    ele=float(ele) if ele is not None else None,
                    hr=int(v["heart_rate"]) if v.get("heart_rate") is not None else None,
                )
            )
        elif name == "sport" or name == "session":
            s = msg.get_value("sport")
            if s:
                sport = str(s)
        elif name == "device_info" and device is None:
            prod = msg.get_value("garmin_product") or msg.get_value("product_name") or msg.get_value("product")
            manu = msg.get_value("manufacturer")
            if prod or manu:
                device = " ".join(str(x) for x in (manu, prod) if x)
        elif name == "file_id":
            # FIT files with no GPS-producing device (e.g. created on a website) are treated as manual.
            if str(msg.get_value("type") or "") not in ("activity", "None", ""):
                manual = True

    return Track(points, source=source, external_id=external_id, device=device, sport=sport, manual=manual)
