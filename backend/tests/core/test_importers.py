"""Every watch format must import to a Track that the validator accepts exactly like a phone run."""

import pytest

from stryde_core.importers import (
    UnsupportedFile,
    from_health_connect,
    from_healthkit,
    import_file,
)
from stryde_core.providers import REGISTRY
from stryde_core.route_builder import build_route
from stryde_core.track import Source
from stryde_core.validator import validate_attempt

from .fileutil import to_fit, to_gpx, to_health_payload, to_tcx
from .synth import ellipse_xy, make_track

LOOP = ellipse_xy()


@pytest.fixture(scope="module")
def route():
    return build_route(make_track(LOOP, seed=99)).spec()


@pytest.fixture(scope="module")
def watch_run():
    # Watches usually record every 1-5 s; use 2 s here.
    return make_track(LOOP, interval_s=2, seed=21, accuracy=None)


def _assert_same_result(track, route, watch_run):
    assert len(track.points) == len(watch_run.points)
    res = validate_attempt(track, route)
    ref = validate_attempt(watch_run, route)
    assert res.valid, res.reasons
    assert abs(res.elapsed_s - ref.elapsed_s) < 1.5


def test_fit_import(route, watch_run):
    tr = import_file(to_fit(watch_run), "run.fit")
    assert tr.points[0].hr == 152
    _assert_same_result(tr, route, watch_run)


def test_gpx_import(route, watch_run):
    tr = import_file(to_gpx(watch_run), "run.gpx")
    assert tr.points[0].hr == 150 and tr.device == "Garmin Connect"
    _assert_same_result(tr, route, watch_run)


def test_tcx_import(route, watch_run):
    tr = import_file(to_tcx(watch_run), "run.tcx")
    assert tr.device == "Polar Vantage V3"
    _assert_same_result(tr, route, watch_run)


def test_format_detected_from_content_not_name(watch_run):
    assert import_file(to_gpx(watch_run), "upload.bin").points
    assert import_file(to_fit(watch_run), "").points


def test_unsupported_file():
    with pytest.raises(UnsupportedFile):
        import_file(b"hello", "notes.txt")


def test_apple_health_payload(route, watch_run):
    tr = from_healthkit(to_health_payload(watch_run))
    assert tr.source == Source.HEALTHKIT and tr.external_id == "HK-123" and tr.device == "Apple Watch"
    assert tr.points[0].hr == 150
    _assert_same_result(tr, route, watch_run)


def test_health_connect_payload_and_manual_flag(route, watch_run):
    payload = to_health_payload(watch_run, device="Galaxy Watch7")
    payload["workout"]["was_user_entered"] = True
    tr = from_health_connect(payload)
    assert tr.source == Source.HEALTH_CONNECT and tr.manual
    assert validate_attempt(tr, route).reasons == ["manual_activity"]


def test_garmin_webhook_to_attempt(route, watch_run):
    garmin = REGISTRY["garmin"]
    payload = {
        "activityFiles": [
            {
                "userId": "g-user-1",
                "summaryId": "act-987",
                "fileType": "FIT",
                "manual": False,
                "callbackURL": "https://apis.garmin.com/wellness-api/rest/activityFile?id=987&token=abc",
                "startTimeInSeconds": 1772971200,
                "activityType": "RUNNING",
            }
        ]
    }
    refs = garmin.parse_webhook(payload)
    assert len(refs) == 1 and refs[0].external_id == "act-987"

    fit = to_fit(watch_run)
    calls = []

    def fake_get(url, headers):
        calls.append((url, headers))
        return fit

    data = garmin.download(refs[0], "TOKEN", fake_get)
    tr = garmin.to_track(refs[0], data)
    assert calls[0][1]["Authorization"] == "Bearer TOKEN"
    assert tr.source == Source.GARMIN and tr.external_id == "act-987"
    _assert_same_result(tr, route, watch_run)


def test_polar_webhook():
    refs = REGISTRY["polar"].parse_webhook(
        {"event": "EXERCISE", "user_id": 475, "entity_id": "aQlC83", "url": "https://www.polaraccesslink.com/v3/exercises/aQlC83"}
    )
    assert refs[0].file_url.endswith("/exercises/aQlC83/fit")
    assert REGISTRY["polar"].parse_webhook({"event": "SLEEP"}) == []


def test_every_provider_is_registered():
    assert set(REGISTRY) == {"garmin", "polar", "coros", "suunto"}
