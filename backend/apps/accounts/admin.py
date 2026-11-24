from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import PrivacyZone, PushToken, User


@admin.register(User)
class StrydeUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("STRYDE", {"fields": ("display_name", "city", "birth_year", "language", "post_watch_runs", "is_premium", "xp")}),
    )
    list_display = ("username", "display_name", "city", "xp", "is_premium")


admin.site.register(PushToken)
admin.site.register(PrivacyZone)
