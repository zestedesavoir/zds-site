from django.urls import re_path

from zds.mp.api.views import (
    PrivateTopicListAPI,
    PrivateTopicDetailAPI,
    PrivatePostListAPI,
    PrivatePostDetailAPI,
    PrivateTopicReadAPI,
)

urlpatterns = [
    re_path(r"^$", PrivateTopicListAPI.as_view(), name="list"),
    re_path(r"^(?P<pk>[0-9]+)/?$", PrivateTopicDetailAPI.as_view(), name="detail"),
    re_path(r"^(?P<pk_ptopic>[0-9]+)/messages/$", PrivatePostListAPI.as_view(), name="message-list"),
    re_path(
        r"^(?P<pk_ptopic>[0-9]+)/messages/(?P<pk>[0-9]+)/?$", PrivatePostDetailAPI.as_view(), name="message-detail"
    ),
    re_path(r"^unread/$", PrivateTopicReadAPI.as_view(), name="list-unread"),
]
