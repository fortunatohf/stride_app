from django.contrib import admin

from .models import TrainingPlan, TrainingSession


class SessionInline(admin.TabularInline):
    model = TrainingSession
    extra = 0


@admin.register(TrainingPlan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "kind", "starts_on", "attempt_on", "active")
    inlines = [SessionInline]
