import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User


@pytest.fixture(autouse=True)
def _eager(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
    from config.celery import app

    app.conf.task_always_eager = True
    app.conf.task_eager_propagates = True


@pytest.fixture
def pushes(monkeypatch):
    sent = []
    monkeypatch.setattr("apps.accounts.tasks.send_push", lambda *a, **k: sent.append(a) or 1)
    return sent


def make_user(username, **kw):
    return User.objects.create_user(username=username, password="Str0ng-pass!", display_name=username.title(), **kw)


def client_for(user) -> APIClient:
    c = APIClient()
    c.force_authenticate(user)
    return c
