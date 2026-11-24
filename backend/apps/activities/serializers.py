from rest_framework import serializers

from .models import Activity, Attempt


class AppPointSerializer(serializers.Serializer):
    t = serializers.DateTimeField()
    lat = serializers.FloatField(min_value=-90, max_value=90)
    lon = serializers.FloatField(min_value=-180, max_value=180)
    alt = serializers.FloatField(required=False, allow_null=True)
    acc = serializers.FloatField(required=False, allow_null=True)
    hr = serializers.IntegerField(required=False, allow_null=True)


class AppRunSerializer(serializers.Serializer):
    """A run recorded by the STRYDE app's native recorder."""

    client_id = serializers.CharField(max_length=120)  # UUID made on the phone: makes uploads idempotent
    device = serializers.CharField(max_length=120, required=False, allow_blank=True)
    points = AppPointSerializer(many=True)

    def validate_points(self, pts):
        if len(pts) < 10:
            raise serializers.ValidationError("Run is too short to save.")
        if len(pts) > 40_000:
            raise serializers.ValidationError("Run has too many points.")
        return pts


class HealthImportSerializer(serializers.Serializer):
    platform = serializers.ChoiceField(choices=["healthkit", "health_connect"])
    workouts = serializers.ListField(child=serializers.DictField(), max_length=20)


class FileImportSerializer(serializers.Serializer):
    file = serializers.FileField()


class AttemptSerializer(serializers.ModelSerializer):
    route = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    route_name = serializers.CharField(source="route.name", read_only=True)

    class Meta:
        model = Attempt
        fields = [
            "id",
            "route",
            "route_name",
            "valid",
            "eligible",
            "elapsed_s",
            "distance_m",
            "reasons",
            "splits_s",
            "took_title",
            "personal_best",
            "start_time",
            "created_at",
        ]


class ActivitySerializer(serializers.ModelSerializer):
    attempts = AttemptSerializer(many=True, read_only=True)
    path = serializers.SerializerMethodField()

    class Meta:
        model = Activity
        fields = ["id", "source", "device", "sport", "started_at", "duration_s", "distance_m", "state", "path", "attempts"]

    def get_path(self, obj):
        # Simplified line only; raw points never leave the server.
        return [[y, x] for x, y in obj.geometry.coords]
