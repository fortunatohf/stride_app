from django.contrib import admin

from .models import Division, Membership, PointsLedger, Season

admin.site.register(Season)
admin.site.register(Division)
admin.site.register(Membership)


@admin.register(PointsLedger)
class LedgerAdmin(admin.ModelAdmin):
    list_display = ("user", "kind", "league_points", "xp", "created_at")
    list_filter = ("kind",)
