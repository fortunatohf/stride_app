"""Write a Track out as FIT / GPX / TCX / health payload, so importer tests round-trip real formats."""

from __future__ import annotations

from stryde_core.track import Track


def to_gpx(tr: Track, creator="Garmin Connect") -> bytes:
    pts = "\n".join(
        f'<trkpt lat="{p.lat:.7f}" lon="{p.lon:.7f}"><ele>150</ele><time>{p.t.strftime("%Y-%m-%dT%H:%M:%SZ")}</time>'
        f"<extensions><gpxtpx:TrackPointExtension><gpxtpx:hr>{150}</gpxtpx:hr></gpxtpx:TrackPointExtension></extensions></trkpt>"
        for p in tr.points
    )
    return (
        f'<?xml version="1.0" encoding="UTF-8"?><gpx version="1.1" creator="{creator}" '
        'xmlns="http://www.topografix.com/GPX/1/1" '
        'xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1">'
        f"<trk><name>Run</name><trkseg>{pts}</trkseg></trk></gpx>"
    ).encode()


def to_tcx(tr: Track) -> bytes:
    pts = "".join(
        f"<Trackpoint><Time>{p.t.strftime('%Y-%m-%dT%H:%M:%SZ')}</Time><Position><LatitudeDegrees>{p.lat:.7f}</LatitudeDegrees>"
        f"<LongitudeDegrees>{p.lon:.7f}</LongitudeDegrees></Position><AltitudeMeters>150</AltitudeMeters>"
        "<HeartRateBpm><Value>148</Value></HeartRateBpm></Trackpoint>"
        for p in tr.points
    )
    return (
        '<?xml version="1.0"?><TrainingCenterDatabase xmlns="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2">'
        f'<Activities><Activity Sport="Running"><Id>x</Id><Lap><Track>{pts}</Track></Lap>'
        "<Creator><Name>Polar Vantage V3</Name></Creator></Activity></Activities></TrainingCenterDatabase>"
    ).encode()


def to_fit(tr: Track) -> bytes:
    from fit_tool.fit_file_builder import FitFileBuilder
    from fit_tool.profile.messages.file_id_message import FileIdMessage
    from fit_tool.profile.messages.record_message import RecordMessage
    from fit_tool.profile.profile_type import FileType, Manufacturer

    b = FitFileBuilder(auto_define=True)
    fid = FileIdMessage()
    fid.type = FileType.ACTIVITY
    fid.manufacturer = Manufacturer.GARMIN.value
    fid.product = 0
    fid.serial_number = 1234
    fid.time_created = int(tr.points[0].t.timestamp() * 1000)
    b.add(fid)
    for p in tr.points:
        r = RecordMessage()
        r.timestamp = int(p.t.timestamp() * 1000)
        r.position_lat = p.lat
        r.position_long = p.lon
        r.heart_rate = 152
        b.add(r)
    return b.build().to_bytes()


def to_health_payload(tr: Track, device="Apple Watch") -> dict:
    return {
        "workout": {
            "id": "HK-123",
            "start": tr.points[0].t.isoformat(),
            "end": tr.points[-1].t.isoformat(),
            "activity": "running",
            "source_name": device,
            "was_user_entered": False,
        },
        "route": [{"t": p.t.isoformat(), "lat": p.lat, "lon": p.lon, "alt": 150.0, "acc": 4.0} for p in tr.points],
        "heart_rate": [{"t": p.t.isoformat(), "bpm": 150} for p in tr.points[::5]],
    }
