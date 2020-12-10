from django.urls import re_path

from zds.notification.api.views import NotificationListAPI

urlpatterns = [
    re_path(r"^$", NotificationListAPI.as_view(), name="list"),
]
