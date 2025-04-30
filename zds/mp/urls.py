from django.urls import path
from django.views.generic.base import RedirectView

from zds.mp.views import (
    PrivatePostAnswer,
    PrivatePostEdit,
    PrivatePostList,
    PrivatePostUnread,
    PrivateTopicAddParticipant,
    PrivateTopicEdit,
    PrivateTopicLeaveDetail,
    PrivateTopicLeaveList,
    PrivateTopicList,
    PrivateTopicNew,
)

app_name = "mp"

urlpatterns = [
    # Routes related to the set of topics
    path("", PrivateTopicList.as_view(), name="list"),
    path("quitter/", PrivateTopicLeaveList.as_view(), name="list-delete"),
    path("creer/", PrivateTopicNew.as_view(), name="create"),
    # Routes related to a single existing topic
    path("<int:pk>/<slug:topic_slug>/", PrivatePostList.as_view(), name="view"),
    path(
        "<int:pk>/<slug:topic_slug>/messages/",
        RedirectView.as_view(pattern_name="mp:view", permanent=True),
        name="old-view",
    ),
    path("<int:pk>/<slug:topic_slug>/repondre/", PrivatePostAnswer.as_view(), name="answer"),
    path("<int:pk>/<slug:topic_slug>/quitter/", PrivateTopicLeaveDetail.as_view(), name="leave"),
    path("<int:pk>/<slug:topic_slug>/modifier/", PrivateTopicEdit.as_view(), name="edit"),
    path(
        "<int:pk>/<slug:topic_slug>/modifier/participants/",
        PrivateTopicAddParticipant.as_view(),
        name="edit-participant",
    ),
    # Routes related to a single message
    path("message/<int:pk>/modifier/", PrivatePostEdit.as_view(), name="post-edit"),
    path("message/<int:pk>/marquer-non-lu/", PrivatePostUnread.as_view(), name="mark-post-unread"),
]
