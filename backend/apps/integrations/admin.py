from django.contrib import admin

from .models import DeviceConnection, WebhookEvent


@admin.register(DeviceConnection)
class DeviceConnectionAdmin(admin.ModelAdmin):
    list_display = ("user", "provider", "external_user_id", "status", "connected_at")
    exclude = ("access_token", "refresh_token")


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ("provider", "received_at", "processed_at", "activities_created")
