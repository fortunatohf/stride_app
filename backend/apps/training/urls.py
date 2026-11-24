from django.urls import path

from . import views

urlpatterns = [
    path("training/current/", views.CurrentPlanView.as_view()),
    path("training/comeback/", views.ComebackPlanView.as_view()),
    path("training/sessions/<int:pk>/complete/", views.CompleteSessionView.as_view()),
]
