# coding: utf-8

from django.conf.urls import patterns, url

from . import views


urlpatterns = patterns('',
                       # Viewing

                       # Current URLs
                       url(r'^recherche/(?P<pk_user>.+)/$', 'zds.tutorial.views.find_tuto'),

                       url(r'^off/(?P<tutorial_pk>\d+)/(?P<tutorial_slug>.+)/' +
                           r'(?P<part_slug>.+)/' +
                           r'(?P<chapter_slug>.+)/$', 'zds.tutorial.views.view_chapter', name="view-chapter-url"),

                       url(r'^off/(?P<tutorial_pk>\d+)/(?P<tutorial_slug>.+)/' +
                           r'(?P<part_slug>.+)/$', 'zds.tutorial.views.view_part', name="view-part-url"),

                       url(r'^off/(?P<tutorial_pk>\d+)/(?P<tutorial_slug>.+)/$',
                           'zds.tutorial.views.view_tutorial'),

                       # View online
                       url(r'^(?P<tutorial_pk>\d+)/(?P<tutorial_slug>.+)/' +
                           r'(?P<part_slug>.+)/' +
                           r'(?P<chapter_slug>.+)/$', 'zds.tutorial.views.view_chapter_online', name="view-chapter-url-online"),

                       url(r'^(?P<tutorial_pk>\d+)/(?P<tutorial_slug>.+)/' +
                           r'(?P<part_slug>.+)/$', 'zds.tutorial.views.view_part_online', name="view-part-url-online"),

                       url(r'^(?P<tutorial_pk>\d+)/(?P<tutorial_slug>.+)/$',
                           'zds.tutorial.views.view_tutorial_online'),

                       # Editing
                       url(r'^editer/tutoriel/$', 'zds.tutorial.views.edit_tutorial'),
                       url(r'^modifier/tutoriel/$', 'zds.tutorial.views.modify_tutorial'),
                       url(r'^modifier/partie/$', 'zds.tutorial.views.modify_part'),
                       url(r'^editer/partie/$', 'zds.tutorial.views.edit_part'),
                       url(r'^modifier/chapitre/$', 'zds.tutorial.views.modify_chapter'),
                       url(r'^editer/chapitre/$', 'zds.tutorial.views.edit_chapter'),
                       url(r'^modifier/extrait/$', 'zds.tutorial.views.modify_extract'),
                       url(r'^editer/extrait/$', 'zds.tutorial.views.edit_extract'),

                       # Adding
                       url(r'^nouveau/tutoriel/$', 'zds.tutorial.views.add_tutorial'),
                       url(r'^nouveau/partie/$', 'zds.tutorial.views.add_part'),
                       url(r'^nouveau/chapitre/$', 'zds.tutorial.views.add_chapter'),
                       url(r'^nouveau/extrait/$', 'zds.tutorial.views.add_extract'),

                       url(r'^$', 'zds.tutorial.views.index'),
                       url(r'^importer/$', 'zds.tutorial.views.import_tuto'),
                       url(r'^import_local/$', 'zds.tutorial.views.local_import'),
                       url(r'^telecharger/$', 'zds.tutorial.views.download'),
                       url(r'^telecharger/pdf/$', 'zds.tutorial.views.download_pdf'),
                       url(r'^telecharger/html/$', 'zds.tutorial.views.download_html'),
                       url(r'^telecharger/epub/$', 'zds.tutorial.views.download_epub'),
                       url(r'^telecharger/md/$', 'zds.tutorial.views.download_markdown'),
                       url(r'^historique/(?P<tutorial_pk>\d+)/(?P<tutorial_slug>.+)/$',
                           'zds.tutorial.views.history'),
                       url(r'^comparaison/(?P<tutorial_pk>\d+)/(?P<tutorial_slug>.+)/$',
                           'zds.tutorial.views.diff'),

                       # user actions
                       url(r'^activation/beta/(?P<tutorial_pk>\d+)/(?P<version>.+)/$',
                           'zds.tutorial.views.activ_beta'),
                       url(
                           r'^desactivation/beta/(?P<tutorial_pk>\d+)/(?P<version>.+)/$',
                           'zds.tutorial.views.desactiv_beta'),
                       url(r'^suppression/(?P<tutorial_pk>\d+)/$',
                           'zds.tutorial.views.delete_tutorial'),
                       url(r'^validation/tutoriel/$', 'zds.tutorial.views.ask_validation'),

                       # Validation
                       url(r'^validation/$', 'zds.tutorial.views.list_validation'),
                       url(r'^validation/reserver/(?P<validation_pk>\d+)/$',
                           'zds.tutorial.views.reservation'),
                       url(r'^validation/reject/$', 'zds.tutorial.views.reject_tutorial'),
                       url(r'^validation/valid/$', 'zds.tutorial.views.valid_tutorial'),
                       url(r'^validation/invalid/(?P<tutorial_pk>\d+)/$',
                           'zds.tutorial.views.invalid_tutorial'),
                       url(r'^validation/historique/(?P<tutorial_pk>\d+)/$',
                           'zds.tutorial.views.history_validation'),

                       # Reactions
                       url(r'^message/editer/$', 'zds.tutorial.views.edit_note'),
                       url(r'^message/nouveau/$', 'zds.tutorial.views.answer'),
                       url(r'^message/like/$', 'zds.tutorial.views.like_note'),
                       url(r'^message/dislike/$', 'zds.tutorial.views.dislike_note'),
                       
                       # Moderation
                       url(r'^resolution_alerte/$', 'zds.tutorial.views.solve_alert'),
                       )
