from django.urls import path

from zds.notification.views import NotificationList, mark_notifications_as_read

app_name = "notification"

urlpatterns = [
    path("", NotificationList.as_view(), name="list"),
    path("marquer-comme-lues/", mark_notifications_as_read, name="mark-as-read"),
]
