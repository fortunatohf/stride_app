from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.db.models import Min
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.activities.models import Activity, Attempt

from .models import Route, TitleChange
from .serializers import (
    CreateRouteSerializer,
    RouteDetailSerializer,
    RouteListSerializer,
)
from .services import RouteRejected, create_route_from_activity


class RouteListCreate(generics.ListAPIView):
    """GET ?lat=&lon=&radius_km= lists approved routes nearby. POST publishes a route from one of your runs."""

    serializer_class = RouteListSerializer

    def get_queryset(self):
        qs = Route.objects.filter(status=Route.Status.APPROVED).select_related("champion")
        p = self.request.query_params
        if "lat" in p and "lon" in p:
            center = Point(float(p["lon"]), float(p["lat"]), srid=4326)
            qs = qs.filter(start__dwithin=(center, D(km=float(p.get("radius_km", 10)))))
        return qs.order_by("-title_changes", "name")

    def post(self, request):
        s = CreateRouteSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        activity = Activity.objects.filter(pk=s.validated_data["activity_id"], user=request.user).first()
        if not activity:
            return Response({"detail": "Activity not found"}, status=404)
        try:
            route = create_route_from_activity(request.user, activity, s.validated_data["name"])
        except RouteRejected as e:
            return Response({"detail": "Route can't be published", "problems": e.problems}, status=400)
        return Response(RouteDetailSerializer(route).data, status=201)


class RouteDetail(generics.RetrieveAPIView):
    serializer_class = RouteDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return Route.objects.filter(status=Route.Status.APPROVED).select_related("champion", "founder")


class LeaderboardView(APIView):
    def get(self, request, slug):
        route = Route.objects.filter(slug=slug, status=Route.Status.APPROVED).first()
        if not route:
            return Response(status=404)
        best = (
            Attempt.objects.filter(route=route, valid=True, eligible=True)
            .values("user_id", "user__display_name", "user__username")
            .annotate(best=Min("elapsed_s"))
            .order_by("best", "user_id")[:100]
        )
        rows = [
            {
                "rank": i + 1,
                "user_id": r["user_id"],
                "name": r["user__display_name"] or r["user__username"],
                "elapsed_s": r["best"],
                "me": r["user_id"] == request.user.id,
            }
            for i, r in enumerate(best)
        ]
        return Response({"route": route.slug, "record_s": route.record_s, "rows": rows})


class MyAlertsView(APIView):
    """Titles the user has lost in the last 14 days and not yet won back (drives the Home card)."""

    def get(self, request):
        from datetime import timedelta

        from django.utils import timezone

        since = timezone.now() - timedelta(days=14)
        changes = (
            TitleChange.objects.filter(previous_holder=request.user, created_at__gte=since)
            .exclude(route__champion=request.user)
            .select_related("route", "new_holder")
            .order_by("-created_at")
        )
        seen, out = set(), []
        for c in changes:
            if c.route_id in seen:
                continue
            seen.add(c.route_id)
            out.append(
                {
                    "type": "title_lost",
                    "route": c.route.slug,
                    "route_name": c.route.name,
                    "distance_m": c.route.distance_m,
                    "by": c.new_holder.public_name,
                    "their_time_s": c.new_record_s,
                    "your_time_s": c.previous_record_s,
                    "at": c.created_at,
                }
            )
        return Response(out)
