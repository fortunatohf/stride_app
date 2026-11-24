"""End-to-end API flows from the product doc: create, conquer, lose and take back, train, watches."""

from datetime import timedelta

import pytest

from apps.integrations.models import DeviceConnection
from apps.leagues.models import Season
from apps.routes.models import Route
from apps.routes.services import approve_route
from tests.core.fileutil import to_fit, to_gpx, to_health_payload
from tests.core.synth import T0, ellipse_xy, make_track

from .conftest import client_for, make_user

pytestmark = pytest.mark.django_db(transaction=True)
LOOP = ellipse_xy()


def app_payload(track, client_id):
    return {
        "client_id": client_id,
        "device": "iPhone 16",
        "points": [{"t": p.t.isoformat(), "lat": p.lat, "lon": p.lon, "acc": p.accuracy} for p in track.points],
    }


def upload(client, track, cid):
    r = client.post("/api/activities/", app_payload(track, cid), format="json")
    assert r.status_code == 201, r.data
    return r.data["id"]


@pytest.fixture
def season():
    return Season.objects.create(
        city="Austin",
        number=1,
        starts_on=T0.date() - timedelta(days=7),
        ends_on=T0.date() + timedelta(days=35),
        status=Season.Status.ACTIVE,
    )


@pytest.fixture
def zilker(season):
    """Ana runs the loop, publishes it, and it is approved: she is founder and first champion."""
    ana = make_user("ana")
    c = client_for(ana)
    act = upload(c, make_track(LOOP, speed_mps=2.9, seed=1), "ana-run-1")
    r = c.post("/api/routes/", {"activity_id": act, "name": "Zilker Loop"}, format="json")
    assert r.status_code == 201, r.data
    route = Route.objects.get(slug="zilker-loop")
    assert route.status == "pending"
    approve_route(route)
    route.refresh_from_db()
    return ana, route


def test_flow1_create_route_founder_is_first_champion(zilker):
    ana, route = zilker
    assert route.champion == ana and route.record_s == pytest.approx(route.distance_m / 2.9, abs=15)
    ana.refresh_from_db()
    assert ana.xp >= 30  # route founded


def test_flow2_and_3_conquer_then_take_back(zilker, pushes):
    ana, route = zilker
    luis = make_user("luis")
    lc = client_for(luis)

    # Luis runs faster on the same course and takes the title. Ana is notified.
    upload(lc, make_track(LOOP, speed_mps=3.0, seed=2, t0=T0 + timedelta(days=1)), "luis-1")
    route.refresh_from_db()
    assert route.champion == luis and route.title_changes == 1
    assert pushes and pushes[-1][0] == ana.id and "took Zilker Loop" in pushes[-1][1]

    alerts = client_for(ana).get("/api/me/alerts/").data
    assert alerts[0]["by"] == "Luis" and alerts[0]["route"] == route.slug

    detail = lc.get(f"/api/routes/{route.slug}/").data
    assert detail["champion"]["name"] == "Luis" and detail["history"][0]["previous_holder"] == "Ana"

    # Ana gets a comeback plan aimed just under the record.
    plan = client_for(ana).post("/api/training/comeback/", {"route": route.slug}, format="json").data
    assert len(plan["sessions"]) == 7 and plan["goal_time_s"] < route.record_s

    # She takes it back; Luis is notified this time.
    upload(client_for(ana), make_track(LOOP, speed_mps=3.15, seed=3, t0=T0 + timedelta(days=3)), "ana-2")
    route.refresh_from_db()
    assert route.champion == ana and route.title_changes == 2
    assert pushes[-1][0] == luis.id
    assert client_for(ana).get("/api/me/alerts/").data == []

    board = lc.get(f"/api/routes/{route.slug}/leaderboard/").data["rows"]
    assert [r["name"] for r in board] == ["Ana", "Luis"]

    league = client_for(ana).get("/api/leagues/current/").data
    assert league["standings"][0]["name"] == "Ana" and league["standings"][0]["points"] == 25


def test_tie_keeps_the_champion(zilker):
    ana, route = zilker
    from apps.activities.models import Attempt
    from apps.activities.services import claim_title

    luis = make_user("luis")
    upload(client_for(luis), make_track(LOOP, speed_mps=2.5, seed=4, t0=T0 + timedelta(days=1)), "luis-slow")
    att = Attempt.objects.get(user=luis, route=route)
    att.elapsed_s = route.record_s
    att.save()
    assert claim_title(att) is False
    route.refresh_from_db()
    assert route.champion == ana


def test_cheating_run_does_not_take_the_title(zilker):
    ana, route = zilker
    cheat = make_user("speedy")
    upload(client_for(cheat), make_track(LOOP, speed_mps=9.0, seed=5, t0=T0 + timedelta(days=1)), "car")
    route.refresh_from_db()
    assert route.champion == ana
    att = cheat.attempts.get()
    assert not att.valid and "too_fast" in att.reasons


def test_duplicate_upload_is_idempotent(zilker):
    luis = make_user("luis")
    c = client_for(luis)
    tr = make_track(LOOP, speed_mps=2.7, seed=6, t0=T0 + timedelta(days=1))
    upload(c, tr, "same-id")
    r = c.post("/api/activities/", app_payload(tr, "same-id"), format="json")
    assert r.status_code == 200 and r.data["duplicate"]


def test_apple_watch_run_needs_consent_before_posting(zilker):
    ana, route = zilker
    sofia = make_user("sofia")
    c = client_for(sofia)
    fast = make_track(LOOP, speed_mps=3.4, interval_s=2, seed=7, t0=T0 + timedelta(days=2), accuracy=None)
    r = c.post("/api/activities/health/", {"platform": "healthkit", "workouts": [to_health_payload(fast)]}, format="json")
    assert r.status_code == 200 and "id" in r.data["results"][0]
    route.refresh_from_db()
    assert route.champion == ana  # valid, but not posted without consent
    att = sofia.attempts.get()
    assert att.valid and not att.eligible

    sofia.post_watch_runs = True
    sofia.save()
    payload = to_health_payload(fast)
    payload["workout"]["id"] = "HK-456"
    c.post("/api/activities/health/", {"platform": "healthkit", "workouts": [payload]}, format="json")
    route.refresh_from_db()
    assert route.champion == sofia


def test_file_upload_from_any_watch(zilker):
    _, route = zilker
    max_ = make_user("max", post_watch_runs=True)
    c = client_for(max_)
    tr = make_track(LOOP, speed_mps=2.8, interval_s=3, seed=8, t0=T0 + timedelta(days=2), accuracy=None)
    from django.core.files.uploadedfile import SimpleUploadedFile

    r = c.post("/api/activities/import-file/", {"file": SimpleUploadedFile("run.gpx", to_gpx(tr))}, format="multipart")
    assert r.status_code == 201, r.data
    assert max_.attempts.get().valid
    r = c.post("/api/activities/import-file/", {"file": SimpleUploadedFile("notes.txt", b"hi")}, format="multipart")
    assert r.status_code == 400


def test_garmin_webhook_creates_attempt(zilker, settings, monkeypatch):
    _, route = zilker
    jay = make_user("jay", post_watch_runs=True)
    DeviceConnection.objects.create(user=jay, provider="garmin", external_user_id="g-77", access_token="tok")
    fit = to_fit(make_track(LOOP, speed_mps=3.3, interval_s=1, seed=9, t0=T0 + timedelta(days=4), accuracy=None))
    monkeypatch.setattr("apps.integrations.services.http_get", lambda url, headers: fit)

    payload = {
        "activityFiles": [
            {"userId": "g-77", "summaryId": "s-1", "fileType": "FIT", "callbackURL": "https://apis.garmin.com/file?id=1"}
        ]
    }
    c = client_for(jay)
    c.force_authenticate(None)
    assert c.post("/api/integrations/garmin/webhook/wrong/", payload, format="json").status_code == 404
    r = c.post(f"/api/integrations/garmin/webhook/{settings.WEBHOOK_SECRET}/", payload, format="json")
    assert r.status_code == 200
    route.refresh_from_db()
    assert route.champion == jay
    assert jay.activities.get().source == "garmin"


def test_route_rules_enforced(season):
    u = make_user("newbie")
    c = client_for(u)
    small = upload(c, make_track(ellipse_xy(a=300, b=200), seed=10), "small")
    r = c.post("/api/routes/", {"activity_id": small, "name": "Tiny"}, format="json")
    assert r.status_code == 400 and "too_short" in r.data["problems"]


def test_privacy_zone_center_never_returned(season):
    u = make_user("pz")
    c = client_for(u)
    r = c.post("/api/me/privacy-zones/", {"label": "Home", "lat": 30.26, "lon": -97.77, "radius_m": 200}, format="json")
    assert r.status_code == 201 and "lat" not in r.data
    assert "lat" not in c.get("/api/me/privacy-zones/").data[0]


def test_integrations_list_shows_every_door(season):
    data = client_for(make_user("w")).get("/api/integrations/").data
    assert {d["key"] for d in data["on_device"]} == {"apple_health", "health_connect", "file"}
    assert {d["key"] for d in data["cloud"]} == {"garmin", "polar", "coros", "suunto"}
