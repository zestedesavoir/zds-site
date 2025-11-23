from django.contrib import admin

from zds.notification.models import Notification, Subscription


class NotificationAdmin(admin.ModelAdmin):
    """Representation of Notification model in the admin interface."""

    list_display = ("subscription", "pubdate", "is_read", "is_dead", "sender")
    list_filter = ("is_read", "is_dead")
    search_fields = ("subscription__user__username", "sender__username", "url", "title")
    raw_id_fields = ("subscription", "sender")


class SubscriptionAdmin(admin.ModelAdmin):
    """Representation of Subscription model in the admin interface."""

    list_display = ("user", "pubdate", "is_active", "by_email")
    list_filter = ("is_active", "by_email")
    search_fields = ("user__username",)
    raw_id_fields = ("user", "last_notification")


admin.site.register(Notification, NotificationAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
