from __future__ import annotations

import logging

import requests
from django.db import transaction
from django.utils import timezone

from apps.activities.services import IngestError, ingest_track
from apps.activities.tasks import process_activity_task
from stryde_core.providers import REGISTRY

from .models import DeviceConnection, WebhookEvent

log = logging.getLogger(__name__)


def http_get(url: str, headers: dict) -> bytes:
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.content


def process_webhook(event: WebhookEvent, http=None) -> int:
    http = http or http_get  # looked up at call time (tests patch it)
    provider = REGISTRY[event.provider]
    created = 0
    errors = []
    for ref in provider.parse_webhook(event.payload):
        conn = (
            DeviceConnection.objects.filter(
                provider=event.provider, external_user_id=ref.external_user_id, status=DeviceConnection.Status.ACTIVE
            )
            .select_related("user")
            .first()
        )
        if not conn:
            errors.append(f"no connection for {ref.external_user_id}")
            continue
        try:
            data = provider.download(ref, conn.access_token, http)
            track = provider.to_track(ref, data)
            if track.sport not in ("running", "walking", "hiking", "generic", "trail_running"):
                continue
            with transaction.atomic():
                activity, is_new = ingest_track(conn.user, track)
                if is_new:
                    created += 1
                    transaction.on_commit(lambda a=activity: process_activity_task.delay(a.pk))
        except (IngestError, requests.RequestException, ValueError) as e:
            log.warning("webhook %s ref %s failed: %s", event.pk, ref.external_id, e)
            errors.append(f"{ref.external_id}: {e}")
    event.processed_at = timezone.now()
    event.activities_created = created
    event.error = "\n".join(errors)[:2000]
    event.save(update_fields=["processed_at", "activities_created", "error"])
    return created
