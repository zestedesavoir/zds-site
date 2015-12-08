# coding: utf-8

from django.conf.urls import url

from zds.tutorial import views
from zds.tutorial import feeds

urlpatterns = [
    # Viewing
    url(r'^flux/rss/$', feeds.LastTutorialsFeedRSS(), name='tutorial-feed-rss'),
    url(r'^flux/atom/$', feeds.LastTutorialsFeedATOM(), name='tutorial-feed-atom'),

    # Current URLs
    url(r'^recherche/(?P<pk_user>\d+)/$', views.find_tuto, name='tutorial-find-tuto'),

    url(r'^off/(?P<tutorial_pk>\d+)/(?P<tutorial_slug>.+)/(?P<part_pk>\d+)/(?P<part_slug>.+)/(?P<chapter_pk>\d+)/(?P<ch'
        r'apter_slug>.+)/$', views.view_chapter, name="view-chapter-url"),

    url(r'^off/(?P<tutorial_pk>\d+)/(?P<tutorial_slug>.+)/(?P<part_pk>\d+)/(?P<part_slug>.+)/$',
        views.view_part, name="view-part-url"),

    url(r'^off/(?P<tutorial_pk>\d+)/(?P<tutorial_slug>.+)/$', views.view_tutorial, name='tutorial-view'),

    # Beta URLs
    url(r'^beta/(?P<tutorial_pk>\d+)/(?P<tutorial_slug>.+)/(?P<part_pk>\d+)/(?P<part_slug>.+)/(?P<chapter_pk>\d+)/(?P<c'
        r'hapter_slug>.+)/$', views.view_chapter_beta, name="view-chapter-url-beta"),

    url(r'^beta/(?P<tutorial_pk>\d+)/(?P<tutorial_slug>.+)/(?P<part_pk>\d+)/(?P<part_slug>.+)/$',
        views.view_part_beta, name="view-part-url-beta"),

    url(r'^beta/(?P<tutorial_pk>\d+)/(?P<tutorial_slug>.+)/$', views.view_tutorial_beta, name='tutorial-view-beta'),

    # View online
    url(r'^(?P<tutorial_pk>\d+)/(?P<tutorial_slug>.+)/(?P<part_pk>\d+)/(?P<part_slug>.+)/(?P<chapter_pk>\d+)/(?P<chapte'
        r'r_slug>.+)/$', views.view_chapter_online, name="view-chapter-url-online"),

    url(r'^(?P<tutorial_pk>\d+)/(?P<tutorial_slug>.+)/(?P<part_pk>\d+)/(?P<part_slug>.+)/$',
        views.view_part_online, name="view-part-url-online"),

    url(r'^(?P<tutorial_pk>\d+)/(?P<tutorial_slug>.+)/$', views.view_tutorial_online, name='tutorial-view-online'),

    # Editing
    url(r'^editer/tutoriel/$', views.edit_tutorial, name='tutorial-edit-tutorial'),
    url(r'^modifier/tutoriel/$', views.modify_tutorial, name='tutorial-modify-tutorial'),
    url(r'^modifier/partie/$', views.modify_part, name='tutorial-modify-part'),
    url(r'^editer/partie/$', views.edit_part, name='tutorial-edit-part'),
    url(r'^modifier/chapitre/$', views.modify_chapter, name='tutorial-modify-chapter'),
    url(r'^editer/chapitre/$', views.edit_chapter, name='tutorial-edit-chapter'),
    url(r'^modifier/extrait/$', views.modify_extract, name='tutorial-modify-extract'),
    url(r'^editer/extrait/$', views.edit_extract, name='tutorial-edit-extract'),

    # Adding
    url(r'^nouveau/tutoriel/$', views.add_tutorial, name='tutorial-add-tutorial'),
    url(r'^nouveau/partie/$', views.add_part, name='tutorial-part'),
    url(r'^nouveau/chapitre/$', views.add_chapter, name='tutorial-chapter'),
    url(r'^nouveau/extrait/$', views.add_extract, name='tutorial-add-extract'),

    url(r'^$', views.index, name='tutorial-index'),
    url(r'^importer/$', views.import_tuto, name='tutorial-import'),
    url(r'^import_local/$', views.local_import, name='tutorial-local-import'),
    url(r'^telecharger/$', views.download, name='tutorial-download'),
    url(r'^telecharger/pdf/$', views.download_pdf, name='tutorial-download-pdf'),
    url(r'^telecharger/html/$', views.download_html, name='tutorial-download-html'),
    url(r'^telecharger/epub/$', views.download_epub, name='tutorial-download-epub'),
    url(r'^telecharger/md/$', views.download_markdown, name='tutorial-download-markdown'),
    url(r'^historique/(?P<tutorial_pk>\d+)/(?P<tutorial_slug>.+)/$', views.history, name='tutorial-history'),
    url(r'^comparaison/(?P<tutorial_pk>\d+)/(?P<tutorial_slug>.+)/$', views.diff, name='tutorial-diff'),

    # user actions
    url(r'^suppression/(?P<tutorial_pk>\d+)/$', views.delete_tutorial, name='tutorial-delete'),
    url(r'^validation/tutoriel/$', views.ask_validation, name='tutorial-ask-validation'),

    # Validation
    url(r'^validation/$', views.list_validation, name='tutorial-list-validation'),
    url(r'^validation/reserver/(?P<validation_pk>\d+)/$', views.reservation, name='tutorial-reservation'),
    url(r'^validation/reject/$', views.reject_tutorial, name='tutorial-reject'),
    url(r'^validation/valid/$', views.valid_tutorial, name='tutorial-valid-tutorial'),
    url(r'^validation/invalid/(?P<tutorial_pk>\d+)/$', views.invalid_tutorial, name='tutorial-invalid-tutorial'),
    url(r'^validation/historique/(?P<tutorial_pk>\d+)/$', views.history_validation, name='tutorial-history-validation'),
    url(r'^activation_js/$', views.activ_js, name='tutorial-activ-js'),
    # Reactions
    url(r'^message/editer/$', views.edit_note, name='tutorial-edit-note'),
    url(r'^message/nouveau/$', views.answer, name='tutorial-answer'),
    url(r'^message/like/$', views.like_note, name='tutorial-like-note'),
    url(r'^message/dislike/$', views.dislike_note, name='tutorial-dislike-note'),
    url(r'^message/typo/(?P<obj_type>.+)/(?P<obj_pk>\d+)/$', views.warn_typo, name='tutorial-warn-typo'),

    # Moderation
    url(r'^resolution_alerte/$', views.solve_alert, name='tutorial-solve-alert'),

    # Help
    url(r'^aides/$', views.help_tutorial, name='tutorial-help-tutorial'),
]
