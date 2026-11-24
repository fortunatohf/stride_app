from django.urls import path

from . import views

urlpatterns = [
    path("me/alerts/", views.MyAlertsView.as_view()),
    path("routes/", views.RouteListCreate.as_view()),
    path("routes/<slug:slug>/", views.RouteDetail.as_view()),
    path("routes/<slug:slug>/leaderboard/", views.LeaderboardView.as_view()),
]
