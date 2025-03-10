import logging

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F
from django.http import Http404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from zds.featured.mixins import FeatureableMixin
from zds.notification.models import ContentReactionAnswerSubscription
from zds.tutorialv2 import signals
from zds.tutorialv2.forms import (
    AcceptValidationForm,
    AskValidationForm,
    CancelValidationForm,
    JsFiddleActivationForm,
    PickOpinionForm,
    PromoteOpinionToArticleForm,
    PublicationForm,
    RejectValidationForm,
    RevokeValidationForm,
    UnpickOpinionForm,
    UnpublicationForm,
    WarnTypoForm,
)
from zds.tutorialv2.mixins import SingleContentDetailViewMixin, SingleOnlineContentDetailViewMixin
from zds.tutorialv2.models.database import (
    ContentContribution,
    ContentReaction,
    ContentSuggestion,
    PublishableContent,
    PublishedContent,
)
from zds.tutorialv2.utils import last_participation_is_old, mark_read
from zds.tutorialv2.views.canonical import EditCanonicalLinkForm
from zds.tutorialv2.views.contents import EditSubtitleForm, EditTitleForm
from zds.tutorialv2.views.contributors import ContributionForm
from zds.tutorialv2.views.display.config import (
    ConfigForBetaView,
    ConfigForContentDraftView,
    ConfigForOnlineView,
    ConfigForValidationView,
    ConfigForVersionView,
)
from zds.tutorialv2.views.goals import EditGoalsForm
from zds.tutorialv2.views.labels import EditLabelsForm
from zds.tutorialv2.views.licence import EditContentLicenseForm
from zds.tutorialv2.views.suggestions import SearchSuggestionForm
from zds.tutorialv2.views.tags import EditTagsForm
from zds.tutorialv2.views.thumbnail import EditThumbnailForm
from zds.utils.models import CommentVote
from zds.utils.paginator import make_pagination

logger = logging.getLogger(__name__)


class ContentBaseView(SingleContentDetailViewMixin):
    template_name = "tutorialv2/view/content.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["base_url"] = self.get_base_url()
        context["is_js"] = self.object.js_support
        context["gallery"] = self.object.gallery
        context["public_content_object"] = self.public_content_object
        context = self.add_contributions_context(context)
        context = self.add_suggestions_context(context)
        context["pm_link"] = self.object.get_absolute_contact_url(_("À propos de"))
        versioned = self.versioned_object

        data_form_ask_validation = {"source": self.object.source, "version": self.sha}
        context["form_ask_validation"] = AskValidationForm(content=versioned, initial=data_form_ask_validation)

        validation = self.object.get_validation()
        context["validation"] = validation

        if validation:
            context["form_valid"] = AcceptValidationForm(validation, initial={"source": self.object.source})
            context["form_reject"] = RejectValidationForm(validation)
            context["form_cancel_validation"] = CancelValidationForm(validation)

        data_form_revoke = {"version": versioned.sha_public}
        context["form_revoke"] = RevokeValidationForm(versioned, initial=data_form_revoke)

        data_form_unpublication = data_form_revoke
        context["form_unpublication"] = UnpublicationForm(versioned, initial=data_form_unpublication)

        context["form_warn_typo"] = WarnTypoForm(versioned, versioned, public=False)
        context["form_jsfiddle"] = JsFiddleActivationForm(initial={"js_support": self.object.js_support})
        context["form_edit_license"] = EditContentLicenseForm(versioned)

        context["form_publication"] = PublicationForm(versioned, initial={"source": self.object.source})
        context["gallery"] = self.object.gallery
        context["alerts"] = self.object.alerts_on_this_content.all()
        data_form_pick = data_form_revoke
        context["form_pick"] = PickOpinionForm(self.versioned_object, initial=data_form_pick)
        data_form_unpick = data_form_revoke
        context["form_unpick"] = UnpickOpinionForm(self.versioned_object, initial=data_form_unpick)
        data_form_convert = data_form_revoke
        context["form_convert"] = PromoteOpinionToArticleForm(self.versioned_object, initial=data_form_convert)
        context["form_warn_typo"] = WarnTypoForm(self.versioned_object, self.versioned_object)
        context["form_edit_tags"] = EditTagsForm(self.versioned_object, self.object)
        context["form_edit_canonical_link"] = EditCanonicalLinkForm(self.object)
        context["form_edit_goals"] = EditGoalsForm(self.object)
        context["form_edit_labels"] = EditLabelsForm(self.object)
        context["is_antispam"] = self.object.antispam(self.request.user)
        return context

    def add_suggestions_context(self, context):
        content_suggestions = ContentSuggestion.objects.filter(publication=self.object)
        context["content_suggestions"] = content_suggestions.all()
        excluded_for_search = [str(x.suggestion.pk) for x in content_suggestions]
        excluded_for_search.append(str(self.object.pk))
        context["form_add_suggestion"] = SearchSuggestionForm(
            content=self.object, initial={"excluded_pk": ",".join(excluded_for_search)}
        )
        return context

    def add_contributions_context(self, context):
        context["form_add_contributor"] = ContributionForm(content=self.object)
        context["contributions"] = (
            ContentContribution.objects.filter(content=self.object)
            .select_related("user")
            .order_by("contribution_role__position")
        )
        return context

    def get_base_url(self):
        raise NotImplementedError


class ContentDraftView(LoginRequiredMixin, ContentBaseView):
    """Show the draft page for a publication."""

    model = PublishableContent
    must_be_author = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_edit_title"] = EditTitleForm(self.versioned_object)
        context["form_edit_subtitle"] = EditSubtitleForm(self.versioned_object)
        context["form_edit_thumbnail"] = EditThumbnailForm(self.versioned_object)
        context["display_config"] = ConfigForContentDraftView(self.request.user, self.object, self.versioned_object)
        return context

    def get_base_url(self):
        route_parameters = {"pk": self.object.pk, "slug": self.object.slug}
        url = reverse("content:view", kwargs=route_parameters)
        return url


class ContentVersionView(LoginRequiredMixin, ContentBaseView):
    """Show the page for a specific version of a publication."""

    model = PublishableContent

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["display_config"] = ConfigForVersionView(self.request.user, self.object, self.versioned_object)
        return context

    def get_base_url(self):
        route_parameters = {
            "pk": self.object.pk,
            "slug": self.object.slug,
            "version": self.versioned_object.current_version,
        }
        url = reverse("content:view-version", kwargs=route_parameters)
        return url


class ContentOnlineView(FeatureableMixin, SingleOnlineContentDetailViewMixin, ContentBaseView):
    """Show the online page of a publication."""

    model = PublishedContent

    current_content_type = ""
    verbose_type_name = _("contenu")
    verbose_type_name_plural = _("contenus")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = self.add_pager_context(context)
        context["content_suggestions_random"] = ContentSuggestion.get_random_public_suggestions(
            self.object, count=settings.ZDS_APP["content"]["suggestions_per_page"]
        )

        comments = self.get_comments()

        make_pagination(
            context,
            self.request,
            comments,
            settings.ZDS_APP["content"]["notes_per_page"],
            context_list_name="reactions",
            with_previous_item=True,
        )

        # optimize requests:
        votes = CommentVote.objects.filter(user_id=self.request.user.id, comment__in=comments).all()
        context["user_like"] = [vote.comment_id for vote in votes if vote.positive]
        context["user_dislike"] = [vote.comment_id for vote in votes if not vote.positive]

        if self.request.user.has_perm("tutorialv2.change_contentreaction"):
            context["user_can_modify"] = [reaction.pk for reaction in comments]
        else:
            context["user_can_modify"] = [reaction.pk for reaction in comments if reaction.author == self.request.user]

        context["subscriber_count"] = ContentReactionAnswerSubscription.objects.get_subscriptions(self.object).count()
        context["reading_time"] = self.get_reading_time()

        if self.request.user.is_authenticated:
            if len(context["reactions"]) > 0:
                signals.content_read.send(
                    sender=context["reactions"][0].__class__, instances=context["reactions"], user=self.request.user
                )
            signals.content_read.send(
                sender=self.object.__class__, instance=self.object, user=self.request.user, target=PublishableContent
            )
        if last_participation_is_old(self.object, self.request.user):
            mark_read(self.object, self.request.user)

        context["display_config"] = ConfigForOnlineView(self.request.user, self.object, self.versioned_object)
        return context

    def get_reading_time(self):
        """Convert to minutes"""
        try:
            char_count = self.object.public_version.char_count
            if char_count:
                chars_per_minute = settings.ZDS_APP["content"]["characters_per_minute"]
                reading_time = int(self.versioned_object.get_tree_level() * char_count / chars_per_minute)
                return reading_time
            else:
                logger.warning("For unknown reason content with id %s has no char count", self.object.pk)
                return 0
        except ZeroDivisionError as e:
            logger.warning("could not compute reading time: setting characters_per_minute is set to zero (error=%s)", e)

    def get_comments(self):
        return list(
            ContentReaction.objects.select_related("author")
            .select_related("author__profile")
            .select_related("hat")
            .select_related("editor")
            .prefetch_related("alerts_on_this_comment")
            .prefetch_related("alerts_on_this_comment__author")
            .filter(related_content__pk=self.object.pk)
            .order_by("pubdate")
        )

    def add_pager_context(self, context):
        if self.current_content_type in ("ARTICLE", "OPINION"):
            queryset_pagination = PublishedContent.objects.filter(
                content_type=self.current_content_type, must_redirect=False
            )
            if self.current_content_type == "OPINION":
                queryset_pagination = queryset_pagination.filter(content__sha_picked=F("sha_public"))

            context["previous_content"] = (
                queryset_pagination.filter(publication_date__lt=self.public_content_object.publication_date)
                .order_by("-publication_date")
                .first()
            )
            context["next_content"] = (
                queryset_pagination.filter(publication_date__gt=self.public_content_object.publication_date)
                .order_by("publication_date")
                .first()
            )
        return context

    def get_base_url(self):
        return self.object.get_absolute_url_online()


class ArticleOnlineView(ContentOnlineView):
    """Show the online page of a tutorial."""

    current_content_type = "ARTICLE"
    verbose_type_name = _("article")
    verbose_type_name_plural = _("articles")


class TutorialOnlineView(ContentOnlineView):
    """Show the online page of a tutorial."""

    current_content_type = "TUTORIAL"
    verbose_type_name = _("tutoriel")
    verbose_type_name_plural = _("tutoriels")


class OpinionOnlineView(ContentOnlineView):
    """Show the online page of an opinion."""

    current_content_type = "OPINION"
    verbose_type_name = _("billet")
    verbose_type_name_plural = _("billets")


class ContentBetaView(LoginRequiredMixin, ContentBaseView):
    """Show the beta page of a content."""

    must_be_author = False

    sha = None

    def get_object(self, queryset=None):
        """rewritten to ensure that the version is set to beta, raise Http404 if there is no such version"""
        obj = super().get_object(queryset)

        if not obj.sha_beta:
            raise Http404("Aucune bêta n'existe pour ce contenu.")
        else:
            self.sha = obj.sha_beta

        # make the slug always right in URLs resolution:
        if "slug" in self.kwargs:
            self.kwargs["slug"] = obj.slug

        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["display_config"] = ConfigForBetaView(self.request.user, self.object, self.versioned_object)
        return context

    def get_base_url(self):
        route_parameters = {"pk": self.object.pk, "slug": self.object.slug}
        url = reverse("content:beta-view", kwargs=route_parameters)
        return url


class ContentValidationView(LoginRequiredMixin, ContentBaseView):
    """Show the validation page of a content."""

    must_be_author = False

    sha = None

    def get_object(self, queryset=None):
        """Ensure that the version is set to validation, raise Http404 if there is no such version."""
        obj = super().get_object(queryset)

        if not obj.sha_validation:
            raise Http404("Aucune version en validation n'existe pour ce contenu.")
        else:
            self.sha = obj.sha_validation

        # make the slug always right in URLs resolution:
        if "slug" in self.kwargs:
            self.kwargs["slug"] = obj.slug

        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["display_config"] = ConfigForValidationView(self.request.user, self.object, self.versioned_object)
        return context

    def get_base_url(self):
        route_parameters = {"pk": self.object.pk, "slug": self.object.slug}
        url = reverse("content:validation-view", kwargs=route_parameters)
        return url
