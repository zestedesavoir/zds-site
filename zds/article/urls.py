# coding: utf-8

from django.conf.urls import url

from zds.article import feeds
from zds.article import views


urlpatterns = [
    # feed
    url(r'^flux/rss/$', feeds.LastArticlesFeedRSS(), name='article-feed-rss'),
    url(r'^flux/atom/$', feeds.LastArticlesFeedATOM(), name='article-feed-atom'),

    # Moderation
    url(r'^resolution_alerte/$', views.solve_alert),

    url(r'^voir/(?P<article_pk>\d+)/(?P<article_slug>.+)/$', views.deprecated_view_redirect),
    url(r'^off/(?P<article_pk>\d+)/(?P<article_slug>.+)/$', views.view),
    url(r'^(?P<article_pk>\d+)/(?P<article_slug>.+)/$', views.view_online),
    url(r'^nouveau/$', views.new),
    url(r'^editer/$', views.edit),
    url(r'^modifier/$', views.modify),
    url(r'^recherche/(?P<pk_user>\d+)/$', views.find_article),

    url(r'^$', views.index),
    url(r'^telecharger/$', views.download),
    url(r'^historique/(?P<article_pk>\d+)/(?P<article_slug>.+)/$', views.history),

    # Validation
    url(r'^validation/$', views.list_validation),
    url(r'^validation/reserver/(?P<validation_pk>\d+)/$', views.reservation),
    url(r'^validation/historique/(?P<article_pk>\d+)/$', views.history_validation),
    url(r'^activation_js/$', views.activ_js),

    # Reactions
    url(r'^message/editer/$', views.edit_reaction),
    url(r'^message/nouveau/$', views.answer),
    url(r'^message/like/$', views.like_reaction),
    url(r'^message/dislike/$', views.dislike_reaction),
    url(r'^message/typo/article/(?P<article_pk>\d+)/$', views.warn_typo),
]
