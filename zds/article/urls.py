# coding: utf-8

from django.conf.urls import  url

import feeds
import views


urlpatterns = [
    # feed
    url(r'^flux/rss/$', feeds.LastArticlesFeedRSS(), name='article-feed-rss'),
    url(r'^flux/atom/$', feeds.LastArticlesFeedATOM(), name='article-feed-atom'),

    # Moderation
    url(r'^resolution_alerte/$', 'zds.article.views.solve_alert'),

    url(r'^voir/(?P<article_pk>\d+)/(?P<article_slug>.+)/$', 'zds.article.views.deprecated_view_redirect'),
    url(r'^off/(?P<article_pk>\d+)/(?P<article_slug>.+)/$', 'zds.article.views.view'),
    url(r'^(?P<article_pk>\d+)/(?P<article_slug>.+)/$', 'zds.article.views.view_online'),
    url(r'^nouveau/$', 'zds.article.views.new'),
    url(r'^editer/$', 'zds.article.views.edit'),
    url(r'^modifier/$', 'zds.article.views.modify'),
    url(r'^recherche/(?P<pk_user>\d+)/$', 'zds.article.views.find_article'),

    url(r'^$', 'zds.article.views.index'),
    url(r'^telecharger/$', 'zds.article.views.download'),
    url(r'^historique/(?P<article_pk>\d+)/(?P<article_slug>.+)/$',  'zds.article.views.history'),

    # Validation
    url(r'^validation/$', 'zds.article.views.list_validation'),
    url(r'^validation/reserver/(?P<validation_pk>\d+)/$',  'zds.article.views.reservation'),
    url(r'^validation/historique/(?P<article_pk>\d+)/$',  'zds.article.views.history_validation'),
    url(r'^activation_js/$', 'zds.article.views.activ_js'),

    # Reactions
    url(r'^message/editer/$', 'zds.article.views.edit_reaction'),
    url(r'^message/nouveau/$', 'zds.article.views.answer'),
    url(r'^message/like/$', 'zds.article.views.like_reaction'),
    url(r'^message/dislike/$', 'zds.article.views.dislike_reaction'),
    url(r'^message/typo/article/(?P<article_pk>\d+)/$', 'zds.article.views.warn_typo'),
]
