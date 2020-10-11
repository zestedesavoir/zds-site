from django.urls import re_path

from zds.forum import feeds
from zds.forum.views import CategoriesForumsListView, ForumCategoryForumsDetailView, ForumTopicsListView, \
    TopicPostsListView, TopicNew, TopicEdit, FindTopic, FindTopicByTag, PostNew, PostEdit, PostSignal, \
    PostPotentialSpam, PostUseful, PostUnread, FindPost, solve_alert, ManageGitHubIssue, LastTopicsListView, \
    FindFollowedTopic

urlpatterns = [

    # Feeds
    re_path(r'^flux/messages/rss/$',
            feeds.LastPostsFeedRSS(), name='post-feed-rss'),
    re_path(r'^flux/messages/atom/$',
            feeds.LastPostsFeedATOM(), name='post-feed-atom'),

    re_path(r'^flux/sujets/rss/$', feeds.LastTopicsFeedRSS(),
            name='topic-feed-rss'),
    re_path(r'^flux/sujets/atom/$', feeds.LastTopicsFeedATOM(),
            name='topic-feed-atom'),

    # Developers warning: if you update something here, check and update help_text
    # on ForumCategory slug field

    # Moderation
    re_path(r'^resolution_alerte/$', solve_alert, name='forum-solve-alert'),

    # Viewing a thread
    re_path(r'^sujet/nouveau/$', TopicNew.as_view(), name='topic-new'),
    re_path(r'^sujet/editer/$', TopicEdit.as_view(), name='topic-edit'),
    re_path(r'^sujet/github/(?P<pk>\d+)/$',
            ManageGitHubIssue.as_view(), name='manage-issue'),
    re_path(r'^sujet/(?P<topic_pk>\d+)/(?P<topic_slug>.+)/$',
            TopicPostsListView.as_view(), name='topic-posts-list'),
    re_path(r'^sujets/membre/(?P<user_pk>\d+)/$',
            FindTopic.as_view(), name='topic-find'),
    re_path(r'^sujets/suivis/$',
            FindFollowedTopic.as_view(), name='followed-topic-find'),

    # The first is kept for URL backward-compatibility.
    re_path(r'^sujets/tag/(?P<tag_pk>\d+)/(?P<tag_slug>.+)/$',
            FindTopicByTag.as_view(), name='old-topic-tag-find'),
    re_path(r'^sujets/tag/(?P<tag_slug>.+)/$',
            FindTopicByTag.as_view(), name='topic-tag-find'),

    # Message-related
    re_path(r'^message/nouveau/$', PostNew.as_view(), name='post-new'),
    re_path(r'^message/editer/$', PostEdit.as_view(), name='post-edit'),
    re_path(r'^message/utile/$', PostUseful.as_view(), name='post-useful'),
    re_path(r'^message/signaler/$', PostSignal.as_view(),
            name='post-create-alert'),
    re_path(r'^message/spam-potentiel/$', PostPotentialSpam.as_view(),
            name='post-potential-spam'),
    re_path(r'^message/nonlu/$', PostUnread.as_view(), name='post-unread'),
    re_path(r'^messages/(?P<user_pk>\d+)/$',
            FindPost.as_view(), name='post-find'),

    # Last subjects.
    re_path(r'^derniers-sujets/$',
            LastTopicsListView.as_view(), name='last-subjects'),

    # Categories and forums list.
    re_path(r'^$', CategoriesForumsListView.as_view(), name='cats-forums-list'),

    # Forum details
    re_path(r'^(?P<cat_slug>.+)/(?P<forum_slug>.+)/$',
            ForumTopicsListView.as_view(), name='forum-topics-list'),

    # Forums belonging to one category
    re_path(r'^(?P<slug>.+)/$', ForumCategoryForumsDetailView.as_view(),
            name='cat-forums-list'),
]
