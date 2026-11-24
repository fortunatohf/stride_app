from django.urls import path

from .views import CurrentLeagueView

urlpatterns = [path("leagues/current/", CurrentLeagueView.as_view())]
