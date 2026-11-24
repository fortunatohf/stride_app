"""Activity ingestion and attempt processing. One path for every source (phone, watch, file)."""

from __future__ import annotations

import logging

from django.contrib.gis.geos import Polygon
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.common.geo import line
from apps.leagues.models import PointsLedger
from apps.leagues.services import award
from apps.routes.models import Route, TitleChange
from stryde_core.filtering import clean
from stryde_core.geo import LocalProjection, path_length_m, simplify
from stryde_core.track import Track
from stryde_core.validator import validate_attempt

from .models import Activity, Attempt

log = logging.getLogger(__name__)
MIN_POINTS = 10


class IngestError(ValueError):
    pass


def ingest_track(user: User, track: Track) -> tuple[Activity, bool]:
    """Store a track as an Activity. Returns (activity, created). Duplicate imports return the existing one."""
    if track.external_id:
        existing = Activity.objects.filter(user=user, source=track.source.value, external_id=track.external_id).first()
        if existing:
            return existing, False
    cleaned, _ = clean(track)
    if len(cleaned.points) < MIN_POINTS:
        raise IngestError("This activity has no usable GPS route.")

    latlons = cleaned.latlons()
    proj = LocalProjection.around(latlons)
    simple = [proj.to_latlon(*p) for p in simplify([proj.to_xy(*p) for p in latlons], 5.0)]
    if len(simple) < 2:
        simple = [latlons[0], latlons[-1]]
    try:
        with transaction.atomic():
            activity = Activity.objects.create(
                user=user,
                source=track.source.value,
                external_id=track.external_id,
                device=(track.device or "")[:120],
                sport=track.sport,
                manual=track.manual,
                started_at=track.points[0].t,
                ended_at=track.points[-1].t,
                duration_s=track.duration_s,
                distance_m=round(path_length_m(latlons), 1),
                geometry=line(simple),
                points=[[p.t.timestamp(), p.lat, p.lon, p.ele, p.hr, p.accuracy] for p in track.points],
            )
    except IntegrityError:  # concurrent duplicate import
        return Activity.objects.get(user=user, source=track.source.value, external_id=track.external_id), False
    return activity, True


def candidate_routes(activity: Activity):
    xmin, ymin, xmax, ymax = activity.geometry.extent
    pad = 0.0005  # ~50 m
    box = Polygon.from_bbox((xmin - pad, ymin - pad, xmax + pad, ymax + pad))
    box.srid = 4326
    return Route.objects.filter(status=Route.Status.APPROVED, path__bboverlaps=box)


def process_activity(activity: Activity) -> list[Attempt]:
    """Validate the activity against every nearby approved route and update titles."""
    track = activity.to_track()
    attempts = []
    for route in candidate_routes(activity):
        if Attempt.objects.filter(activity=activity, route=route).exists():
            continue
        res = validate_attempt(track, route.spec())
        if not res.valid and res.reasons in (["no_start"],):
            continue  # just passed nearby, never started the route: don't record anything
        eligible = res.valid and (not activity.is_watch or activity.user.post_watch_runs)
        attempt = Attempt.objects.create(
            activity=activity,
            route=route,
            user=activity.user,
            valid=res.valid,
            eligible=eligible,
            elapsed_s=res.elapsed_s,
            start_time=res.start_time,
            finish_time=res.finish_time,
            distance_m=res.distance_m,
            reasons=res.reasons,
            splits_s=res.splits_s,
            metrics={
                "corridor_ratio": res.corridor_ratio,
                "route_coverage": res.route_coverage,
                "max_sustained_mps": res.max_sustained_mps,
                "checkpoints_hit": res.checkpoints_hit,
            },
        )
        if eligible:
            claim_title(attempt)
        attempts.append(attempt)
    activity.state = Activity.State.PROCESSED
    activity.save(update_fields=["state"])
    return attempts


def claim_title(attempt: Attempt) -> bool:
    """Compare a valid attempt with the route record inside a row lock. Returns True if the title changed."""
    from apps.accounts.tasks import send_push_task

    with transaction.atomic():
        route = Route.objects.select_for_update().get(pk=attempt.route_id)
        prev_best = (
            Attempt.objects.filter(route=route, user=attempt.user, valid=True, eligible=True)
            .exclude(pk=attempt.pk)
            .order_by("elapsed_s")
            .values_list("elapsed_s", flat=True)
            .first()
        )
        is_pb = prev_best is None or attempt.elapsed_s < prev_best
        took = route.record_s is None or attempt.elapsed_s < route.record_s  # ties keep the champion
        previous_holder_id = route.champion_id
        previous_record = route.record_s

        if took:
            route.champion = attempt.user
            route.record_s = attempt.elapsed_s
            route.record_attempt = attempt
            route.champion_since = timezone.now()
            if previous_holder_id and previous_holder_id != attempt.user_id:
                route.title_changes += 1
            route.save(update_fields=["champion", "record_s", "record_attempt", "champion_since", "title_changes"])
            TitleChange.objects.create(
                route=route,
                attempt=attempt,
                new_holder=attempt.user,
                previous_holder_id=previous_holder_id,
                previous_record_s=previous_record,
                new_record_s=attempt.elapsed_s,
            )
        attempt.took_title = took
        attempt.personal_best = is_pb and prev_best is not None
        attempt.save(update_fields=["took_title", "personal_best"])

        if took and previous_holder_id and previous_holder_id != attempt.user_id:
            award(attempt.user, PointsLedger.Kind.CONQUER, attempt, note=route.name)
            gap = previous_record - attempt.elapsed_s
            name = attempt.user.public_name
            transaction.on_commit(
                lambda: send_push_task.delay(
                    previous_holder_id,
                    f"{name} took {route.name}",
                    f"{_fmt(attempt.elapsed_s)}, {gap:.0f} s under your record. Ready to take it back?",
                    {"type": "title_lost", "route": route.slug, "attempt": attempt.pk},
                )
            )
        elif attempt.personal_best:
            award(attempt.user, PointsLedger.Kind.PERSONAL_BEST, attempt, note=route.name)
    return took


def _fmt(seconds: float) -> str:
    m, s = divmod(int(round(seconds)), 60)
    return f"{m}:{s:02d}"
