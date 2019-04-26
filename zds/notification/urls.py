from django.urls import re_path

from zds.notification.views import NotificationList, mark_notifications_as_read
from zds.notification.feeds import MemberNotificationFeed, MemberNotificationAtomFeed
urlpatterns = [
    re_path(r'^$', NotificationList.as_view(), name='notification-list'),
    re_path(r'^marquer-comme-lues/$', mark_notifications_as_read,
            name='mark-notifications-as-read'),
    re_path(r'^/flux/rss/(?P<token>[a-zA-Z0-9]+)/$', MemberNotificationFeed(), name='rss'),
    re_path(r'^/flux/rss/(?P<token>[a-zA-Z0-9]+)/$', MemberNotificationAtomFeed(), name='atom'),
]
