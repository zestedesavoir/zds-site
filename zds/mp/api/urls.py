from django.conf.urls import url

from zds.mp.api.views import PrivateTopicListAPI, PrivateTopicDetailAPI, PrivatePostListAPI, PrivatePostDetailAPI, \
    PrivateTopicReadAPI

urlpatterns = [
    url(r'^$', PrivateTopicListAPI.as_view(), name='list'),
    url(r'^(?P<pk>[0-9]+)/?$', PrivateTopicDetailAPI.as_view(), name='detail'),
    url(r'^(?P<pk_ptopic>[0-9]+)/messages/$', PrivatePostListAPI.as_view(), name='message-list'),
    url(r'^(?P<pk_ptopic>[0-9]+)/messages/(?P<pk>[0-9]+)/?$', PrivatePostDetailAPI.as_view(), name='message-detail'),
    url(r'^unread/$', PrivateTopicReadAPI.as_view(), name='list-unread'),
]
