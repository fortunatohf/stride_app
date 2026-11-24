from django.conf import settings
from django.contrib.gis.db import models

from apps.common.geo import latlon, latlons
from stryde_core.validator import RouteSpec


class Route(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        RETIRED = "retired", "Retired"

    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=100, unique=True)
    city = models.CharField(max_length=60, default="Austin")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True)
    founder = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="founded_routes")
    source_activity = models.ForeignKey("activities.Activity", on_delete=models.SET_NULL, null=True, blank=True, related_name="+")

    path = models.LineStringField(srid=4326)
    start = models.PointField(srid=4326)
    finish = models.PointField(srid=4326)
    checkpoints = models.MultiPointField(srid=4326)
    distance_m = models.FloatField()
    is_loop = models.BooleanField(default=False)

    champion = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="titles"
    )
    record_s = models.FloatField(null=True, blank=True)
    record_attempt = models.ForeignKey("activities.Attempt", on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    champion_since = models.DateTimeField(null=True, blank=True)
    title_changes = models.PositiveIntegerField(default=0)

    review_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["city", "status"])]

    def __str__(self):
        return self.name

    def spec(self) -> RouteSpec:
        return RouteSpec(
            path=latlons(self.path),
            start=latlon(self.start),
            finish=latlon(self.finish),
            checkpoints=[latlon(p) for p in self.checkpoints],
            distance_m=self.distance_m,
        )


class TitleChange(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name="title_history")
    attempt = models.ForeignKey("activities.Attempt", on_delete=models.CASCADE, related_name="+")
    new_holder = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    previous_holder = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    previous_record_s = models.FloatField(null=True)
    new_record_s = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
