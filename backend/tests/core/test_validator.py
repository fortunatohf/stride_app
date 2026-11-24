from datetime import timedelta

import pytest

from stryde_core.route_builder import PrivacyZone, build_route
from stryde_core.track import Source, Track, TrackPoint
from stryde_core.validator import validate_attempt

from .synth import PROJ, ellipse_xy, join, make_track, straight

LOOP = ellipse_xy()


@pytest.fixture(scope="module")
def route():
    draft = build_route(make_track(LOOP, seed=99))
    assert draft.ok, draft.problems
    return draft.spec()


def test_route_builder_makes_a_5k_loop_with_checkpoints(route):
    assert 5000 < route.distance_m < 5200
    assert route.start == route.finish
    assert len(route.checkpoints) == 4


def test_honest_phone_run_is_valid_and_timed(route):
    res = validate_attempt(make_track(LOOP, speed_mps=3.0, seed=2), route)
    assert res.valid, res.reasons
    expected = route.distance_m / 3.0
    assert abs(res.elapsed_s - expected) < 15  # within 15 s on a ~28 min run
    assert len(res.splits_s) == 5
    assert all(310 < s < 360 for s in res.splits_s)  # ~5:33 /km


def test_sparse_watch_data_still_valid(route):
    res = validate_attempt(make_track(LOOP, interval_s=5, seed=3, source=Source.GARMIN, accuracy=None), route)
    assert res.valid, res.reasons
    assert abs(res.elapsed_s - route.distance_m / 3.0) < 20


def test_wrong_direction_misses_checkpoint_order(route):
    res = validate_attempt(make_track(ellipse_xy(reverse=True), seed=4), route)
    assert not res.valid
    assert any(r.startswith("missed_checkpoint") for r in res.reasons)


def test_shortcut_across_the_park_is_rejected(route):
    # Run the first 45% of the loop, cut straight across to the 80% point, finish the loop.
    n = len(LOOP) - 1
    a, b = int(n * 0.45), int(n * 0.80)
    cut = LOOP[: a + 1] + straight(LOOP[a], LOOP[b])[1:] + LOOP[b + 1 :]
    res = validate_attempt(make_track(cut, seed=5), route)
    assert not res.valid
    assert {"distance_short", "off_route"} & set(res.reasons) or any(r.startswith("missed") for r in res.reasons)


@pytest.mark.parametrize("cut_from,cut_to", [(0.62, 0.78), (0.81, 0.99), (0.22, 0.38)])
def test_shortcut_between_checkpoints_is_rejected(route, cut_from, cut_to):
    # Hits every checkpoint but skips a stretch of the route in between.
    n = len(LOOP) - 1
    a, b = int(n * cut_from), int(n * cut_to)
    cut = LOOP[: a + 1] + straight(LOOP[a], LOOP[b])[1:] + LOOP[b + 1 :]
    res = validate_attempt(make_track(cut, seed=5), route)
    assert not res.valid
    assert "off_route" in res.reasons


def test_car_or_bike_is_rejected(route):
    res = validate_attempt(make_track(LOOP, speed_mps=9.0, seed=6), route)
    assert not res.valid
    assert "too_fast" in res.reasons


def test_gps_gap_is_rejected(route):
    tr = make_track(LOOP, seed=7)
    t_mid = tr.points[len(tr.points) // 2].t
    pts = [p for p in tr.points if not (t_mid <= p.t < t_mid + timedelta(seconds=120))]
    res = validate_attempt(Track(pts), route)
    assert not res.valid
    assert "gps_gap" in res.reasons


def test_manual_activity_never_counts(route):
    tr = make_track(LOOP, seed=8)
    tr.manual = True
    assert validate_attempt(tr, route).reasons == ["manual_activity"]


def test_warmup_then_two_laps_keeps_the_fastest_lap(route):
    warm = make_track(straight((-1600, -900), LOOP[0], 80), speed_mps=2.5, seed=9)
    lap1 = make_track(LOOP, speed_mps=2.8, seed=10, t0=warm.ended_at + timedelta(seconds=1))
    lap2 = make_track(LOOP, speed_mps=3.3, seed=11, t0=lap1.ended_at + timedelta(seconds=1))
    res = validate_attempt(join(warm, lap1, lap2), route)
    assert res.valid, res.reasons
    assert abs(res.elapsed_s - route.distance_m / 3.3) < 20


def test_a_few_gps_glitches_are_filtered_not_fatal(route):
    tr = make_track(LOOP, seed=12)
    pts = list(tr.points)
    for i in (300, 900, 1400):
        p = pts[i]
        lat, lon = PROJ.to_latlon(5000, 5000)  # 5 km away for one sample
        pts[i] = TrackPoint(p.t, lat, lon, accuracy=5.0)
    res = validate_attempt(Track(pts), route)
    assert res.valid, res.reasons
    assert res.filter_report.dropped_teleports == 3


def test_route_too_short_and_privacy_zone():
    small = ellipse_xy(a=300, b=200)
    draft = build_route(make_track(small, seed=13))
    assert "too_short" in draft.problems
    home = PROJ.to_latlon(*LOOP[0])
    draft = build_route(make_track(LOOP, seed=14), privacy_zones=[PrivacyZone(home, 100)])
    assert "near_privacy_zone:start" in draft.problems


def test_duplicate_route_detected(route):
    draft = build_route(make_track(LOOP, seed=15), existing=[route.path])
    assert "duplicate_route" in draft.problems
