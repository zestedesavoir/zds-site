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

    url(r'^voir/(?P<article_pk>\d+)/(?P<article_slug>.+)/$', views.deprecated_view_redirect,
        name='article-depreciated_view_redirect'),
    url(r'^off/(?P<article_pk>\d+)/(?P<article_slug>.+)/$', views.view, name='article-view'),
    url(r'^(?P<article_pk>\d+)/(?P<article_slug>.+)/$', views.view_online, name='article-view-online'),
    url(r'^nouveau/$', views.new, name='article-new'),
    url(r'^editer/$', views.edit, name='article-edit'),
    url(r'^modifier/$', views.modify, name='article-modify'),
    url(r'^recherche/(?P<pk_user>\d+)/$', views.find_article, name='article-find-article'),

    url(r'^$', views.index, name='article-index'),
    url(r'^telecharger/$', views.download, name='article-download'),
    url(r'^historique/(?P<article_pk>\d+)/(?P<article_slug>.+)/$', views.history, name='article-history'),

    # Validation
    url(r'^validation/$', views.list_validation, name='article-list-validation'),
    url(r'^validation/reserver/(?P<validation_pk>\d+)/$', views.reservation, name='article-reservation'),
    url(r'^validation/historique/(?P<article_pk>\d+)/$', views.history_validation, name='article-history-validation'),
    url(r'^activation_js/$', views.activ_js, name='article-activ-js'),

    # Reactions
    url(r'^message/editer/$', views.edit_reaction, name='article-edit-reaction'),
    url(r'^message/nouveau/$', views.answer, name='article-answer'),
    url(r'^message/like/$', views.like_reaction, name='article-like-reaction'),
    url(r'^message/dislike/$', views.dislike_reaction, name='article-dislike-reaction'),
    url(r'^message/typo/article/(?P<article_pk>\d+)/$', views.warn_typo, name='article-warn-typo'),
]
