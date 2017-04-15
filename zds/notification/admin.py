# coding: utf-8

from django.contrib import admin
from zds.notification.models import Notification, Subscription


class NotificationAdmin(admin.ModelAdmin):

    """Representation of Notification model in the admin interface."""

    raw_id_fields = ('subscription', 'sender')


class SubscriptionAdmin(admin.ModelAdmin):

    """Representation of Subscription model in the admin interface."""

    raw_id_fields = ('user', 'last_notification')


admin.site.register(Notification, NotificationAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
