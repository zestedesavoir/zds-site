from django.contrib import admin
from zds.notification.models import Notification, Subscription


admin.site.register(Notification)
admin.site.register(Subscription)
