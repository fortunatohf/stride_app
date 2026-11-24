from __future__ import annotations

from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from apps.common.geo import latlon, latlons, line, multipoint, point
from apps.leagues.models import PointsLedger
from apps.leagues.services import award
from stryde_core.route_builder import PrivacyZone, build_route
from stryde_core.validator import validate_attempt

from .models import Route


class RouteRejected(ValueError):
    def __init__(self, problems: list[str]):
        super().__init__(", ".join(problems))
        self.problems = problems


def nearby_paths(activity, km: float = 2.0) -> list[list[tuple[float, float]]]:
    """Paths of live or pending routes near this run, for the duplicate check."""
    area = activity.geometry.envelope.buffer(km / 111)  # degrees, roughly km
    qs = Route.objects.exclude(status=Route.Status.REJECTED).filter(path__bboverlaps=area)
    return [latlons(r.path) for r in qs]


def create_route_from_activity(user, activity, name: str) -> Route:
    """Make a pending route from one of the user's runs. Raises RouteRejected with every rule it breaks."""
    if activity.user_id != user.id:
        raise RouteRejected(["not_your_activity"])
    if activity.manual:
        raise RouteRejected(["manual_activity"])
    zones = [PrivacyZone(latlon(z.center), z.radius_m) for z in user.privacy_zones.all()]
    draft = build_route(activity.to_track(), existing=nearby_paths(activity), privacy_zones=zones)
    if not draft.ok:
        raise RouteRejected(draft.problems)
    base = slugify(name)[:80] or "route"
    slug, n = base, 2
    while Route.objects.filter(slug=slug).exists():
        slug, n = f"{base}-{n}", n + 1
    return Route.objects.create(
        name=name[:80],
        slug=slug,
        city=user.city,
        founder=user,
        source_activity=activity,
        path=line(draft.path),
        start=point(draft.start),
        finish=point(draft.finish),
        checkpoints=multipoint(draft.checkpoints),
        distance_m=draft.distance_m,
        is_loop=draft.is_loop,
    )


@transaction.atomic
def approve_route(route: Route) -> Route:
    """Approve a route. The founder's run becomes the first record, judged by the same validator."""
    from apps.activities.models import Attempt
    from apps.activities.services import claim_title

    route.status = Route.Status.APPROVED
    route.approved_at = timezone.now()
    route.save(update_fields=["status", "approved_at"])
    act = route.source_activity
    if act:
        res = validate_attempt(act.to_track(), route.spec())
        if res.valid:
            attempt, _ = Attempt.objects.get_or_create(
                activity=act,
                route=route,
                defaults=dict(
                    user=act.user,
                    valid=True,
                    eligible=True,
                    elapsed_s=res.elapsed_s,
                    start_time=res.start_time,
                    finish_time=res.finish_time,
                    distance_m=res.distance_m,
                    splits_s=res.splits_s,
                ),
            )
            claim_title(attempt)
    if route.founder:
        award(route.founder, PointsLedger.Kind.ROUTE_FOUNDED, note=route.name)
    return route
