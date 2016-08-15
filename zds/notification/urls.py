# coding: utf-8

from django.conf.urls import url

from zds.notification.views import NotificationList

urlpatterns = [
    url(r'^$', NotificationList.as_view(), name='notification-list'),
]
