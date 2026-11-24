from django.conf import settings
from django.db import models


class TrainingPlan(models.Model):
    class Kind(models.TextChoices):
        COMEBACK = "comeback", "Comeback (win back a route)"
        GENERAL = "general", "General"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="plans")
    kind = models.CharField(max_length=10, choices=Kind.choices)
    title = models.CharField(max_length=100)
    route = models.ForeignKey("routes.Route", on_delete=models.SET_NULL, null=True, blank=True)
    goal_time_s = models.FloatField(null=True, blank=True)
    starts_on = models.DateField()
    attempt_on = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class TrainingSession(models.Model):
    class Kind(models.TextChoices):
        REST = "rest"
        EASY = "easy"
        TEMPO = "tempo"
        INTERVALS = "intervals"
        SHAKEOUT = "shakeout"
        ATTEMPT = "attempt"

    plan = models.ForeignKey(TrainingPlan, on_delete=models.CASCADE, related_name="sessions")
    date = models.DateField()
    kind = models.CharField(max_length=10, choices=Kind.choices)
    title = models.CharField(max_length=80)
    detail = models.CharField(max_length=160, blank=True)
    minutes = models.PositiveSmallIntegerField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["date"]
