from django.urls import path, re_path
from django.views.generic.base import RedirectView

from zds.tutorialv2.views.contents import DisplayContent, CreateContent, EditContent, EditContentLicense, DeleteContent
from zds.tutorialv2.views.events import EventsList
from zds.tutorialv2.views.validations_contents import ActivateJSFiddleInContent
from zds.tutorialv2.views.containers_extracts import (
    CreateContainer,
    DisplayContainer,
    EditContainer,
    CreateExtract,
    EditExtract,
    DeleteContainerOrExtract,
    MoveChild,
)
from zds.tutorialv2.views.beta import ManageBetaContent
from zds.tutorialv2.views.display import DisplayBetaContent, DisplayBetaContainer
from zds.tutorialv2.views.history import DisplayHistory, DisplayDiff
from zds.tutorialv2.views.help import ContentsWithHelps, ChangeHelp
from zds.tutorialv2.views.authors import AddAuthorToContent, RemoveAuthorFromContent
from zds.tutorialv2.views.redirect import RedirectOldContentOfAuthor
from zds.tutorialv2.views.archives import DownloadContent, UpdateContentWithArchive, CreateContentFromArchive
from zds.tutorialv2.views.contributors import (
    AddContributorToContent,
    RemoveContributorFromContent,
    ContentOfContributors,
)
from zds.tutorialv2.views.editorialization import RemoveSuggestion, AddSuggestion, EditContentTags

from zds.tutorialv2.views.lists import TagsListView, ContentOfAuthor, ListContentReactions
from zds.tutorialv2.views.alerts import SendContentAlert, SolveContentAlert
from zds.tutorialv2.views.misc import RequestFeaturedContent, FollowNewContent, WarnTypo
from zds.tutorialv2.views.statistics import ContentStatisticsView
from zds.tutorialv2.views.comments import (
    SendNoteFormView,
    UpdateNoteView,
    HideReaction,
    ShowReaction,
    SendNoteAlert,
    SolveNoteAlert,
    FollowContentReaction,
)

urlpatterns = [
    # Flux
    path("flux/rss/", RedirectView.as_view(pattern_name="publication:feed-rss", permanent=True), name="feed-rss"),
    path("flux/atom/", RedirectView.as_view(pattern_name="publication:feed-atom", permanent=True), name="feed-atom"),
    path("voir/<str:username>/", ContentOfAuthor.as_view(type="ALL", context_object_name="contents"), name="find-all"),
    path(
        "contributions/<str:username>/",
        ContentOfContributors.as_view(type="ALL", context_object_name="contribution_contents"),
        name="find-contribution-all",
    ),
    path("commentaires/<int:pk>/", ListContentReactions.as_view(), name="list-content-reactions"),
    path("tutoriels/<int:pk>/", RedirectOldContentOfAuthor.as_view(type="TUTORIAL")),
    path("articles/<int:pk>/", RedirectOldContentOfAuthor.as_view(type="ARTICLE")),
    path("tribunes/<int:pk>/", RedirectOldContentOfAuthor.as_view(type="OPINION")),
    path("aides/", ContentsWithHelps.as_view(), name="helps"),
    path("aides/<int:pk>/change/", ChangeHelp.as_view(), name="helps-change"),
    path(
        "<int:pk>/<slug:slug>/<slug:parent_container_slug>/<slug:container_slug>/",
        DisplayContainer.as_view(public_is_prioritary=False),
        name="view-container",
    ),
    path(
        "<int:pk>/<slug:slug>/<slug:container_slug>/",
        DisplayContainer.as_view(public_is_prioritary=False),
        name="view-container",
    ),
    path("<int:pk>/<slug:slug>/", DisplayContent.as_view(public_is_prioritary=False), name="view"),
    path("telecharger/<int:pk>/<slug:slug>/", DownloadContent.as_view(), name="download-zip"),
    # beta:
    path(
        "beta/<int:pk>/<slug:slug>/<slug:parent_container_slug>/<slug:container_slug>/",
        DisplayBetaContainer.as_view(public_is_prioritary=False),
        name="beta-view-container",
    ),
    path(
        "beta/<int:pk>/<slug:slug>/<slug:container_slug>/",
        DisplayBetaContainer.as_view(public_is_prioritary=False),
        name="beta-view-container",
    ),
    path("beta/<int:pk>/<slug:slug>/", DisplayBetaContent.as_view(), name="beta-view"),
    # reactions:
    path("reactions/ajouter/", SendNoteFormView.as_view(redirection_is_needed=False), name="add-reaction"),
    path("reactions/editer/", UpdateNoteView.as_view(redirection_is_needed=False), name="update-reaction"),
    path("reactions/cacher/<int:pk>/", HideReaction.as_view(), name="hide-reaction"),
    path("reactions/afficher/<int:pk>/", ShowReaction.as_view(), name="show-reaction"),
    path("reactions/alerter/<int:pk>/", SendNoteAlert.as_view(), name="alert-reaction"),
    path("reactions/resoudre/", SolveNoteAlert.as_view(), name="resolve-reaction"),
    # follow:
    path("suivre/<int:pk>/reactions/", FollowContentReaction.as_view(), name="follow-reactions"),
    path("suivre/membres/<int:pk>/", FollowNewContent.as_view(), name="follow"),
    # request
    path("requete/<int:pk>/", RequestFeaturedContent.as_view(), name="request-featured"),
    # content alerts:
    path("alerter/<int:pk>/", SendContentAlert.as_view(), name="alert-content"),
    path("resoudre/<int:pk>/", SolveContentAlert.as_view(), name="resolve-content"),
    # typo:
    path("reactions/typo/", WarnTypo.as_view(), name="warn-typo"),
    # create:
    path("nouveau-contenu/<str:created_content_type>/", CreateContent.as_view(), name="create-content"),
    path(
        "nouveau-conteneur/<int:pk>/<slug:slug>/<slug:container_slug>/",
        CreateContainer.as_view(),
        name="create-container",
    ),
    path("nouveau-conteneur/<int:pk>/<slug:slug>/", CreateContainer.as_view(), name="create-container"),
    path(
        "nouvelle-section/<int:pk>/<slug:slug>/<slug:parent_container_slug>/<slug:container_slug>/",
        CreateExtract.as_view(),
        name="create-extract",
    ),
    path(
        "nouvelle-section/<int:pk>/<slug:slug>/<slug:container_slug>/",
        CreateExtract.as_view(),
        name="create-extract",
    ),
    path("nouvelle-section/<int:pk>/<slug:slug>/", CreateExtract.as_view(), name="create-extract"),
    # edit:
    path(
        "editer-conteneur/<int:pk>/<slug:slug>/<slug:parent_container_slug>/" r"<slug:container_slug>/",
        EditContainer.as_view(),
        name="edit-container",
    ),
    path(
        "editer-conteneur/<int:pk>/<slug:slug>/<slug:container_slug>/",
        EditContainer.as_view(),
        name="edit-container",
    ),
    path(
        "editer-section/<int:pk>/<slug:slug>/<slug:parent_container_slug>/<slug:container_slug>/<slug:extract_slug>/",
        EditExtract.as_view(),
        name="edit-extract",
    ),
    path(
        "editer-section/<int:pk>/<slug:slug>/<slug:container_slug>/<slug:extract_slug>/",
        EditExtract.as_view(),
        name="edit-extract",
    ),
    path("editer-section/<int:pk>/<slug:slug>/<slug:extract_slug>/", EditExtract.as_view(), name="edit-extract"),
    path("editer/<int:pk>/<slug:slug>/", EditContent.as_view(), name="edit"),
    path("deplacer/", MoveChild.as_view(), name="move-element"),
    path("historique/<int:pk>/<slug:slug>/", DisplayHistory.as_view(), name="history"),
    path("comparaison/<int:pk>/<slug:slug>/", DisplayDiff.as_view(), name="diff"),
    path("ajouter-contributeur/<int:pk>/", AddContributorToContent.as_view(), name="add-contributor"),
    path("enlever-contributeur/<int:pk>/", RemoveContributorFromContent.as_view(), name="remove-contributor"),
    path("ajouter-auteur/<int:pk>/", AddAuthorToContent.as_view(), name="add-author"),
    path("enlever-auteur/<int:pk>/", RemoveAuthorFromContent.as_view(), name="remove-author"),
    # Modify the license
    path("modifier-licence/<int:pk>/", EditContentLicense.as_view(), name="edit-license"),
    # Modify the tags
    path("modifier-tags/<int:pk>/", EditContentTags.as_view(), name="edit-tags"),
    # beta:
    path("activer-beta/<int:pk>/<slug:slug>/", ManageBetaContent.as_view(action="set"), name="set-beta"),
    path(
        "desactiver-beta/<int:pk>/<slug:slug>/",
        ManageBetaContent.as_view(action="inactive"),
        name="inactive-beta",
    ),
    path("stats/<int:pk>/<slug:slug>/", ContentStatisticsView.as_view(), name="stats-content"),
    path("ajouter-suggestion/<int:pk>/", AddSuggestion.as_view(), name="add-suggestion"),
    path("enlever-suggestion/<int:pk>/", RemoveSuggestion.as_view(), name="remove-suggestion"),
    # jsfiddle support:
    path("activer-js/", ActivateJSFiddleInContent.as_view(), name="activate-jsfiddle"),
    # delete:
    path(
        "supprimer/<int:pk>/<slug:slug>/<slug:parent_container_slug>/<slug:container_slug>/<slug:object_slug>/",
        DeleteContainerOrExtract.as_view(),
        name="delete",
    ),
    path(
        "supprimer/<int:pk>/<slug:slug>/<slug:container_slug>/<slug:object_slug>/",
        DeleteContainerOrExtract.as_view(),
        name="delete",
    ),
    path("supprimer/<int:pk>/<slug:slug>/<slug:object_slug>/", DeleteContainerOrExtract.as_view(), name="delete"),
    path("supprimer/<int:pk>/<slug:slug>/", DeleteContent.as_view(), name="delete"),
    # markdown import
    path("importer/archive/nouveau/", CreateContentFromArchive.as_view(), name="import-new"),
    path("importer/<int:pk>/<slug:slug>/", UpdateContentWithArchive.as_view(), name="import"),
    # tags
    path("tags/", TagsListView.as_view(), name="tags"),
    path("", RedirectView.as_view(pattern_name="publication:list", permanent=True), name="list"),
    # Journal of events
    path("evenements/<int:pk>/", EventsList.as_view(), name="events"),
]
