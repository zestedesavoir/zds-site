# coding: utf-8

from django.conf.urls import patterns, url

from zds.tutorialv2.views.views_contents import ListContents, DisplayContent, CreateContent, EditContent, \
    DeleteContent, CreateContainer, DisplayContainer, EditContainer, CreateExtract, EditExtract, \
    DeleteContainerOrExtract, ManageBetaContent, DisplayHistory, DisplayDiff, ActivateJSFiddleInContent, MoveChild, \
    DownloadContent, UpdateContentWithArchive, CreateContentFromArchive, ContentsWithHelps, AddAuthorToContent, \
    RemoveAuthorFromContent, WarnTypo, DisplayBetaContent, DisplayBetaContainer

from zds.tutorialv2.views.views_published import RedirectContentSEO, SendNoteFormView, UpvoteReaction, \
    DownvoteReaction, UpdateNoteView, GetReaction, HideReaction, SendNoteAlert, SolveNoteAlert

urlpatterns = patterns('',
                       url(r'^$', ListContents.as_view(), name='index'),

                       url(r'^aides/$', ContentsWithHelps.as_view(), name='helps'),

                       # view:
                       url(r'^(?P<pk>\d+)/(?P<slug>.+)/(?P<parent_container_slug>.+)/(?P<container_slug>.+)/$',
                           DisplayContainer.as_view(),
                           name='view-container'),
                       url(r'^(?P<pk>\d+)/(?P<slug>.+)/(?P<container_slug>.+)/$',
                           DisplayContainer.as_view(),
                           name='view-container'),

                       url(r'^(?P<pk>\d+)/(?P<slug>.+)/$', DisplayContent.as_view(), name='view'),

                       url(r'^telecharger/(?P<pk>\d+)/(?P<slug>.+)/$', DownloadContent.as_view(),
                           name='download-zip'),

                       # beta:
                       url(r'^beta/(?P<pk>\d+)/(?P<slug>.+)/(?P<parent_container_slug>.+)/(?P<container_slug>.+)/$',
                           DisplayBetaContainer.as_view(),
                           name='beta-view-container'),
                       url(r'^beta/(?P<pk>\d+)/(?P<slug>.+)/(?P<container_slug>.+)/$',
                           DisplayBetaContainer.as_view(),
                           name='beta-view-container'),

                       url(r'^beta/(?P<pk>\d+)/(?P<slug>.+)/$', DisplayBetaContent.as_view(), name='beta-view'),

                       # reactions:
                       url(r'^reactions/ajouter/$', SendNoteFormView.as_view(), name="add-reaction"),
                       url(r'^reactions/edit/$', UpdateNoteView.as_view(), name="update-reaction"),
                       url(r'^reactions/get-json/(?P<pk>\d+)/$',
                           GetReaction.as_view(), name="json-reaction"),
                       url(r'^reactions/upvote/$', UpvoteReaction.as_view(), name="up-vote"),
                       url(r'^reactions/downvote/$', DownvoteReaction.as_view(), name="down-vote"),
                       url(r'^reactions/hide/(?P<pk>\d+)/$', HideReaction.as_view(), name="hide-reaction"),
                       url(r'^reactions/alerter/(?P<pk>\d+)/$', SendNoteAlert.as_view(), name="alert-reaction"),
                       url(r'^reactions/resoudre/$', SolveNoteAlert.as_view(), name="resolve-reaction"),

                       # typo:
                       url(r'^reactions/typo/$', WarnTypo.as_view(), name="warn-typo"),

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
                       url(r'^deplacer/$', MoveChild.as_view(), name='move-element'),

                       url(r'^historique/(?P<pk>\d+)/(?P<slug>.+)/$', DisplayHistory.as_view(), name="history"),
                       url(r'^comparaison/(?P<pk>\d+)/(?P<slug>.+)/$', DisplayDiff.as_view(), name="diff"),
                       url(r'^ajouter-auteur/(?P<pk>\d+)/$', AddAuthorToContent.as_view(), name="add-author"),
                       url(r'^enlever-auteur/(?P<pk>\d+)/$', RemoveAuthorFromContent.as_view(), name="remove-author"),
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
                       url(r'^importer/archive/nouveau/$', CreateContentFromArchive.as_view(), name="import-new"),
                       url(r'^importer/(?P<pk>\d+)/(?P<slug>.+)/$', UpdateContentWithArchive.as_view(), name="import"),

                       url(r'^(?P<pk>\d+)/(?P<slug>.+)/(?P<p2>\d+)/'
                           r'(?P<parent_container_slug>.+)/(?P<p3>\d+)/(?P<container_slug>.+)/$',
                           RedirectContentSEO.as_view(), name="redirect_old_tuto"))
