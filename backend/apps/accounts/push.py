"""Expo push notifications. Called from Celery tasks only (never inside a request)."""

import logging

import requests
from django.conf import settings

from .models import PushToken

log = logging.getLogger(__name__)


def send_push(user_id: int, title: str, body: str, data: dict | None = None) -> int:
    tokens = list(PushToken.objects.filter(user_id=user_id).values_list("token", flat=True))
    if not tokens:
        return 0
    messages = [{"to": t, "title": title, "body": body, "data": data or {}, "sound": "default"} for t in tokens]
    try:
        resp = requests.post(settings.EXPO_PUSH_URL, json=messages, timeout=10)
        resp.raise_for_status()
    except requests.RequestException:
        log.exception("push failed for user %s", user_id)
        return 0
    return len(messages)
