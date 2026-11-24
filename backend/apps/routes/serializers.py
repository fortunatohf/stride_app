from rest_framework import serializers

from apps.common.geo import latlon, latlons

from .models import Route, TitleChange


def _champion(route: Route):
    if not route.champion_id:
        return None
    return {
        "user_id": route.champion_id,
        "name": route.champion.public_name,
        "record_s": route.record_s,
        "since": route.champion_since,
    }


class RouteListSerializer(serializers.ModelSerializer):
    champion = serializers.SerializerMethodField()
    start = serializers.SerializerMethodField()

    class Meta:
        model = Route
        fields = ["slug", "name", "city", "distance_m", "is_loop", "status", "start", "champion", "title_changes"]

    def get_champion(self, obj):
        return _champion(obj)

    def get_start(self, obj):
        return latlon(obj.start)


class TitleChangeSerializer(serializers.ModelSerializer):
    new_holder = serializers.CharField(source="new_holder.public_name")
    previous_holder = serializers.CharField(source="previous_holder.public_name", default=None)

    class Meta:
        model = TitleChange
        fields = ["new_holder", "previous_holder", "previous_record_s", "new_record_s", "created_at"]


class RouteDetailSerializer(RouteListSerializer):
    path = serializers.SerializerMethodField()
    finish = serializers.SerializerMethodField()
    checkpoints = serializers.SerializerMethodField()
    founder = serializers.CharField(source="founder.public_name", default=None)
    history = TitleChangeSerializer(source="title_history", many=True, read_only=True)

    class Meta(RouteListSerializer.Meta):
        fields = RouteListSerializer.Meta.fields + ["path", "finish", "checkpoints", "founder", "history"]

    def get_path(self, obj):
        return latlons(obj.path)

    def get_finish(self, obj):
        return latlon(obj.finish)

    def get_checkpoints(self, obj):
        return [latlon(p) for p in obj.checkpoints]


class CreateRouteSerializer(serializers.Serializer):
    activity_id = serializers.IntegerField()
    name = serializers.CharField(max_length=80)
