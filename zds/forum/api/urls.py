from django.conf.urls import url

from .views import PostKarmaView, ForumListAPI, ForumDetailAPI, PostListAPI, TopicListAPI, TopicDetailAPI, UserTopicListAPI, MemberPostListAPI, UserPostListAPI, PostDetailAPI, PostAlertAPI
urlpatterns = [
    url(r'^$', ForumListAPI.as_view(), name='list'),
    url(r'^(?P<pk>[0-9]+)/?$', ForumDetailAPI.as_view(), name='detail'),
    url(r'^sujets/?$', TopicListAPI.as_view(), name='list-topic'),
    url(r'^membre/sujets/?$', UserTopicListAPI.as_view(), name='list-usertopic'),
    url(r'^message/(?P<pk>\d+)/karma/?$', PostKarmaView.as_view(), name='post-karma'),
    url(r'^sujets/(?P<pk>[0-9]+)/messages?$', PostListAPI.as_view(), name='list-post'),
    url(r'^sujets/(?P<pk>[0-9]+)/?$', TopicDetailAPI.as_view(), name='detail-topic'),
    url(r'^membres/(?P<pk>[0-9]+)/messages/?$', MemberPostListAPI.as_view(), name='list-memberpost'),
    url(r'^membres/messages/?$', UserPostListAPI.as_view(), name='list-userpost'),
    url(r'^sujets/(?P<pk_sujet>[0-9]+)/messages/(?P<pk>[0-9]+)/?$', PostDetailAPI.as_view(), name='detail-post'),
    url(r'^sujets/(?P<pk_sujet>[0-9]+)/messages/(?P<pk>[0-9]+)/alert/?$', PostAlertAPI.as_view(), name='alert-post')
]
