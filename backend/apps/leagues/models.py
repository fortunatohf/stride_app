from django.conf import settings
from django.db import models


class Tier(models.TextChoices):
    BRONZE = "bronze", "Bronze"
    SILVER = "silver", "Silver"
    GOLD = "gold", "Gold"
    ELITE = "elite", "Elite"


TIER_ORDER = [Tier.BRONZE, Tier.SILVER, Tier.GOLD, Tier.ELITE]


class Season(models.Model):
    class Status(models.TextChoices):
        UPCOMING = "upcoming"
        ACTIVE = "active"
        CLOSED = "closed"

    city = models.CharField(max_length=60, default="Austin")
    number = models.PositiveIntegerField()
    starts_on = models.DateField()
    ends_on = models.DateField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.UPCOMING)

    class Meta:
        unique_together = [("city", "number")]

    def __str__(self):
        return f"{self.city} season {self.number}"


class Division(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name="divisions")
    tier = models.CharField(max_length=10, choices=Tier.choices)
    group = models.PositiveSmallIntegerField(default=1)  # several groups per tier keep divisions ~30 runners

    class Meta:
        unique_together = [("season", "tier", "group")]


class Membership(models.Model):
    division = models.ForeignKey(Division, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="league_memberships")
    points = models.IntegerField(default=0)

    class Meta:
        unique_together = [("division", "user")]
        ordering = ["-points"]


class PointsLedger(models.Model):
    class Kind(models.TextChoices):
        CONQUER = "conquer"
        PERSONAL_BEST = "pb"
        ROUTE_FOUNDED = "route_founded"
        CHALLENGE = "challenge"
        SESSION = "session"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ledger")
    season = models.ForeignKey(Season, on_delete=models.SET_NULL, null=True, blank=True)
    kind = models.CharField(max_length=20, choices=Kind.choices)
    league_points = models.IntegerField(default=0)
    xp = models.IntegerField(default=0)
    attempt = models.ForeignKey("activities.Attempt", on_delete=models.SET_NULL, null=True, blank=True)
    note = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
