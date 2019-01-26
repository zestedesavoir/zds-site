from django.conf.urls import url
from django.views.generic.base import RedirectView

from zds.tutorialv2.views.contents import DisplayContent, CreateContent, EditContent, \
    DeleteContent, CreateContainer, DisplayContainer, EditContainer, CreateExtract, EditExtract, \
    DeleteContainerOrExtract, ManageBetaContent, DisplayHistory, DisplayDiff, ActivateJSFiddleInContent, MoveChild, \
    DownloadContent, UpdateContentWithArchive, CreateContentFromArchive, ContentsWithHelps, AddAuthorToContent, \
    RemoveAuthorFromContent, WarnTypo, DisplayBetaContent, DisplayBetaContainer, ContentOfAuthor

from zds.tutorialv2.views.published import SendNoteFormView, UpdateNoteView, \
    HideReaction, ShowReaction, SendNoteAlert, SolveNoteAlert, TagsListView, \
    FollowContentReaction, FollowNewContent, SendContentAlert, SolveContentAlert, ContentStatisticsView

urlpatterns = [
    # Flux
    url(r'^flux/rss/$', RedirectView.as_view(pattern_name='publication:feed-rss', permanent=True), name='feed-rss'),
    url(r'^flux/atom/$', RedirectView.as_view(pattern_name='publication:feed-atom', permanent=True), name='feed-atom'),

    url(r'^tutoriels/(?P<pk>\d+)/$',
        ContentOfAuthor.as_view(type='TUTORIAL', context_object_name='tutorials'),
        name='find-tutorial'),
    url(r'^articles/(?P<pk>\d+)/$',
        ContentOfAuthor.as_view(type='ARTICLE', context_object_name='articles'),
        name='find-article'),
    url(r'^tribunes/(?P<pk>\d+)/$',
        ContentOfAuthor.as_view(type='OPINION', context_object_name='opinions', sort='creation'),
        name='find-opinion'),
    url(r'^aides/$', ContentsWithHelps.as_view(), name='helps'),
    url(r'^(?P<pk>\d+)/(?P<slug>.+)/(?P<parent_container_slug>.+)/(?P<container_slug>.+)/$',
        DisplayContainer.as_view(public_is_prioritary=False),
        name='view-container'),
    url(r'^(?P<pk>\d+)/(?P<slug>.+)/(?P<container_slug>.+)/$',
        DisplayContainer.as_view(public_is_prioritary=False),
        name='view-container'),

    url(r'^(?P<pk>\d+)/(?P<slug>.+)/$', DisplayContent.as_view(public_is_prioritary=False),
        name='view'),

    url(r'^telecharger/(?P<pk>\d+)/(?P<slug>.+)/$', DownloadContent.as_view(),
        name='download-zip'),

    # beta:
    url(r'^beta/(?P<pk>\d+)/(?P<slug>.+)/(?P<parent_container_slug>.+)/(?P<container_slug>.+)/$',
        DisplayBetaContainer.as_view(public_is_prioritary=False),
        name='beta-view-container'),
    url(r'^beta/(?P<pk>\d+)/(?P<slug>.+)/(?P<container_slug>.+)/$',
        DisplayBetaContainer.as_view(public_is_prioritary=False),
        name='beta-view-container'),

    url(r'^beta/(?P<pk>\d+)/(?P<slug>.+)/$', DisplayBetaContent.as_view(), name='beta-view'),

    # reactions:
    url(r'^reactions/ajouter/$', SendNoteFormView.as_view(redirection_is_needed=False), name='add-reaction'),
    url(r'^reactions/editer/$', UpdateNoteView.as_view(redirection_is_needed=False), name='update-reaction'),
    url(r'^reactions/cacher/(?P<pk>\d+)/$', HideReaction.as_view(), name='hide-reaction'),
    url(r'^reactions/afficher/(?P<pk>\d+)/$', ShowReaction.as_view(), name='show-reaction'),
    url(r'^reactions/alerter/(?P<pk>\d+)/$', SendNoteAlert.as_view(), name='alert-reaction'),
    url(r'^reactions/resoudre/$', SolveNoteAlert.as_view(), name='resolve-reaction'),

    # follow:
    url(r'^suivre/(?P<pk>\d+)/reactions/$', FollowContentReaction.as_view(), name='follow-reactions'),
    url(r'^suivre/membres/(?P<pk>\d+)/$', FollowNewContent.as_view(), name='follow'),

    # content alerts:
    url(r'^alerter/(?P<pk>\d+)/$', SendContentAlert.as_view(), name='alert-content'),
    url(r'^resoudre/(?P<pk>\d+)/$', SolveContentAlert.as_view(), name='resolve-content'),

    # typo:
    url(r'^reactions/typo/$', WarnTypo.as_view(), name='warn-typo'),

    # create:
    url(r'^nouveau-tutoriel/$',
        CreateContent.as_view(created_content_type='TUTORIAL'), name='create-tutorial'),
    url(r'^nouvel-article/$',
        CreateContent.as_view(created_content_type='ARTICLE'), name='create-article'),
    url(r'^nouveau-billet/$',
        CreateContent.as_view(created_content_type='OPINION'), name='create-opinion'),
    url(r'^nouveau-conteneur/(?P<pk>\d+)/(?P<slug>.+)/(?P<container_slug>.+)/$',
        CreateContainer.as_view(),
        name='create-container'),
    url(r'^nouveau-conteneur/(?P<pk>\d+)/(?P<slug>.+)/$',
        CreateContainer.as_view(),
        name='create-container'),

    url(r'^nouvelle-section/(?P<pk>\d+)/(?P<slug>.+)/(?P<parent_container_slug>.+)/(?P<container_slug>.+)/$',
        CreateExtract.as_view(),
        name='create-extract'),
    url(r'^nouvelle-section/(?P<pk>\d+)/(?P<slug>.+)/(?P<container_slug>.+)/$',
        CreateExtract.as_view(),
        name='create-extract'),
    url(r'^nouvelle-section/(?P<pk>\d+)/(?P<slug>.+)/$',
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

    url(r'^editer-section/(?P<pk>\d+)/(?P<slug>.+)/(?P<parent_container_slug>.+)/'
        r'(?P<container_slug>.+)/(?P<extract_slug>.+)/$',
        EditExtract.as_view(),
        name='edit-extract'),
    url(r'^editer-section/(?P<pk>\d+)/(?P<slug>.+)/(?P<container_slug>.+)/(?P<extract_slug>.+)/$',
        EditExtract.as_view(),
        name='edit-extract'),
    url(r'^editer-section/(?P<pk>\d+)/(?P<slug>.+)/(?P<extract_slug>.+)/$',
        EditExtract.as_view(),
        name='edit-extract'),

    url(r'^editer/(?P<pk>\d+)/(?P<slug>.+)/$', EditContent.as_view(), name='edit'),
    url(r'^deplacer/$', MoveChild.as_view(), name='move-element'),

    url(r'^historique/(?P<pk>\d+)/(?P<slug>.+)/$', DisplayHistory.as_view(), name='history'),
    url(r'^comparaison/(?P<pk>\d+)/(?P<slug>.+)/$', DisplayDiff.as_view(), name='diff'),
    url(r'^ajouter-auteur/(?P<pk>\d+)/$', AddAuthorToContent.as_view(), name='add-author'),
    url(r'^enlever-auteur/(?P<pk>\d+)/$', RemoveAuthorFromContent.as_view(), name='remove-author'),
    # beta:
    url(r'^activer-beta/(?P<pk>\d+)/(?P<slug>.+)/$', ManageBetaContent.as_view(action='set'),
        name='set-beta'),
    url(r'^desactiver-beta/(?P<pk>\d+)/(?P<slug>.+)/$', ManageBetaContent.as_view(action='inactive'),
        name='inactive-beta'),
    url(r'^stats/(?P<pk>\d+)/(?P<slug>.+)/$', ContentStatisticsView.as_view(),
        name='stats-content'),

    # jsfiddle support:
    url(r'activer-js/', ActivateJSFiddleInContent.as_view(), name='activate-jsfiddle'),

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
    url(r'^importer/archive/nouveau/$', CreateContentFromArchive.as_view(), name='import-new'),
    url(r'^importer/(?P<pk>\d+)/(?P<slug>.+)/$', UpdateContentWithArchive.as_view(), name='import'),

    # tags
    url(r'^tags/$', TagsListView.as_view(), name='tags'),

    url(r'^$', RedirectView.as_view(pattern_name='publication:list', permanent=True), name='list'),
]
