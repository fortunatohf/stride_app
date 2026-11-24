"""Points and seasons. League points are capped per week so volume alone can't win; XP is uncapped."""

from __future__ import annotations

from datetime import date, timedelta

from django.db import transaction
from django.db.models import F, Sum
from django.utils import timezone

from apps.accounts.models import User

from .models import TIER_ORDER, Division, Membership, PointsLedger, Season, Tier

POINTS = {  # kind: (league points, xp)
    PointsLedger.Kind.CONQUER: (25, 25),
    PointsLedger.Kind.PERSONAL_BEST: (10, 10),
    PointsLedger.Kind.CHALLENGE: (20, 20),
    PointsLedger.Kind.ROUTE_FOUNDED: (0, 30),
    PointsLedger.Kind.SESSION: (0, 5),
}
WEEKLY_CAP = 120
PROMOTE, RELEGATE = 3, 3


def active_season(city: str) -> Season | None:
    return Season.objects.filter(city=city, status=Season.Status.ACTIVE).first()


def membership_for(user: User, season: Season) -> Membership:
    m = Membership.objects.filter(user=user, division__season=season).select_related("division").first()
    if m:
        return m
    div, _ = Division.objects.get_or_create(season=season, tier=Tier.BRONZE, group=1)
    return Membership.objects.create(division=div, user=user)


@transaction.atomic
def award(user: User, kind: str, attempt=None, note: str = "") -> PointsLedger:
    league_pts, xp = POINTS[kind]
    season = active_season(user.city)
    if season and league_pts:
        week_start = timezone.now() - timedelta(days=timezone.now().weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        used = (
            PointsLedger.objects.filter(user=user, season=season, created_at__gte=week_start).aggregate(s=Sum("league_points"))[
                "s"
            ]
            or 0
        )
        league_pts = max(0, min(league_pts, WEEKLY_CAP - used))
    else:
        league_pts = 0
    entry = PointsLedger.objects.create(
        user=user, season=season, kind=kind, league_points=league_pts, xp=xp, attempt=attempt, note=note
    )
    User.objects.filter(pk=user.pk).update(xp=F("xp") + xp)
    if season and league_pts:
        m = membership_for(user, season)
        Membership.objects.filter(pk=m.pk).update(points=F("points") + league_pts)
    return entry


def standings(division: Division) -> list[Membership]:
    return list(division.members.select_related("user").order_by("-points", "user_id"))


@transaction.atomic
def close_season(season: Season, next_start: date | None = None, length_days: int = 42) -> Season:
    """Close a season: top 3 of each division move up a tier, bottom 3 move down. Opens the next season."""
    start = next_start or season.ends_on + timedelta(days=1)
    nxt, _ = Season.objects.get_or_create(
        city=season.city,
        number=season.number + 1,
        defaults={"starts_on": start, "ends_on": start + timedelta(days=length_days - 1), "status": Season.Status.ACTIVE},
    )
    for div in season.divisions.all():
        ranked = standings(div)
        idx = TIER_ORDER.index(Tier(div.tier))
        for pos, m in enumerate(ranked):
            tier = TIER_ORDER[idx]
            if pos < PROMOTE and idx < len(TIER_ORDER) - 1 and m.points > 0:
                tier = TIER_ORDER[idx + 1]
            elif pos >= len(ranked) - RELEGATE and idx > 0 and len(ranked) > PROMOTE + RELEGATE:
                tier = TIER_ORDER[idx - 1]
            new_div, _ = Division.objects.get_or_create(season=nxt, tier=tier, group=1)
            Membership.objects.get_or_create(division=new_div, user=m.user)
    season.status = Season.Status.CLOSED
    season.save(update_fields=["status"])
    return nxt
