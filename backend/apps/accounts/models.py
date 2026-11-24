from datetime import date

from django.contrib.auth.models import AbstractUser
from django.contrib.gis.db import models


class User(AbstractUser):
    display_name = models.CharField(max_length=60, blank=True)
    city = models.CharField(max_length=60, blank=True, default="Austin")
    birth_year = models.PositiveSmallIntegerField(null=True, blank=True)
    language = models.CharField(max_length=5, default="en", choices=[("en", "English"), ("es", "Español")])
    # Watch runs (Apple Health, Garmin...) only post to public leaderboards after the runner agrees.
    post_watch_runs = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)  # cosmetic/analysis features only, never competitive
    xp = models.PositiveIntegerField(default=0)

    @property
    def is_minor(self) -> bool:
        return self.birth_year is not None and date.today().year - self.birth_year < 18

    @property
    def public_name(self) -> str:
        return self.display_name or self.username


class PrivacyZone(models.Model):
    """Areas (e.g. home) where routes cannot start or finish and raw tracks are never shown."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="privacy_zones")
    label = models.CharField(max_length=40, default="Home")
    center = models.PointField(srid=4326)
    radius_m = models.PositiveIntegerField(default=200)


class PushToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="push_tokens")
    token = models.CharField(max_length=200, unique=True)
    platform = models.CharField(max_length=10, choices=[("ios", "iOS"), ("android", "Android")])
    created_at = models.DateTimeField(auto_now_add=True)
