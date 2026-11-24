from datetime import datetime, timezone

from django.conf import settings
from django.contrib.gis.db import models

from stryde_core.track import Source, Track, TrackPoint


class Activity(models.Model):
    class State(models.TextChoices):
        RECEIVED = "received"
        PROCESSED = "processed"
        FAILED = "failed"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="activities")
    source = models.CharField(max_length=20, choices=[(s.value, s.value) for s in Source], db_index=True)
    external_id = models.CharField(max_length=120, null=True, blank=True)
    device = models.CharField(max_length=120, blank=True)
    sport = models.CharField(max_length=30, default="running")
    manual = models.BooleanField(default=False)
    started_at = models.DateTimeField(db_index=True)
    ended_at = models.DateTimeField()
    duration_s = models.FloatField()
    distance_m = models.FloatField()
    geometry = models.LineStringField(srid=4326)  # simplified, for display and route lookup
    points = models.JSONField()  # compact raw points: [[epoch, lat, lon, ele, hr, acc], ...]
    state = models.CharField(max_length=10, choices=State.choices, default=State.RECEIVED)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-started_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "source", "external_id"],
                condition=models.Q(external_id__isnull=False),
                name="uniq_external_activity",
            )
        ]

    @property
    def is_watch(self) -> bool:
        return self.source != Source.APP.value

    def to_track(self) -> Track:
        pts = [TrackPoint(datetime.fromtimestamp(p[0], tz=timezone.utc), p[1], p[2], p[3], p[4], p[5]) for p in self.points]
        return Track(
            pts,
            source=Source(self.source),
            external_id=self.external_id,
            device=self.device,
            sport=self.sport,
            manual=self.manual,
        )


class Attempt(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="attempts")
    route = models.ForeignKey("routes.Route", on_delete=models.CASCADE, related_name="attempts")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="attempts")
    valid = models.BooleanField(db_index=True)
    eligible = models.BooleanField(default=True)  # valid but not posted (e.g. watch run without consent)
    elapsed_s = models.FloatField(null=True)
    start_time = models.DateTimeField(null=True)
    finish_time = models.DateTimeField(null=True)
    distance_m = models.FloatField(null=True)
    reasons = models.JSONField(default=list)
    splits_s = models.JSONField(default=list)
    metrics = models.JSONField(default=dict)
    took_title = models.BooleanField(default=False)
    personal_best = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["activity", "route"], name="uniq_attempt_per_route")]
        indexes = [models.Index(fields=["route", "valid", "elapsed_s"])]
