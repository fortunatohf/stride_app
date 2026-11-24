from django.db import transaction
from rest_framework import generics, status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from stryde_core.importers import (
    UnsupportedFile,
    from_health_connect,
    from_healthkit,
    import_file,
)
from stryde_core.track import Source, Track, TrackPoint

from .models import Activity, Attempt
from .serializers import (
    ActivitySerializer,
    AppRunSerializer,
    AttemptSerializer,
    FileImportSerializer,
    HealthImportSerializer,
)
from .services import IngestError, ingest_track
from .tasks import process_activity_task


def _ingest_and_queue(user, track):
    activity, created = ingest_track(user, track)
    if created:
        transaction.on_commit(lambda: process_activity_task.delay(activity.pk))
    return activity, created


class UploadThrottleMixin:
    """Rate-limit uploads (POST) only; reads are not throttled."""

    throttle_scope = "uploads"

    def get_throttles(self):
        return [ScopedRateThrottle()] if self.request.method == "POST" else []


class ActivityListCreate(UploadThrottleMixin, generics.ListAPIView):
    serializer_class = ActivitySerializer

    def get_queryset(self):
        return Activity.objects.filter(user=self.request.user).prefetch_related("attempts__route")

    def post(self, request):
        """Upload a run recorded in the app."""
        s = AppRunSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        pts = [
            TrackPoint(p["t"], p["lat"], p["lon"], p.get("alt"), p.get("hr"), p.get("acc")) for p in s.validated_data["points"]
        ]
        track = Track(pts, source=Source.APP, external_id=s.validated_data["client_id"], device=s.validated_data.get("device"))
        try:
            activity, created = _ingest_and_queue(request.user, track)
        except IngestError as e:
            return Response({"detail": str(e)}, status=400)
        return Response({"id": activity.id, "duplicate": not created}, status=201 if created else 200)


class ActivityDetail(generics.RetrieveAPIView):
    serializer_class = ActivitySerializer

    def get_queryset(self):
        return Activity.objects.filter(user=self.request.user)


class FileImportView(UploadThrottleMixin, APIView):
    """Upload a .FIT, .GPX or .TCX exported from any watch."""

    parser_classes = [MultiPartParser]

    def post(self, request):
        s = FileImportSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        f = s.validated_data["file"]
        try:
            track = import_file(f.read(), f.name)
            activity, created = _ingest_and_queue(request.user, track)
        except (UnsupportedFile, IngestError) as e:
            return Response({"detail": str(e)}, status=400)
        except Exception:
            return Response({"detail": "We couldn't read that file."}, status=400)
        return Response({"id": activity.id, "duplicate": not created}, status=201 if created else 200)


class HealthImportView(UploadThrottleMixin, APIView):
    """Workouts read from Apple Health or Health Connect on the phone (Apple Watch, Wear OS, synced brands)."""

    def post(self, request):
        s = HealthImportSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        parse = from_healthkit if s.validated_data["platform"] == "healthkit" else from_health_connect
        results = []
        for payload in s.validated_data["workouts"]:
            try:
                activity, created = _ingest_and_queue(request.user, parse(payload))
                results.append({"id": activity.id, "duplicate": not created})
            except (IngestError, KeyError, ValueError) as e:
                results.append({"error": str(e)})
        return Response({"results": results}, status=status.HTTP_200_OK)


class MyAttemptsView(generics.ListAPIView):
    serializer_class = AttemptSerializer

    def get_queryset(self):
        return Attempt.objects.filter(user=self.request.user).select_related("route")
