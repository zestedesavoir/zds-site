# coding: utf-8

from django.conf.urls import patterns, url

import views


urlpatterns = patterns('',
# Viewing

    # Current URLs
    url(r'^recherche/(?P<pk_user>.+)$', views.find_tuto),
    
    url(r'^off/(?P<tutorial_pk>\d+)/(?P<tutorial_slug>.+)/' +
        r'(?P<part_slug>.+)/' +
        r'(?P<chapter_slug>.+)/$', views.view_chapter, name="view-chapter-url"),

    url(r'^off/(?P<tutorial_pk>\d+)/(?P<tutorial_slug>.+)/' +
    r'(?P<part_slug>.+)/$', views.view_part, name="view-part-url"),

    url(r'^off/(?P<tutorial_pk>\d+)/(?P<tutorial_slug>.+)/$',
        views.view_tutorial),
    
    #View online
    url(r'^(?P<tutorial_pk>\d+)/(?P<tutorial_slug>.+)/' +
        r'(?P<part_slug>.+)/' +
        r'(?P<chapter_slug>.+)/$', views.view_chapter_online, name="view-chapter-url-online"),

    url(r'^(?P<tutorial_pk>\d+)/(?P<tutorial_slug>.+)/' +
    r'(?P<part_slug>.+)/$', views.view_part_online, name="view-part-url-online"),

    url(r'^(?P<tutorial_pk>\d+)/(?P<tutorial_slug>.+)/$',
        views.view_tutorial_online),
                       
# Editing
    url(r'^editer/tutoriel$', views.edit_tutorial),
    url(r'^modifier/tutoriel$', views.modify_tutorial),
    url(r'^modifier/partie$', views.modify_part),
    url(r'^editer/partie$', views.edit_part),
    url(r'^modifier/chapitre$', views.modify_chapter),
    url(r'^editer/chapitre$', views.edit_chapter),
    url(r'^modifier/extrait$', views.modify_extract),
    url(r'^editer/extrait$', views.edit_extract),

# Adding
    url(r'^nouveau/tutoriel$', views.add_tutorial),
    url(r'^nouveau/partie$', views.add_part),
    url(r'^nouveau/chapitre$', views.add_chapter),
    url(r'^nouveau/extrait$', views.add_extract),

    url(r'^$', views.index),
    url(r'^importer/$', views.import_tuto),
    url(r'^telecharger/$', views.download),
    url(r'^telecharger/pdf/$', views.download_pdf),
    url(r'^telecharger/epub/$', views.download_epub),
    url(r'^telecharger/md/$', views.download_markdown),
    url(r'^historique/(?P<tutorial_pk>\d+)/(?P<tutorial_slug>.+)/$', views.history),
    url(r'^comparaison/(?P<tutorial_pk>\d+)/(?P<tutorial_slug>.+)/$', views.diff),
    
# user actions
    url(r'^activation/beta/(?P<tutorial_pk>\d+)/(?P<version>.+)/$', views.activ_beta),
    url(r'^desactivation/beta/(?P<tutorial_pk>\d+)/(?P<version>.+)/$', views.desactiv_beta),
    url(r'^validation/tutoriel$', views.ask_validation),

#Validation
    url(r'^validation/$', views.list_validation),
    url(r'^validation/reserver/(?P<validation_pk>\d+)/$', views.reservation),
    
#Reactions
    url(r'^message/editer$', views.edit_note),
    url(r'^message/nouveau$', views.answer),
    url(r'^message/like$', views.like_note),
    url(r'^message/dislike$', views.dislike_note),
)
