# coding: utf-8

from django.conf.urls import patterns, url

from zds.tutorialv2.views import ListContent, DisplayContent, CreateContent, EditContent, DeleteContent,\
    CreateContainer, DisplayContainer, EditContainer, CreateExtract, EditExtract, DeleteContainerOrExtract, \
    ManageBetaContent, DisplayHistory, DisplayDiff, ValidationListView, ActivateJSFiddleInContent, \
    AskValidationForContent, ReserveValidation, HistoryOfValidationDisplay
from zds.tutorialv2.importation import ImportMarkdownView

urlpatterns = patterns('',
                       url(r'^$', ListContent.as_view(), name='index'),

                       # view:
                       url(r'^(?P<pk>\d+)/(?P<slug>.+)/(?P<parent_container_slug>.+)/(?P<container_slug>.+)/$',
                           DisplayContainer.as_view(),
                           name='view-container'),
                       url(r'^(?P<pk>\d+)/(?P<slug>.+)/(?P<container_slug>.+)/$',
                           DisplayContainer.as_view(),
                           name='view-container'),

                       url(r'^(?P<pk>\d+)/(?P<slug>.+)/$', DisplayContent.as_view(), name='view'),

                       # create:
                       url(r'^nouveau/$', CreateContent.as_view(), name='create'),

                       url(r'^nouveau-conteneur/(?P<pk>\d+)/(?P<slug>.+)/(?P<container_slug>.+)/$',
                           CreateContainer.as_view(),
                           name='create-container'),
                       url(r'^nouveau-conteneur/(?P<pk>\d+)/(?P<slug>.+)/$',
                           CreateContainer.as_view(),
                           name='create-container'),


                       url(r'^nouvel-extrait/(?P<pk>\d+)/(?P<slug>.+)/(?P<parent_container_slug>.+)/'
                           r'(?P<container_slug>.+)/$',
                           CreateExtract.as_view(),
                           name='create-extract'),
                       url(r'^nouvel-extrait/(?P<pk>\d+)/(?P<slug>.+)/(?P<container_slug>.+)/$',
                           CreateExtract.as_view(),
                           name='create-extract'),
                       url(r'^nouvel-extrait/(?P<pk>\d+)/(?P<slug>.+)/$',
                           CreateExtract.as_view(),
                           name='create-extract'),

                       # edit:
                       url(r'^editer-conteneur/(?P<pk>\d+)/(?P<slug>.+)/(?P<parent_container_slug>.+)/'
                           r'(?P<container_slug>.+)/$',
                           EditContainer.as_view(),
                           name='edit-container'),
                       url(r'^editer-conteneur/(?P<pk>\d+)/(?P<slug>.+)/(?P<container_slug>.+)/$',
                           EditContainer.as_view(),
                           name='edit-container'),

                       url(r'^editer-extrait/(?P<pk>\d+)/(?P<slug>.+)/(?P<parent_container_slug>.+)/'
                           r'(?P<container_slug>.+)/(?P<extract_slug>.+)/$',
                           EditExtract.as_view(),
                           name='edit-extract'),
                       url(r'^editer-extrait/(?P<pk>\d+)/(?P<slug>.+)/(?P<container_slug>.+)/(?P<extract_slug>.+)/$',
                           EditExtract.as_view(),
                           name='edit-extract'),
                       url(r'^editer-extrait/(?P<pk>\d+)/(?P<slug>.+)/(?P<extract_slug>.+)/$',
                           EditExtract.as_view(),
                           name='edit-extract'),

                       url(r'^editer/(?P<pk>\d+)/(?P<slug>.+)/$', EditContent.as_view(), name='edit'),

                       url(r'^historique/(?P<pk>\d+)/(?P<slug>.+)/$', DisplayHistory.as_view(), name="history"),
                       url(r'^comparaison/(?P<pk>\d+)/(?P<slug>.+)/$', DisplayDiff.as_view(), name="diff"),

                       # beta:
                       url(r'^activer-beta/(?P<pk>\d+)/(?P<slug>.+)/$', ManageBetaContent.as_view(action='set'),
                           name="set-beta"),
                       url(r'^desactiver-beta/(?P<pk>\d+)/(?P<slug>.+)/$', ManageBetaContent.as_view(action='inactive'),
                           name="inactive-beta"),

                       # jsfiddle support:
                       url(r'activer-js/', ActivateJSFiddleInContent.as_view(), name="activate-jsfiddle"),

                       # delete:
                       url(r'^supprimer/(?P<pk>\d+)/(?P<slug>.+)/(?P<parent_container_slug>.+)/(?P<container_slug>.+)/'
                           r'(?P<object_slug>.+)/$',
                           DeleteContainerOrExtract.as_view(),
                           name='delete'),
                       url(r'^supprimer/(?P<pk>\d+)/(?P<slug>.+)/(?P<container_slug>.+)/(?P<object_slug>.+)/$',
                           DeleteContainerOrExtract.as_view(),
                           name='delete'),
                       url(r'^supprimer/(?P<pk>\d+)/(?P<slug>.+)/(?P<object_slug>.+)/$',
                           DeleteContainerOrExtract.as_view(),
                           name='delete'),

                       url(r'^supprimer/(?P<pk>\d+)/(?P<slug>.+)/$', DeleteContent.as_view(), name='delete'),

                       # markdown import
                       url(r'^importer/archive/nouveau/$', ImportMarkdownView.as_view(), name="import_new_archive"),
                       url(r'^importer/archive/(?P<pk>\d+)/$', ImportMarkdownView.as_view(),
                           name="update_with_archive"),

                       # validation
                       url(r'^valider/liste/$', ValidationListView.as_view(), name="list_validation"),
                       url(r'^valider/proposer/$', AskValidationForContent.as_view(), name="ask_validation"),
                       url(r'^valider/reserver/(?P<pk>\d+)/$', ReserveValidation.as_view(), name="reserve_validation"),
                       url(r'^validation/historique/(?P<pk>\d+)/$', HistoryOfValidationDisplay.as_view(),
                           name="validation_history")
                       )
