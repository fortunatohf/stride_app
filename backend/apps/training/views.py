from django.utils import timezone
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.leagues.models import PointsLedger
from apps.leagues.services import award
from apps.routes.models import Route

from .models import TrainingPlan, TrainingSession
from .services import create_comeback_plan


class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingSession
        fields = ["id", "date", "kind", "title", "detail", "minutes", "completed_at"]


class PlanSerializer(serializers.ModelSerializer):
    sessions = SessionSerializer(many=True, read_only=True)
    route = serializers.SlugRelatedField(slug_field="slug", read_only=True)

    class Meta:
        model = TrainingPlan
        fields = ["id", "kind", "title", "route", "goal_time_s", "starts_on", "attempt_on", "sessions"]


class CurrentPlanView(APIView):
    def get(self, request):
        plan = TrainingPlan.objects.filter(user=request.user, active=True).prefetch_related("sessions").first()
        return Response(PlanSerializer(plan).data if plan else None)


class ComebackPlanView(APIView):
    def post(self, request):
        route = Route.objects.filter(slug=request.data.get("route"), status=Route.Status.APPROVED).first()
        if not route or route.record_s is None:
            return Response({"detail": "Route not found"}, status=404)
        plan = create_comeback_plan(request.user, route)
        return Response(PlanSerializer(plan).data, status=201)


class CompleteSessionView(APIView):
    def post(self, request, pk):
        s = TrainingSession.objects.filter(pk=pk, plan__user=request.user).first()
        if not s:
            return Response(status=404)
        if not s.completed_at:
            s.completed_at = timezone.now()
            s.save(update_fields=["completed_at"])
            award(request.user, PointsLedger.Kind.SESSION, note=s.title)
        return Response(SessionSerializer(s).data)
