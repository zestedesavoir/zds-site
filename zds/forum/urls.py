# coding: utf-8

from django.conf.urls import patterns, url

from . import feeds
from . import views


urlpatterns = patterns('',

                       url(r'^flux/messages/rss/$',
                           feeds.LastPostsFeedRSS(),
                           name='post-feed-rss'),
                       url(r'^flux/messages/atom/$',
                           feeds.LastPostsFeedATOM(),
                           name='post-feed-atom'),

                       url(r'^flux/sujets/rss/$',
                           feeds.LastTopicsFeedRSS(),
                           name='topic-feed-rss'),
                       url(r'^flux/sujets/atom/$',
                           feeds.LastTopicsFeedATOM(),
                           name='topic-feed-atom'),

                       # Viewing a thread
                       url(r'^sujet/nouveau/$', 'zds.forum.views.new'),
                       url(r'^sujet/editer/$', 'zds.forum.views.edit'),
                       url(r'^sujet/deplacer$', 'zds.forum.views.move_topic'),
                       url(r'^sujet/(?P<topic_pk>\d+)/(?P<topic_slug>.+)/$',
                           'zds.forum.views.topic'),
                       url(r'^sujets/(?P<user_pk>.+)/$', 'zds.forum.views.find_topic'),

                       # Message-related
                       url(r'^message/editer/$', 'zds.forum.views.edit_post'),
                       url(r'^message/nouveau/$', 'zds.forum.views.answer'),
                       url(r'^message/utile/$', 'zds.forum.views.useful_post'),
                       url(r'^message/like/$', 'zds.forum.views.like_post'),
                       url(r'^message/dislike/$', 'zds.forum.views.dislike_post'),
                       url(r'^messages/(?P<user_pk>.+)/$', 'zds.forum.views.find_post'),

                       # Forum details
                       url(r'^(?P<cat_slug>.+)/(?P<forum_slug>.+)/$',
                           'zds.forum.views.details'),

                       # Forums belonging to one category
                       url(r'^(?P<cat_slug>.+)/$', 'zds.forum.views.cat_details'),

                       # Home
                       url(r'^$', 'zds.forum.views.index'),

                       # Followed topics
                       url(r'^notifications/$', 'zds.forum.views.followed_topics'),

                       # Moderation
                       url(r'^resolution_alerte/$', 'zds.forum.views.solve_alert'),
                       )
