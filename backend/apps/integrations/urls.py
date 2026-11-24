from django.urls import path

from . import views

urlpatterns = [
    path("integrations/", views.ProviderListView.as_view()),
    path("integrations/<str:provider>/connect/", views.ConnectView.as_view()),
    path("integrations/<str:provider>/webhook/<str:secret>/", views.WebhookView.as_view()),
]
