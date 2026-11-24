from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", lambda r: JsonResponse({"ok": True})),
    path("api/", include("apps.accounts.urls")),
    path("api/", include("apps.routes.urls")),
    path("api/", include("apps.activities.urls")),
    path("api/", include("apps.leagues.urls")),
    path("api/", include("apps.training.urls")),
    path("api/", include("apps.integrations.urls")),
]
