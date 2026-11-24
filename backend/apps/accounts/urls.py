from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

urlpatterns = [
    path("auth/register/", views.RegisterView.as_view()),
    path("auth/token/", TokenObtainPairView.as_view()),
    path("auth/token/refresh/", TokenRefreshView.as_view()),
    path("me/", views.MeView.as_view()),
    path("me/privacy-zones/", views.PrivacyZoneListCreate.as_view()),
    path("me/push-tokens/", views.PushTokenView.as_view()),
]
