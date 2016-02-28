from django.conf.urls import url

from zds.mp.views import PrivateTopicList, PrivatePostList, PrivateTopicNew, PrivateTopicAddParticipant, \
    PrivateTopicLeaveDetail, PrivateTopicLeaveList, \
    PrivatePostAnswer, PrivatePostEdit, PrivateTopicEdit


urlpatterns = [
    # Topics.
    url(r'^$', PrivateTopicList.as_view(), name='mp-list'),
    url(r'^quitter/$', PrivateTopicLeaveList.as_view(), name='mp-list-delete'),
    url(r'^creer/$', PrivateTopicNew.as_view(), name='mp-new'),

    url(r'^(?P<pk>\d+)/(?P<topic_slug>.+)/quitter/$', PrivateTopicLeaveDetail.as_view(), name='mp-delete'),
    url(r'^(?P<pk>\d+)/(?P<topic_slug>.+)/editer/topic/$', PrivateTopicEdit.as_view(), name='mp-edit-topic'),
    url(r'^(?P<pk>\d+)/(?P<topic_slug>.+)/editer/participants/$', PrivateTopicAddParticipant.as_view(),
        name='mp-edit-participant'),

    # Posts.
    url(r'^(?P<pk>\d+)/(?P<topic_slug>.+)/messages/$', PrivatePostList.as_view(), name='private-posts-list'),
    url(r'^(?P<pk>\d+)/(?P<topic_slug>.+)/messages/creer/$', PrivatePostAnswer.as_view(), name='private-posts-new'),
    url(r'^(?P<topic_pk>\d+)/(?P<topic_slug>.+)/messages/(?P<pk>\d+)/editer/$',
        PrivatePostEdit.as_view(), name='private-posts-edit'),
]
