from django.urls import path
from django.views.generic.base import RedirectView

from zds.tutorialv2.views.alerts import SendContentAlert, SolveContentAlert
from zds.tutorialv2.views.archives import CreateContentFromArchive, DownloadContent, UpdateContentWithArchive
from zds.tutorialv2.views.authors import AddAuthorToContent, RemoveAuthorFromContent
from zds.tutorialv2.views.beta import ManageBetaContent
from zds.tutorialv2.views.canonical import EditCanonicalLinkView
from zds.tutorialv2.views.categories import EditCategoriesView
from zds.tutorialv2.views.comments import (
    FollowContentReaction,
    HideReaction,
    SendNoteAlert,
    SendNoteFormView,
    ShowReaction,
    SolveNoteAlert,
    UpdateNoteView,
)
from zds.tutorialv2.views.containers_extracts import (
    CreateContainer,
    CreateExtract,
    DeleteContainerOrExtract,
    EditContainer,
    EditExtract,
    MoveChild,
)
from zds.tutorialv2.views.contents import (
    CreateContentView,
    DeleteContent,
    EditConclusionView,
    EditIntroductionView,
    EditSubtitle,
    EditTitle,
)
from zds.tutorialv2.views.contributors import (
    AddContributorToContent,
    ContentOfContributors,
    RemoveContributorFromContent,
)
from zds.tutorialv2.views.display import (
    ContainerBetaView,
    ContainerDraftView,
    ContainerVersionView,
    ContentBetaView,
    ContentDraftView,
    ContentVersionView,
)
from zds.tutorialv2.views.display.container import ContainerValidationView
from zds.tutorialv2.views.display.content import ContentValidationView
from zds.tutorialv2.views.events import EventsList
from zds.tutorialv2.views.goals import EditGoals, MassEditGoals, ViewContentsByGoal
from zds.tutorialv2.views.help import ChangeHelp, ContentsWithHelps
from zds.tutorialv2.views.history import DisplayDiff, DisplayHistory
from zds.tutorialv2.views.labels import EditLabels, ViewContentsByLabel
from zds.tutorialv2.views.licence import EditContentLicense
from zds.tutorialv2.views.lists import ContentOfAuthor, ListContentReactions, TagsListView
from zds.tutorialv2.views.misc import FollowNewContent, RequestFeaturedContent, WarnTypo
from zds.tutorialv2.views.redirect import RedirectOldContentOfAuthor
from zds.tutorialv2.views.statistics import ContentStatisticsView
from zds.tutorialv2.views.suggestions import AddSuggestionView, RemoveSuggestionView
from zds.tutorialv2.views.tags import EditTags
from zds.tutorialv2.views.thumbnail import EditThumbnailView
from zds.tutorialv2.views.validations_contents import ActivateJSFiddleInContent

feeds = [
    path("flux/rss/", RedirectView.as_view(pattern_name="publication:feed-rss", permanent=True), name="feed-rss"),
    path("flux/atom/", RedirectView.as_view(pattern_name="publication:feed-atom", permanent=True), name="feed-atom"),
]


def get_beta_pages():
    base_pattern = "beta/<int:pk>/<slug:slug>"
    beta_pages = [
        path(
            f"{base_pattern}/<slug:parent_container_slug>/<slug:container_slug>/",
            ContainerBetaView.as_view(public_is_prioritary=False),
            name="beta-view-container",
        ),
        path(
            f"{base_pattern}/<slug:container_slug>/",
            ContainerBetaView.as_view(public_is_prioritary=False),
            name="beta-view-container",
        ),
        path(f"{base_pattern}/", ContentBetaView.as_view(), name="beta-view"),
    ]
    return beta_pages


def get_validation_pages():
    base_pattern = "validation/<int:pk>/<slug:slug>"
    pages = [
        path(
            f"{base_pattern}/<slug:parent_container_slug>/<slug:container_slug>/",
            ContainerValidationView.as_view(public_is_prioritary=False),
            name="validation-view-container",
        ),
        path(
            f"{base_pattern}/<slug:container_slug>/",
            ContainerValidationView.as_view(public_is_prioritary=False),
            name="validation-view-container",
        ),
        path(f"{base_pattern}/", ContentValidationView.as_view(), name="validation-view"),
    ]
    return pages


def get_version_pages():
    base_pattern = "version/<str:version>/<int:pk>/<slug:slug>"
    specific_version_page = [
        path(
            f"{base_pattern}/<slug:parent_container_slug>/<slug:container_slug>/",
            ContainerVersionView.as_view(),
            name="view-container-version",
        ),
        path(f"{base_pattern}/<slug:container_slug>/", ContainerVersionView.as_view(), name="view-container-version"),
        path(f"{base_pattern}/", ContentVersionView.as_view(), name="view-version"),
    ]
    return specific_version_page


urlpatterns = (
    feeds
    + get_version_pages()
    + get_beta_pages()
    + get_validation_pages()
    + [
        path(
            "voir/<str:username>/", ContentOfAuthor.as_view(type="ALL", context_object_name="contents"), name="find-all"
        ),
        path(
            "contributions/<str:username>/",
            ContentOfContributors.as_view(type="ALL", context_object_name="contribution_contents"),
            name="find-contribution-all",
        ),
        path("commentaires/<int:pk>/", ListContentReactions.as_view(), name="list-content-reactions"),
        path("tutoriels/<int:pk>/", RedirectOldContentOfAuthor.as_view(type="TUTORIAL"), name="legacy-find-tutorial"),
        path("articles/<int:pk>/", RedirectOldContentOfAuthor.as_view(type="ARTICLE"), name="legacy-find-article"),
        path("tribunes/<int:pk>/", RedirectOldContentOfAuthor.as_view(type="OPINION"), name="legacy-find-opinion"),
        path("aides/", ContentsWithHelps.as_view(), name="helps"),
        path("aides/<int:pk>/change/", ChangeHelp.as_view(), name="helps-change"),
        path(
            "<int:pk>/<slug:slug>/<slug:parent_container_slug>/<slug:container_slug>/",
            ContainerDraftView.as_view(public_is_prioritary=False),
            name="view-container",
        ),
        path(
            "<int:pk>/<slug:slug>/<slug:container_slug>/",
            ContainerDraftView.as_view(public_is_prioritary=False),
            name="view-container",
        ),
        path("<int:pk>/<slug:slug>/", ContentDraftView.as_view(public_is_prioritary=False), name="view"),
        path("telecharger/<int:pk>/<slug:slug>/", DownloadContent.as_view(), name="download-zip"),
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
        path("nouveau-contenu/<str:created_content_type>/", CreateContentView.as_view(), name="create-content"),
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
        path("deplacer/", MoveChild.as_view(), name="move-element"),
        path("historique/<int:pk>/<slug:slug>/", DisplayHistory.as_view(), name="history"),
        path("comparaison/<int:pk>/<slug:slug>/", DisplayDiff.as_view(), name="diff"),
        path("ajouter-contributeur/<int:pk>/", AddContributorToContent.as_view(), name="add-contributor"),
        path("enlever-contributeur/<int:pk>/", RemoveContributorFromContent.as_view(), name="remove-contributor"),
        path("ajouter-auteur/<int:pk>/", AddAuthorToContent.as_view(), name="add-author"),
        path("enlever-auteur/<int:pk>/", RemoveAuthorFromContent.as_view(), name="remove-author"),
        path("modifier-titre/<int:pk>/", EditTitle.as_view(), name="edit-title"),
        path("modifier-sous-titre/<int:pk>/", EditSubtitle.as_view(), name="edit-subtitle"),
        path("modifier-miniature/<int:pk>/", EditThumbnailView.as_view(), name="edit-thumbnail"),
        path("modifier-introduction/<int:pk>/", EditIntroductionView.as_view(), name="edit-introduction"),
        path("modifier-conclusion/<int:pk>/", EditConclusionView.as_view(), name="edit-conclusion"),
        path("modifier-licence/<int:pk>/", EditContentLicense.as_view(), name="edit-license"),
        path("modifier-tags/<int:pk>/", EditTags.as_view(), name="edit-tags"),
        path("modifier-lien-canonique/<int:pk>", EditCanonicalLinkView.as_view(), name="edit-canonical-link"),
        path("modifier-categories/<int:pk>/", EditCategoriesView.as_view(), name="edit-categories"),
        # beta:
        path("activer-beta/<int:pk>/<slug:slug>/", ManageBetaContent.as_view(action="set"), name="set-beta"),
        path(
            "desactiver-beta/<int:pk>/<slug:slug>/",
            ManageBetaContent.as_view(action="inactive"),
            name="inactive-beta",
        ),
        path("stats/<int:pk>/<slug:slug>/", ContentStatisticsView.as_view(), name="stats-content"),
        path("ajouter-suggestion/<int:pk>/", AddSuggestionView.as_view(), name="add-suggestion"),
        path("enlever-suggestion/<int:pk>/", RemoveSuggestionView.as_view(), name="remove-suggestion"),
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
        # Goal-based classification
        path("modifier-objectifs/", MassEditGoals.as_view(), name="mass-edit-goals"),
        path("modifier-objectifs/<int:pk>/", EditGoals.as_view(), name="edit-goals"),
        path("objectifs/", ViewContentsByGoal.as_view(), name="view-goals"),
        # Label-based classification
        path("modifier-labels/<int:pk>/", EditLabels.as_view(), name="edit-labels"),
        path("labels/<slug:slug>/", ViewContentsByLabel.as_view(), name="view-labels"),
    ]
)
