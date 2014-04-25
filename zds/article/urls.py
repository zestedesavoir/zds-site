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
        'article.views.deprecated_view_redirect'),
    url(r'^off/(?P<article_pk>\d+)/(?P<article_slug>.+)$', 'article.views.view'),
    url(r'^(?P<article_pk>\d+)/(?P<article_slug>.+)$', 'article.views.view_online'),
    url(r'^nouveau$', 'article.views.new'),
    url(r'^editer$', 'article.views.edit'),
    url(r'^modifier$', 'article.views.modify'),
    url(r'^recherche/(?P<name>.+)$', 'article.views.find_article'),


    url(r'^$', 'article.views.index'),
    url(r'^telecharger/$', 'article.views.download'),
    url(r'^historique/(?P<article_pk>\d+)/(?P<article_slug>.+)/$', 'article.views.history'),
    
    #Validation
    url(r'^validation/$', 'article.views.list_validation'),
    url(r'^validation/reserver/(?P<validation_pk>\d+)/$', 'article.views.reservation'),
    url(r'^validation/historique/(?P<article_pk>\d+)/$', 'article.views.history_validation'),
    
    #Reactions
    url(r'^message/editer$', 'article.views.edit_reaction'),
    url(r'^message/nouveau$', 'article.views.answer'),
    url(r'^message/like$', 'article.views.like_reaction'),
    url(r'^message/dislike$', 'article.views.dislike_reaction'),
)
