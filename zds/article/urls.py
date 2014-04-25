# coding: utf-8

from django.conf.urls import patterns, url

import feeds
import views


urlpatterns = patterns('',

    url(r'^flux/rss/$', feeds.LastArticlesFeedRSS(), name='article-feed-rss'),
    url(r'^flux/atom/$', feeds.LastArticlesFeedATOM(),
        name='article-feed-atom'),

    # TODO: Handle redirect

    url(r'^voir/(?P<article_pk>\d+)/(?P<article_slug>.+)$',
        'zds.views.deprecated_view_redirect'),
    url(r'^off/(?P<article_pk>\d+)/(?P<article_slug>.+)$', 'zds.views.view'),
    url(r'^(?P<article_pk>\d+)/(?P<article_slug>.+)$', 'zds.views.view_online'),
    url(r'^nouveau$', 'zds.views.new'),
    url(r'^editer$', 'zds.views.edit'),
    url(r'^modifier$', 'zds.views.modify'),
    url(r'^recherche/(?P<name>.+)$', 'zds.views.find_article'),


    url(r'^$', 'zds.views.index'),
    url(r'^telecharger/$', 'zds.views.download'),
    url(r'^historique/(?P<article_pk>\d+)/(?P<article_slug>.+)/$', 'zds.views.history'),
    
    #Validation
    url(r'^validation/$', 'zds.views.list_validation'),
    url(r'^validation/reserver/(?P<validation_pk>\d+)/$', 'zds.views.reservation'),
    url(r'^validation/historique/(?P<article_pk>\d+)/$', 'zds.views.history_validation'),
    
    #Reactions
    url(r'^message/editer$', 'zds.views.edit_reaction'),
    url(r'^message/nouveau$', 'zds.views.answer'),
    url(r'^message/like$', 'zds.views.like_reaction'),
    url(r'^message/dislike$', 'zds.views.dislike_reaction'),
)
