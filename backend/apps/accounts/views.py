from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PushToken
from .serializers import (
    MeSerializer,
    PrivacyZoneSerializer,
    PushTokenSerializer,
    RegisterSerializer,
)


class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = MeSerializer

    def get_object(self):
        return self.request.user


class PrivacyZoneListCreate(generics.ListCreateAPIView):
    serializer_class = PrivacyZoneSerializer
    pagination_class = None

    def get_queryset(self):
        return self.request.user.privacy_zones.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PushTokenView(APIView):
    def post(self, request):
        s = PushTokenSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        PushToken.objects.update_or_create(
            token=s.validated_data["token"], defaults={"user": request.user, "platform": s.validated_data["platform"]}
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
