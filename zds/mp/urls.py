from django.urls import re_path

from zds.mp.views import PrivateTopicList, PrivatePostList, PrivateTopicNew, PrivateTopicAddParticipant, \
    PrivateTopicLeaveDetail, PrivateTopicLeaveList, \
    PrivatePostAnswer, PrivatePostEdit, PrivatePostUnread, PrivateTopicEdit


urlpatterns = [
    # Topics.
    re_path(r'^$', PrivateTopicList.as_view(), name='mp-list'),
    re_path(r'^quitter/$', PrivateTopicLeaveList.as_view(),
            name='mp-list-delete'),
    re_path(r'^creer/$', PrivateTopicNew.as_view(), name='mp-new'),

    re_path(r'^(?P<pk>\d+)/(?P<topic_slug>.+)/quitter/$',
            PrivateTopicLeaveDetail.as_view(), name='mp-delete'),
    re_path(r'^(?P<pk>\d+)/(?P<topic_slug>.+)/editer/topic/$',
            PrivateTopicEdit.as_view(), name='mp-edit-topic'),
    re_path(r'^(?P<pk>\d+)/(?P<topic_slug>.+)/editer/participants/$', PrivateTopicAddParticipant.as_view(),
            name='mp-edit-participant'),

    # Posts.
    re_path(r'^(?P<pk>\d+)/(?P<topic_slug>.+)/messages/$',
            PrivatePostList.as_view(), name='private-posts-list'),
    re_path(r'^(?P<pk>\d+)/(?P<topic_slug>.+)/messages/creer/$',
            PrivatePostAnswer.as_view(), name='private-posts-new'),
    re_path(r'^(?P<topic_pk>\d+)/(?P<topic_slug>.+)/messages/(?P<pk>\d+)/editer/$',
            PrivatePostEdit.as_view(), name='private-posts-edit'),
    re_path(r'^message/nonlu/$', PrivatePostUnread.as_view(), name='private-post-unread'),
]
