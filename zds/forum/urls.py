# coding: utf-8

from django.conf.urls import url

from zds.forum import feeds
from zds.forum.views import CategoriesForumsListView, CategoryForumsDetailView, ForumTopicsListView, \
    TopicPostsListView, TopicNew, TopicEdit, FindTopic, FindTopicByTag, PostNew, PostEdit, \
    PostUseful, PostUnread, FindPost, solve_alert, ManageGitHubIssue

urlpatterns = [

    # Feeds
    url(r'^flux/messages/rss/$', feeds.LastPostsFeedRSS(), name='post-feed-rss'),
    url(r'^flux/messages/atom/$', feeds.LastPostsFeedATOM(), name='post-feed-atom'),

    url(r'^flux/sujets/rss/$', feeds.LastTopicsFeedRSS(), name='topic-feed-rss'),
    url(r'^flux/sujets/atom/$', feeds.LastTopicsFeedATOM(), name='topic-feed-atom'),

    # Developers warning: if you update something here, check and update help_text
    # on Category slug field

    # Moderation
    url(r'^resolution_alerte/$', solve_alert, name='forum-solve-alert'),

    # Viewing a thread
    url(r'^sujet/nouveau/$', TopicNew.as_view(), name='topic-new'),
    url(r'^sujet/editer/$', TopicEdit.as_view(), name='topic-edit'),
    url(r'^sujet/github/(?P<pk>\d+)/$', ManageGitHubIssue.as_view(), name='manage-issue'),
    url(r'^sujet/(?P<topic_pk>\d+)/(?P<topic_slug>.+)/$', TopicPostsListView.as_view(), name='topic-posts-list'),
    url(r'^sujets/membre/(?P<user_pk>\d+)/$', FindTopic.as_view(), name='topic-find'),
    url(r'^sujets/tag/(?P<tag_pk>\d+)/(?P<tag_slug>.+)/$', FindTopicByTag.as_view(), name='topic-tag-find'),

    # Message-related
    url(r'^message/nouveau/$', PostNew.as_view(), name='post-new'),
    url(r'^message/editer/$', PostEdit.as_view(), name='post-edit'),
    url(r'^message/utile/$', PostUseful.as_view(), name='post-useful'),
    url(r'^message/nonlu/$', PostUnread.as_view(), name='post-unread'),
    url(r'^messages/(?P<user_pk>\d+)/$', FindPost.as_view(), name='post-find'),

    # Categories and forums list.
    url(r'^$', CategoriesForumsListView.as_view(), name='cats-forums-list'),

    # Forum details
    url(r'^(?P<cat_slug>.+)/(?P<forum_slug>.+)/$', ForumTopicsListView.as_view(), name='forum-topics-list'),

    # Forums belonging to one category
    url(r'^(?P<slug>.+)/$', CategoryForumsDetailView.as_view(), name='cat-forums-list'),
]
