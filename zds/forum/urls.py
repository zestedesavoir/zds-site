from django.urls import path

from zds.forum import feeds
from zds.forum.views import (
    CategoriesForumsListView,
    FindFollowedTopic,
    FindPost,
    FindTopic,
    FindTopicByTag,
    ForumCategoryForumsDetailView,
    ForumTopicsListView,
    LastTopicsListView,
    ManageGitHubIssue,
    PostEdit,
    PostNew,
    PostSignal,
    PostUnread,
    PostUseful,
    TopicEdit,
    TopicNew,
    TopicPostsListView,
    solve_alert,
)

app_name = "forum"

urlpatterns = [
    # Feeds
    path("flux/messages/rss/", feeds.LastPostsFeedRSS(), name="post-feed-rss"),
    path("flux/messages/atom/", feeds.LastPostsFeedATOM(), name="post-feed-atom"),
    path("flux/sujets/rss/", feeds.LastTopicsFeedRSS(), name="topic-feed-rss"),
    path("flux/sujets/atom/", feeds.LastTopicsFeedATOM(), name="topic-feed-atom"),
    # Developers warning: if you update something here, check and update help_text
    # on ForumCategory slug field
    # Moderation
    path("resolution_alerte/", solve_alert, name="solve-alert"),
    # Viewing a thread
    path("sujet/nouveau/", TopicNew.as_view(), name="topic-new"),
    path("sujet/modifier/", TopicEdit.as_view(), name="topic-edit"),
    path("sujet/github/<int:pk>/", ManageGitHubIssue.as_view(), name="manage-issue"),
    path("sujet/<int:topic_pk>/<slug:topic_slug>/", TopicPostsListView.as_view(), name="topic-posts-list"),
    path("sujets/membre/<int:user_pk>/", FindTopic.as_view(), name="topic-find"),
    path("sujets/suivis/", FindFollowedTopic.as_view(), name="followed-topic-find"),
    # The first is kept for URL backward-compatibility.
    path("sujets/tag/<int:tag_pk>/<slug:tag_slug>/", FindTopicByTag.as_view(), name="old-topic-tag-find"),
    path("sujets/tag/<slug:tag_slug>/", FindTopicByTag.as_view(), name="topic-tag-find"),
    # Message-related
    path("message/nouveau/", PostNew.as_view(), name="post-new"),
    path("message/modifier/", PostEdit.as_view(), name="post-edit"),
    path("message/utile/", PostUseful.as_view(), name="post-useful"),
    path("message/signaler/", PostSignal.as_view(), name="post-create-alert"),
    path("message/nonlu/", PostUnread.as_view(), name="post-unread"),
    path("messages/<int:user_pk>/", FindPost.as_view(), name="post-find"),
    # Last subjects
    path("derniers-sujets/", LastTopicsListView.as_view(), name="last-subjects"),
    # Categories and forums list
    path("", CategoriesForumsListView.as_view(), name="cats-forums-list"),
    # Forum details
    path("<slug:cat_slug>/<slug:forum_slug>/", ForumTopicsListView.as_view(), name="topics-list"),
    # Forums belonging to one category
    path("<slug:slug>/", ForumCategoryForumsDetailView.as_view(), name="cat-forums-list"),
]
