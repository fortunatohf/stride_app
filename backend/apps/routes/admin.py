from django.contrib import messages
from django.contrib.gis import admin

from .models import Route, TitleChange
from .services import approve_route


@admin.register(Route)
class RouteAdmin(admin.GISModelAdmin):
    """The review queue: filter by status=pending, check the map, then approve or reject."""

    list_display = ("name", "city", "status", "distance_m", "founder", "champion", "record_s", "created_at")
    list_filter = ("status", "city")
    search_fields = ("name", "slug")
    readonly_fields = ("champion", "record_s", "record_attempt", "champion_since", "title_changes", "source_activity")
    actions = ["approve", "reject"]

    @admin.action(description="Approve selected routes")
    def approve(self, request, queryset):
        for route in queryset.filter(status=Route.Status.PENDING):
            approve_route(route)
        messages.success(request, "Approved.")

    @admin.action(description="Reject selected routes")
    def reject(self, request, queryset):
        queryset.update(status=Route.Status.REJECTED)


admin.site.register(TitleChange)
