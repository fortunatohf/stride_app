from django.conf import settings
from django.db import models

from apps.common.fields import EncryptedTextField


class DeviceConnection(models.Model):
    """A user's linked watch-platform account (Garmin, Polar, COROS, Suunto)."""

    class Status(models.TextChoices):
        ACTIVE = "active"
        REVOKED = "revoked"
        ERROR = "error"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="device_connections")
    provider = models.CharField(max_length=20)
    external_user_id = models.CharField(max_length=120)
    access_token = EncryptedTextField(blank=True)
    refresh_token = EncryptedTextField(blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    connected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["provider", "external_user_id"], name="uniq_provider_user")]


class WebhookEvent(models.Model):
    """Every webhook is stored first, answered 200 fast, then processed by a worker (retries are safe)."""

    provider = models.CharField(max_length=20)
    payload = models.JSONField()
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    activities_created = models.PositiveIntegerField(default=0)
    error = models.TextField(blank=True)
