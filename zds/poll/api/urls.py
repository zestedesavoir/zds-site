# coding: utf-8

from django.conf.urls import url

from zds.poll.api.views import PollListAPIView, PollDetailAPIView

urlpatterns = [
    url(r'^$', PollListAPIView.as_view(), name='list'),
    url(r'^(?P<poll__id>[0-9]+)/$', PollDetailAPIView.as_view(), name='detail'),
]