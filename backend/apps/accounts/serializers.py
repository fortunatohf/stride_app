from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.common.geo import point

from .models import PrivacyZone, PushToken, User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "display_name", "city", "birth_year", "language"]

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate_birth_year(self, value):
        if value and value > 2026 - 13:
            raise serializers.ValidationError("STRYDE is for runners 13 and older.")
        return value

    def create(self, data):
        return User.objects.create_user(**data)


class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "display_name", "city", "language", "post_watch_runs", "is_premium", "xp"]
        read_only_fields = ["id", "username", "is_premium", "xp"]


class PrivacyZoneSerializer(serializers.ModelSerializer):
    lat = serializers.FloatField(write_only=True)
    lon = serializers.FloatField(write_only=True)

    class Meta:
        model = PrivacyZone
        fields = ["id", "label", "radius_m", "lat", "lon"]

    def create(self, data):
        lat, lon = data.pop("lat"), data.pop("lon")
        return PrivacyZone.objects.create(center=point((lat, lon)), **data)

    def to_representation(self, obj):
        # The center is never echoed back, even to its owner, to keep it off logs and screenshots.
        return {"id": obj.id, "label": obj.label, "radius_m": obj.radius_m}


class PushTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = PushToken
        fields = ["token", "platform"]
