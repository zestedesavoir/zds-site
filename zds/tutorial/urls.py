# coding: utf-8

from django.conf.urls import url

from zds.tutorial import views
from zds.tutorial import feeds

urlpatterns = [
    # Viewing
    url(r'^flux/rss/$', feeds.LastTutorialsFeedRSS(), name='tutorial-feed-rss'),
    url(r'^flux/atom/$', feeds.LastTutorialsFeedATOM(), name='tutorial-feed-atom'),

    # Current URLs
    url(r'^recherche/(?P<pk_user>\d+)/$', views.find_tuto),

    url(r'^off/(?P<tutorial_pk>\d+)/(?P<tutorial_slug>.+)/(?P<part_pk>\d+)/(?P<part_slug>.+)/(?P<chapter_pk>\d+)/(?P<ch'
        r'apter_slug>.+)/$', views.view_chapter, name="view-chapter-url"),

    url(r'^off/(?P<tutorial_pk>\d+)/(?P<tutorial_slug>.+)/(?P<part_pk>\d+)/(?P<part_slug>.+)/$',
        views.view_part, name="view-part-url"),

    url(r'^off/(?P<tutorial_pk>\d+)/(?P<tutorial_slug>.+)/$', views.view_tutorial),

    # Beta URLs
    url(r'^beta/(?P<tutorial_pk>\d+)/(?P<tutorial_slug>.+)/(?P<part_pk>\d+)/(?P<part_slug>.+)/(?P<chapter_pk>\d+)/(?P<c'
        r'hapter_slug>.+)/$', views.view_chapter_beta, name="view-chapter-url-beta"),

    url(r'^beta/(?P<tutorial_pk>\d+)/(?P<tutorial_slug>.+)/(?P<part_pk>\d+)/(?P<part_slug>.+)/$',
        views.view_part_beta, name="view-part-url-beta"),

    url(r'^beta/(?P<tutorial_pk>\d+)/(?P<tutorial_slug>.+)/$', views.view_tutorial_beta),

    # View online
    url(r'^(?P<tutorial_pk>\d+)/(?P<tutorial_slug>.+)/(?P<part_pk>\d+)/(?P<part_slug>.+)/(?P<chapter_pk>\d+)/(?P<chapte'
        r'r_slug>.+)/$', views.view_chapter_online, name="view-chapter-url-online"),

    url(r'^(?P<tutorial_pk>\d+)/(?P<tutorial_slug>.+)/(?P<part_pk>\d+)/(?P<part_slug>.+)/$',
        views.view_part_online, name="view-part-url-online"),

    url(r'^(?P<tutorial_pk>\d+)/(?P<tutorial_slug>.+)/$', views.view_tutorial_online),

    # Editing
    url(r'^editer/tutoriel/$', views.edit_tutorial),
    url(r'^modifier/tutoriel/$', views.modify_tutorial),
    url(r'^modifier/partie/$', views.modify_part),
    url(r'^editer/partie/$', views.edit_part),
    url(r'^modifier/chapitre/$', views.modify_chapter),
    url(r'^editer/chapitre/$', views.edit_chapter),
    url(r'^modifier/extrait/$', views.modify_extract),
    url(r'^editer/extrait/$', views.edit_extract),

    # Adding
    url(r'^nouveau/tutoriel/$', views.add_tutorial),
    url(r'^nouveau/partie/$', views.add_part),
    url(r'^nouveau/chapitre/$', views.add_chapter),
    url(r'^nouveau/extrait/$', views.add_extract),

    url(r'^$', views.index),
    url(r'^importer/$', views.import_tuto),
    url(r'^import_local/$', views.local_import),
    url(r'^telecharger/$', views.download),
    url(r'^telecharger/pdf/$', views.download_pdf),
    url(r'^telecharger/html/$', views.download_html),
    url(r'^telecharger/epub/$', views.download_epub),
    url(r'^telecharger/md/$', views.download_markdown),
    url(r'^historique/(?P<tutorial_pk>\d+)/(?P<tutorial_slug>.+)/$', views.history),
    url(r'^comparaison/(?P<tutorial_pk>\d+)/(?P<tutorial_slug>.+)/$', views.diff),

    # user actions
    url(r'^suppression/(?P<tutorial_pk>\d+)/$', views.delete_tutorial),
    url(r'^validation/tutoriel/$', views.ask_validation),

    # Validation
    url(r'^validation/$', views.list_validation),
    url(r'^validation/reserver/(?P<validation_pk>\d+)/$', views.reservation),
    url(r'^validation/reject/$', views.reject_tutorial),
    url(r'^validation/valid/$', views.valid_tutorial),
    url(r'^validation/invalid/(?P<tutorial_pk>\d+)/$', views.invalid_tutorial),
    url(r'^validation/historique/(?P<tutorial_pk>\d+)/$', views.history_validation),
    url(r'^activation_js/$', views.activ_js),
    # Reactions
    url(r'^message/editer/$', views.edit_note),
    url(r'^message/nouveau/$', views.answer),
    url(r'^message/like/$', views.like_note),
    url(r'^message/dislike/$', views.dislike_note),
    url(r'^message/typo/(?P<obj_type>.+)/(?P<obj_pk>\d+)/$', views.warn_typo),

    # Moderation
    url(r'^resolution_alerte/$', views.solve_alert),

    # Help
    url(r'^aides/$', views.help_tutorial),
]
