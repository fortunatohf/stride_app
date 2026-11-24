"""Demo data for building the app: a season, three runners and an approved Zilker Loop with a title fight.

    python manage.py seed_demo

Logins: ana / luis / sofia, password "stryde-demo-123".
"""

import math
from datetime import date, datetime, timedelta, timezone

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import User
from apps.activities.services import ingest_track, process_activity
from apps.leagues.models import Season
from apps.routes.services import approve_route, create_route_from_activity
from stryde_core.geo import LocalProjection
from stryde_core.track import Track, TrackPoint

PROJ = LocalProjection(30.2669, -97.7729)  # Zilker Park, Austin


def loop_track(speed_mps: float, t0: datetime, a=1000, b=600) -> Track:
    n, pts = 400, []
    ring = [
        (a * math.cos(-math.pi / 2 + 2 * math.pi * i / n), b * math.sin(-math.pi / 2 + 2 * math.pi * i / n)) for i in range(n + 1)
    ]
    seg = [math.dist(ring[i], ring[i + 1]) for i in range(n)]
    t = 0.0
    for i in range(n):
        steps = max(1, int(seg[i] / speed_mps))
        for s in range(steps):
            f = s / steps
            x = ring[i][0] + f * (ring[i + 1][0] - ring[i][0])
            y = ring[i][1] + f * (ring[i + 1][1] - ring[i][1])
            lat, lon = PROJ.to_latlon(x, y)
            pts.append(TrackPoint(t0 + timedelta(seconds=t), lat, lon, accuracy=5.0))
            t += seg[i] / steps / speed_mps
    lat, lon = PROJ.to_latlon(*ring[-1])
    pts.append(TrackPoint(t0 + timedelta(seconds=t), lat, lon, accuracy=5.0))
    return Track(pts)


class Command(BaseCommand):
    help = "Create demo users, a season and an approved route with a title history."

    @transaction.atomic
    def handle(self, *args, **opts):
        today = date.today()
        Season.objects.get_or_create(
            city="Austin",
            number=1,
            defaults={"starts_on": today - timedelta(days=28), "ends_on": today + timedelta(days=13), "status": "active"},
        )
        users = {}
        for name in ("ana", "luis", "sofia"):
            u, created = User.objects.get_or_create(username=name, defaults={"display_name": name.title(), "city": "Austin"})
            if created:
                u.set_password("stryde-demo-123")
                u.save()
            users[name] = u

        t0 = datetime.now(timezone.utc) - timedelta(days=5)
        founding = loop_track(2.82, t0)
        founding.external_id = "seed-ana-1"
        act, _ = ingest_track(users["ana"], founding)
        if not act.user.founded_routes.exists():
            route = create_route_from_activity(users["ana"], act, "Zilker Loop")
            approve_route(route)
        for name, speed, days, cid in (("sofia", 2.75, 4, "seed-sofia-1"), ("luis", 2.9, 2, "seed-luis-1")):
            tr = loop_track(speed, datetime.now(timezone.utc) - timedelta(days=days))
            tr.external_id = cid
            a, created = ingest_track(users[name], tr)
            if created:
                process_activity(a)
        self.stdout.write(self.style.SUCCESS("Demo data ready. Log in as ana / luis / sofia, password stryde-demo-123"))
