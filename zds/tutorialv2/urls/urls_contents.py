from django.urls import path, re_path
from django.views.generic.base import RedirectView

from zds.tutorialv2.views.contents import (DisplayContent, CreateContent, EditContent,
                                           DeleteContent, CreateContainer, DisplayContainer, EditContainer,
                                           CreateExtract, EditExtract,
                                           DeleteContainerOrExtract, ManageBetaContent, DisplayHistory, DisplayDiff,
                                           ActivateJSFiddleInContent, MoveChild,
                                           DownloadContent, UpdateContentWithArchive, CreateContentFromArchive,
                                           ContentsWithHelps, AddAuthorToContent,
                                           RemoveAuthorFromContent, WarnTypo, DisplayBetaContent, DisplayBetaContainer,
                                           ContentOfAuthor, RedirectOldContentOfAuthor)

from zds.tutorialv2.views.published import (SendNoteFormView, UpdateNoteView,
                                            HideReaction, ShowReaction, SendNoteAlert, SolveNoteAlert, TagsListView,
                                            FollowContentReaction, FollowNewContent, SendContentAlert,
                                            SolveContentAlert,
                                            RequestFeaturedContent, ContentStatisticsView)

urlpatterns = [
    # Flux
    re_path(r'^flux/rss/$', RedirectView.as_view(pattern_name='publication:feed-rss',
                                                 permanent=True), name='feed-rss'),
    re_path(r'^flux/atom/$', RedirectView.as_view(pattern_name='publication:feed-atom',
                                                  permanent=True), name='feed-atom'),

    path('voir/<str:username>/',
         ContentOfAuthor.as_view(
             type='ALL', context_object_name='contents'),
         name='find-all'),

    path('tutoriels/<int:pk>/', RedirectOldContentOfAuthor.as_view(type='TUTORIAL')),
    path('articles/<int:pk>/', RedirectOldContentOfAuthor.as_view(type='ARTICLE')),
    path('tribunes/<int:pk>/', RedirectOldContentOfAuthor.as_view(type='OPINION')),

    re_path(r'^aides/$', ContentsWithHelps.as_view(), name='helps'),
    re_path(r'^(?P<pk>\d+)/(?P<slug>[a-zA-Z0-9_-]+)/(?P<parent_container_slug>.+)/(?P<container_slug>.+)/$',
            DisplayContainer.as_view(public_is_prioritary=False),
            name='view-container'),
    re_path(r'^(?P<pk>\d+)/(?P<slug>[a-zA-Z0-9_-]+)/(?P<container_slug>.+)/$',
            DisplayContainer.as_view(public_is_prioritary=False),
            name='view-container'),

    re_path(r'^(?P<pk>\d+)/(?P<slug>[a-zA-Z0-9_-]+)/$', DisplayContent.as_view(public_is_prioritary=False),
            name='view'),

    re_path(r'^telecharger/(?P<pk>\d+)/(?P<slug>.+)/$', DownloadContent.as_view(),
            name='download-zip'),

    # beta:
    re_path(r'^beta/(?P<pk>\d+)/(?P<slug>.+)/(?P<parent_container_slug>.+)/(?P<container_slug>.+)/$',
            DisplayBetaContainer.as_view(public_is_prioritary=False),
            name='beta-view-container'),
    re_path(r'^beta/(?P<pk>\d+)/(?P<slug>.+)/(?P<container_slug>.+)/$',
            DisplayBetaContainer.as_view(public_is_prioritary=False),
            name='beta-view-container'),

    re_path(r'^beta/(?P<pk>\d+)/(?P<slug>.+)/$',
            DisplayBetaContent.as_view(), name='beta-view'),

    # reactions:
    re_path(r'^reactions/ajouter/$',
            SendNoteFormView.as_view(redirection_is_needed=False), name='add-reaction'),
    re_path(r'^reactions/editer/$',
            UpdateNoteView.as_view(redirection_is_needed=False), name='update-reaction'),
    re_path(r'^reactions/cacher/(?P<pk>\d+)/$',
            HideReaction.as_view(), name='hide-reaction'),
    re_path(r'^reactions/afficher/(?P<pk>\d+)/$',
            ShowReaction.as_view(), name='show-reaction'),
    re_path(r'^reactions/alerter/(?P<pk>\d+)/$',
            SendNoteAlert.as_view(), name='alert-reaction'),
    re_path(r'^reactions/resoudre/$',
            SolveNoteAlert.as_view(), name='resolve-reaction'),

    # follow:
    re_path(r'^suivre/(?P<pk>\d+)/reactions/$',
            FollowContentReaction.as_view(), name='follow-reactions'),
    re_path(r'^suivre/membres/(?P<pk>\d+)/$',
            FollowNewContent.as_view(), name='follow'),

    # request
    re_path(r'^requete/(?P<pk>\d+)/$', RequestFeaturedContent.as_view(), name='request-featured'),

    # content alerts:
    re_path(r'^alerter/(?P<pk>\d+)/$',
            SendContentAlert.as_view(), name='alert-content'),
    re_path(r'^resoudre/(?P<pk>\d+)/$',
            SolveContentAlert.as_view(), name='resolve-content'),

    # typo:
    re_path(r'^reactions/typo/$', WarnTypo.as_view(), name='warn-typo'),

    # create:
    re_path(r'^nouveau-tutoriel/$',
            CreateContent.as_view(created_content_type='TUTORIAL'), name='create-tutorial'),
    re_path(r'^nouvel-article/$',
            CreateContent.as_view(created_content_type='ARTICLE'), name='create-article'),
    re_path(r'^nouveau-billet/$',
            CreateContent.as_view(created_content_type='OPINION'), name='create-opinion'),
    re_path(r'^nouveau-conteneur/(?P<pk>\d+)/(?P<slug>.+)/(?P<container_slug>.+)/$',
            CreateContainer.as_view(),
            name='create-container'),
    re_path(r'^nouveau-conteneur/(?P<pk>\d+)/(?P<slug>.+)/$',
            CreateContainer.as_view(),
            name='create-container'),

    re_path(r'^nouvelle-section/(?P<pk>\d+)/(?P<slug>.+)/(?P<parent_container_slug>.+)/(?P<container_slug>.+)/$',
            CreateExtract.as_view(),
            name='create-extract'),
    re_path(r'^nouvelle-section/(?P<pk>\d+)/(?P<slug>.+)/(?P<container_slug>.+)/$',
            CreateExtract.as_view(),
            name='create-extract'),
    re_path(r'^nouvelle-section/(?P<pk>\d+)/(?P<slug>.+)/$',
            CreateExtract.as_view(),
            name='create-extract'),

    # edit:
    re_path(r'^editer-conteneur/(?P<pk>\d+)/(?P<slug>.+)/(?P<parent_container_slug>.+)/'
            r'(?P<container_slug>.+)/$',
            EditContainer.as_view(),
            name='edit-container'),
    re_path(r'^editer-conteneur/(?P<pk>\d+)/(?P<slug>.+)/(?P<container_slug>.+)/$',
            EditContainer.as_view(),
            name='edit-container'),

    re_path(r'^editer-section/(?P<pk>\d+)/(?P<slug>.+)/(?P<parent_container_slug>.+)/'
            r'(?P<container_slug>.+)/(?P<extract_slug>.+)/$',
            EditExtract.as_view(),
            name='edit-extract'),
    re_path(r'^editer-section/(?P<pk>\d+)/(?P<slug>.+)/(?P<container_slug>.+)/(?P<extract_slug>.+)/$',
            EditExtract.as_view(),
            name='edit-extract'),
    re_path(r'^editer-section/(?P<pk>\d+)/(?P<slug>.+)/(?P<extract_slug>.+)/$',
            EditExtract.as_view(),
            name='edit-extract'),

    re_path(r'^editer/(?P<pk>\d+)/(?P<slug>.+)/$',
            EditContent.as_view(), name='edit'),
    re_path(r'^deplacer/$', MoveChild.as_view(), name='move-element'),

    re_path(r'^historique/(?P<pk>\d+)/(?P<slug>.+)/$',
            DisplayHistory.as_view(), name='history'),
    re_path(r'^comparaison/(?P<pk>\d+)/(?P<slug>.+)/$',
            DisplayDiff.as_view(), name='diff'),
    re_path(r'^ajouter-auteur/(?P<pk>\d+)/$',
            AddAuthorToContent.as_view(), name='add-author'),
    re_path(r'^enlever-auteur/(?P<pk>\d+)/$',
            RemoveAuthorFromContent.as_view(), name='remove-author'),
    # beta:
    re_path(r'^activer-beta/(?P<pk>\d+)/(?P<slug>.+)/$', ManageBetaContent.as_view(action='set'),
            name='set-beta'),
    re_path(r'^desactiver-beta/(?P<pk>\d+)/(?P<slug>.+)/$', ManageBetaContent.as_view(action='inactive'),
            name='inactive-beta'),
    re_path(r'^stats/(?P<pk>\d+)/(?P<slug>.+)/$', ContentStatisticsView.as_view(),
            name='stats-content'),

    # jsfiddle support:
    re_path(r'activer-js/', ActivateJSFiddleInContent.as_view(),
            name='activate-jsfiddle'),

    # delete:
    re_path(r'^supprimer/(?P<pk>\d+)/(?P<slug>.+)/(?P<parent_container_slug>.+)/(?P<container_slug>.+)/'
            r'(?P<object_slug>.+)/$',
            DeleteContainerOrExtract.as_view(),
            name='delete'),
    re_path(r'^supprimer/(?P<pk>\d+)/(?P<slug>.+)/(?P<container_slug>.+)/(?P<object_slug>.+)/$',
            DeleteContainerOrExtract.as_view(),
            name='delete'),
    re_path(r'^supprimer/(?P<pk>\d+)/(?P<slug>.+)/(?P<object_slug>.+)/$',
            DeleteContainerOrExtract.as_view(),
            name='delete'),

    re_path(r'^supprimer/(?P<pk>\d+)/(?P<slug>.+)/$',
            DeleteContent.as_view(), name='delete'),

    # markdown import
    re_path(r'^importer/archive/nouveau/$',
            CreateContentFromArchive.as_view(), name='import-new'),
    re_path(r'^importer/(?P<pk>\d+)/(?P<slug>.+)/$',
            UpdateContentWithArchive.as_view(), name='import'),

    # tags
    re_path(r'^tags/$', TagsListView.as_view(), name='tags'),

    re_path(r'^$', RedirectView.as_view(
        pattern_name='publication:list', permanent=True), name='list'),
]
