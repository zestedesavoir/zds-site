# coding: utf-8

from django.conf.urls import patterns, url

import views
import feeds

urlpatterns = patterns('',

    url(r'^flux/rss/$', feeds.LastArticlesFeedRSS(), name='article-feed-rss'),
    url(r'^flux/atom/$', feeds.LastArticlesFeedATOM(),
        name='article-feed-atom'),

    # TODO: Handle redirect

    url(r'^voir/(?P<article_pk>\d+)/(?P<article_slug>.+)$',
        views.deprecated_view_redirect),
    url(r'^off/(?P<article_pk>\d+)/(?P<article_slug>.+)$', views.view),
    url(r'^(?P<article_pk>\d+)/(?P<article_slug>.+)$', views.view_online),
    url(r'^nouveau$', views.new),
    url(r'^editer$', views.edit),
    url(r'^modifier$', views.modify),
    url(r'^recherche/(?P<name>.+)$', views.find_article),


    url(r'^$', views.index),
    url(r'^telecharger/$', views.download),
    url(r'^historique/(?P<article_pk>\d+)/(?P<article_slug>.+)/$', views.history),
    
    #Validation
    url(r'^validation/$', views.list_validation),
    url(r'^validation/reserver/(?P<validation_pk>\d+)/$', views.reservation),
    
    #Reactions
    url(r'^message/editer$', views.edit_reaction),
    url(r'^message/nouveau$', views.answer),
    url(r'^message/like$', views.like_reaction),
    url(r'^message/dislike$', views.dislike_reaction),
)
