from django.conf.urls import url

from zds.notification.api.views import NotificationListAPI

urlpatterns = [
    url(r'^$', NotificationListAPI.as_view(), name='list'),
]
