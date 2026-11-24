from django.urls import path

from . import views

urlpatterns = [
    path("activities/", views.ActivityListCreate.as_view()),
    path("activities/<int:pk>/", views.ActivityDetail.as_view()),
    path("activities/import-file/", views.FileImportView.as_view()),
    path("activities/health/", views.HealthImportView.as_view()),
    path("attempts/", views.MyAttemptsView.as_view()),
]
