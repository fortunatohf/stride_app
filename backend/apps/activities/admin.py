from django.contrib.gis import admin

from .models import Activity, Attempt


@admin.register(Activity)
class ActivityAdmin(admin.GISModelAdmin):
    list_display = ("id", "user", "source", "device", "started_at", "distance_m", "state")
    list_filter = ("source", "state")
    exclude = ("points",)


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "route", "user", "valid", "eligible", "elapsed_s", "took_title", "created_at")
    list_filter = ("valid", "took_title")
