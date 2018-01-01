from django.conf.urls import url

from zds.notification.views import NotificationList, mark_notifications_as_read

urlpatterns = [
    url(r'^$', NotificationList.as_view(), name='notification-list'),
    url(r'^marquer-comme-lues/$', mark_notifications_as_read, name='mark-notifications-as-read'),
]
