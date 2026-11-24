import secrets

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from stryde_core.providers import REGISTRY, ProviderStatus

from .models import DeviceConnection, WebhookEvent
from .tasks import process_webhook_task

# Connected through the phone (no server keys needed). Listed so the app can show one "Connect" screen.
ON_DEVICE = [
    {
        "key": "apple_health",
        "name": "Apple Health",
        "covers": "Apple Watch, and Garmin/COROS/Polar/Suunto when synced to Apple Health",
        "status": "ready",
        "platform": "ios",
    },
    {
        "key": "health_connect",
        "name": "Health Connect",
        "covers": "Wear OS, Galaxy Watch, Pixel Watch and brands that sync to it",
        "status": "ready",
        "platform": "android",
    },
    {"key": "file", "name": "Upload a file", "covers": "Any watch: .FIT, .GPX or .TCX", "status": "ready", "platform": "all"},
]


class ProviderListView(APIView):
    def get(self, request):
        mine = {c.provider: c.status for c in DeviceConnection.objects.filter(user=request.user)}
        cloud = [
            {
                "key": p.key,
                "name": p.name,
                "status": p.status.value,
                "available": p.status != ProviderStatus.SCAFFOLD and bool(settings.PROVIDERS[p.key]["client_id"]),
                "connected": mine.get(p.key) == DeviceConnection.Status.ACTIVE,
            }
            for p in REGISTRY.values()
        ]
        return Response({"on_device": ON_DEVICE, "cloud": cloud, "post_watch_runs": request.user.post_watch_runs})


class ConnectView(APIView):
    """Returns the brand's consent URL. The callback (after keys are issued) exchanges the code for tokens."""

    def get(self, request, provider):
        p = REGISTRY.get(provider)
        cfg = settings.PROVIDERS.get(provider, {})
        if not p or not cfg.get("client_id"):
            return Response({"detail": f"{provider} is not available yet"}, status=400)
        state = secrets.token_urlsafe(24)
        cache.set(f"oauth:{state}", {"user": request.user.id, "provider": provider}, 600)
        redirect = f"{settings.PUBLIC_BASE_URL}/api/integrations/{provider}/callback/"
        return Response({"url": p.authorize_url(cfg["client_id"], redirect, state)})


class WebhookView(APIView):
    """Brand -> STRYDE push. Store, answer 200 quickly, process in the worker."""

    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request, provider, secret):
        if provider not in REGISTRY or not secrets.compare_digest(secret, settings.WEBHOOK_SECRET):
            return Response(status=404)
        event = WebhookEvent.objects.create(provider=provider, payload=request.data)
        transaction.on_commit(lambda: process_webhook_task.delay(event.pk))
        return Response({"ok": True})

    def get(self, request, provider, secret):
        # Some providers verify the endpoint with a GET before enabling pushes.
        if provider not in REGISTRY or not secrets.compare_digest(secret, settings.WEBHOOK_SECRET):
            return Response(status=404)
        return Response({"ok": True})
