from django.urls import re_path

from zds.notification.views import NotificationList, mark_notifications_as_read

urlpatterns = [
    re_path(r"^$", NotificationList.as_view(), name="notification-list"),
    re_path(r"^marquer-comme-lues/$", mark_notifications_as_read, name="mark-notifications-as-read"),
]
