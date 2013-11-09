# coding: utf-8

from django.conf.urls import patterns, url

import views
import feeds

urlpatterns = patterns('',

    # Feeds
    url(r'^flux/rss/$', views.deprecated_feed_messages_rss),
    url(r'^flux/atom/$', views.deprecated_feed_messages_atom),

    url(r'^flux/messages/rss/$', feeds.LastPostsFeedRSS(), name='post-feed-rss'),
    url(r'^flux/messages/atom/$', feeds.LastPostsFeedATOM(), name='post-feed-atom'),

    url(r'^flux/sujets/rss/$', feeds.LastTopicsFeedRSS(), name='topic-feed-rss'),
    url(r'^flux/sujets/atom/$', feeds.LastTopicsFeedATOM(), name='topic-feed-atom'),

    # Viewing a thread
    url(r'^sujet/nouveau$', views.new),
    url(r'^sujet/editer$', views.edit),
    url(r'^sujet/(?P<topic_pk>\d+)/(?P<topic_slug>.+)$', views.topic),
    url(r'^sujets/(?P<name>.+)', views.find_topic),

    # Message-related
    url(r'^message/editer$', views.edit_post),
    url(r'^message/nouveau$', views.answer),
    url(r'^message/utile$', views.useful_post),
    url(r'^message/like$', views.like_post),
    url(r'^message/dislike$', views.dislike_post),
    url(r'^messages/(?P<name>.+)$', views.find_post),

    # Forum details
    url(r'^(?P<cat_slug>.+)/(?P<forum_slug>.+)/$',
        views.details),

    # Forums belonging to one category
    url(r'^(?P<cat_slug>.+)/$', views.cat_details),

    # Home
    url(r'^$', views.index),
)
