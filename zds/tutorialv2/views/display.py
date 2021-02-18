import logging

from django.db.models import F
from django.conf import settings
from django.http import Http404
from django.utils.translation import gettext_lazy as _

from zds.featured.mixins import FeatureableMixin
from zds.tutorialv2 import signals
from zds.notification.models import ContentReactionAnswerSubscription
from zds.tutorialv2.forms import (
    RevokeValidationForm,
    UnpublicationForm,
    WarnTypoForm,
    PickOpinionForm,
    UnpickOpinionForm,
    PromoteOpinionToArticleForm,
    SearchSuggestionForm,
    EditContentTagsForm,
)
from zds.tutorialv2.mixins import SingleOnlineContentDetailViewMixin

from zds.tutorialv2.models.database import (
    PublishableContent,
    PublishedContent,
    ContentReaction,
    ContentSuggestion,
    ContentContribution,
)
from zds.tutorialv2.utils import search_container_or_404, last_participation_is_old, mark_read
from zds.tutorialv2.views.containers_extracts import DisplayContainer
from zds.tutorialv2.views.contents import DisplayContent
from zds.utils.models import CommentVote
from zds.utils.paginator import make_pagination

logger = logging.getLogger(__name__)


class DisplayOnlineContent(FeatureableMixin, SingleOnlineContentDetailViewMixin):
    """Base class that can show any online content"""

    model = PublishedContent
    template_name = "tutorialv2/view/content_online.html"

    current_content_type = ""
    verbose_type_name = _("contenu")
    verbose_type_name_plural = _("contenus")

    def featured_request_allowed(self):
        """Featured request is not allowed on obsolete content and opinions"""
        return self.object.type != "OPINION" and not self.object.is_obsolete

    def get_context_data(self, **kwargs):
        """Show the given tutorial if exists."""
        context = super(DisplayOnlineContent, self).get_context_data(**kwargs)

        if context["is_staff"]:
            if self.current_content_type == "OPINION":
                context["alerts"] = self.object.alerts_on_this_content.all()
            context["formRevokeValidation"] = RevokeValidationForm(
                self.versioned_object, initial={"version": self.versioned_object.sha_public}
            )
            context["formUnpublication"] = UnpublicationForm(
                self.versioned_object, initial={"version": self.versioned_object.sha_public}
            )

        context["formWarnTypo"] = WarnTypoForm(self.versioned_object, self.versioned_object)

        queryset_reactions = (
            ContentReaction.objects.select_related("author")
            .select_related("author__profile")
            .select_related("hat")
            .select_related("editor")
            .prefetch_related("alerts_on_this_comment")
            .prefetch_related("alerts_on_this_comment__author")
            .filter(related_content__pk=self.object.pk)
            .order_by("pubdate")
        )

        # pagination of articles and opinions
        context["previous_content"] = None
        context["next_content"] = None

        if self.current_content_type in ("ARTICLE", "OPINION"):
            queryset_pagination = PublishedContent.objects.filter(
                content_type=self.current_content_type, must_redirect=False
            )
            
        if self.current_content_type == 'OPINION':
            queryset_pagination = queryset_pagination.filter(content__sha_picked=F('sha_public'))

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

        if self.versioned_object.type == "OPINION":
            context["formPickOpinion"] = PickOpinionForm(
                self.versioned_object, initial={"version": self.versioned_object.sha_public}
            )
            context["formUnpickOpinion"] = UnpickOpinionForm(
                self.versioned_object, initial={"version": self.versioned_object.sha_public}
            )
            context["formConvertOpinion"] = PromoteOpinionToArticleForm(
                self.versioned_object, initial={"version": self.versioned_object.sha_public}
            )
        else:
            context["content_suggestions"] = ContentSuggestion.objects.filter(publication=self.object)
            excluded_for_search = [str(x.suggestion.pk) for x in context["content_suggestions"]]
            excluded_for_search.append(str(self.object.pk))
            context["formAddSuggestion"] = SearchSuggestionForm(
                content=self.object, initial={"excluded_pk": ",".join(excluded_for_search)}
            )

        context["form_edit_tags"] = EditContentTagsForm(self.versioned_object, self.object)

        # pagination of comments
        make_pagination(
            context,
            self.request,
            queryset_reactions,
            settings.ZDS_APP["content"]["notes_per_page"],
            context_list_name="reactions",
            with_previous_item=True,
        )

        # is JS activated ?
        context["is_js"] = True
        if not self.object.js_support:
            context["is_js"] = False

        # optimize requests:
        votes = CommentVote.objects.filter(user_id=self.request.user.id, comment__in=queryset_reactions).all()
        context["user_like"] = [vote.comment_id for vote in votes if vote.positive]
        context["user_dislike"] = [vote.comment_id for vote in votes if not vote.positive]

        if self.request.user.has_perm("tutorialv2.change_contentreaction"):
            context["user_can_modify"] = [reaction.pk for reaction in queryset_reactions]
        else:
            context["user_can_modify"] = [
                reaction.pk for reaction in queryset_reactions if reaction.author == self.request.user
            ]

        context["is_antispam"] = self.object.antispam()
        context["pm_link"] = self.object.get_absolute_contact_url(_("À propos de"))
        context["subscriber_count"] = ContentReactionAnswerSubscription.objects.get_subscriptions(self.object).count()
        # We need reading time expressed in minutes
        try:
            char_count = self.object.public_version.char_count
            if char_count:
                context["reading_time"] = int(
                    self.versioned_object.get_tree_level()
                    * char_count
                    / settings.ZDS_APP["content"]["characters_per_minute"]
                )
        except ZeroDivisionError as e:
            logger.warning("could not compute reading time: setting characters_per_minute is set to zero (error=%s)", e)

        if self.request.user.is_authenticated:
            for reaction in context["reactions"]:
                signals.content_read.send(sender=reaction.__class__, instance=reaction, user=self.request.user)
            signals.content_read.send(
                sender=self.object.__class__, instance=self.object, user=self.request.user, target=PublishableContent
            )
        if last_participation_is_old(self.object, self.request.user):
            mark_read(self.object, self.request.user)

        context["contributions"] = ContentContribution.objects.filter(content=self.object).order_by(
            "contribution_role__position"
        )
        context["content_suggestions_random"] = ContentSuggestion.objects.filter(publication=self.object).order_by("?")[
            : settings.ZDS_APP["content"]["suggestions_per_page"]
        ]

        return context


class DisplayOnlineArticle(DisplayOnlineContent):
    """Displays the list of published articles"""

    current_content_type = "ARTICLE"
    verbose_type_name = _("article")
    verbose_type_name_plural = _("articles")


class DisplayOnlineTutorial(DisplayOnlineContent):
    """Displays the list of published tutorials"""

    current_content_type = "TUTORIAL"
    verbose_type_name = _("tutoriel")
    verbose_type_name_plural = _("tutoriels")


class DisplayOnlineOpinion(DisplayOnlineContent):
    """Displays the list of published articles"""

    current_content_type = "OPINION"
    verbose_type_name = _("billet")
    verbose_type_name_plural = _("billets")


class DisplayOnlineContainer(SingleOnlineContentDetailViewMixin):
    """Base class that can show any content in any state"""

    template_name = "tutorialv2/view/container_online.html"
    current_content_type = "TUTORIAL"  # obviously, an article cannot have container !

    def get_context_data(self, **kwargs):
        context = super(DisplayOnlineContainer, self).get_context_data(**kwargs)
        container = search_container_or_404(self.versioned_object, self.kwargs)

        context["container"] = container
        context["pm_link"] = self.object.get_absolute_contact_url(_("À propos de"))

        context["formWarnTypo"] = WarnTypoForm(
            self.versioned_object, container, initial={"target": container.get_path(relative=True)}
        )

        # pagination: search for `previous` and `next`, if available
        if not self.versioned_object.has_extracts():
            chapters = self.versioned_object.get_list_of_chapters()
            try:
                position = chapters.index(container)
            except ValueError:
                pass  # this is not (yet?) a chapter
            else:
                context["has_pagination"] = True
                context["previous"] = None
                context["next"] = None
                if position == 0:
                    context["previous"] = container.parent
                if position > 0:
                    previous_chapter = chapters[position - 1]
                    if previous_chapter.parent == container.parent:
                        context["previous"] = previous_chapter
                    else:
                        context["previous"] = container.parent
                if position < len(chapters) - 1:
                    next_chapter = chapters[position + 1]
                    if next_chapter.parent == container.parent:
                        context["next"] = next_chapter
                    else:
                        context["next"] = next_chapter.parent

        return context


class DisplayBetaContent(DisplayContent):
    """View to get the beta version of a content"""

    sha = None

    def get_object(self, queryset=None):
        """rewritten to ensure that the version is set to beta, raise Http404 if there is no such version"""
        obj = super(DisplayBetaContent, self).get_object(queryset)

        if not obj.sha_beta:
            raise Http404("Aucune bêta n'existe pour ce contenu.")
        else:
            self.sha = obj.sha_beta

        # make the slug always right in URLs resolution:
        if "slug" in self.kwargs:
            self.kwargs["slug"] = obj.slug

        return obj

    def get_context_data(self, **kwargs):
        context = super(DisplayBetaContent, self).get_context_data(**kwargs)
        context["pm_link"] = self.object.get_absolute_contact_url()
        return context


class DisplayBetaContainer(DisplayContainer):
    """View to get the beta version of a container"""

    sha = None

    def get_object(self, queryset=None):
        """rewritten to ensure that the version is set to beta, raise Http404 if there is no such version"""
        obj = super(DisplayBetaContainer, self).get_object(queryset)

        if not obj.sha_beta:
            raise Http404("Aucune bêta n'existe pour ce contenu.")
        else:
            self.sha = obj.sha_beta

        # make the slug always right in URLs resolution:
        if "slug" in self.kwargs:
            self.kwargs["slug"] = obj.slug

        return obj

    def get_context_data(self, **kwargs):
        context = super(DisplayBetaContainer, self).get_context_data(**kwargs)
        context["pm_link"] = self.object.get_absolute_contact_url()
        return context
