from urllib.parse import unquote

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as __
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, UpdateView

from zds.forum.models import Topic, TopicRead
from zds.gallery.forms import ImageAsAvatarForm
from zds.member import EMAIL_EDIT
from zds.member.forms import ChangePasswordForm, ChangeUserForm, GitHubTokenForm, KarmaForm, ProfileForm
from zds.member.models import Ban, KarmaNote, NewEmailProvider, Profile
from zds.member.utils import get_bot_account
from zds.notification.models import NewPublicationSubscription, TopicAnswerSubscription
from zds.tutorialv2.models import CONTENT_TYPES
from zds.tutorialv2.models.database import ContentContribution, ContentReaction, PublishedContent
from zds.utils.misc import is_ajax
from zds.utils.templatetags.pluralize_fr import pluralize_fr


class MemberDetail(DetailView):
    """Display details about a profile."""

    context_object_name = "usr"
    model = User
    template_name = "member/profile.html"

    def get_object(self, queryset=None):
        # Use unquote to accept twicely quoted URLs (for instance in MPs
        # sent through emarkdown parser).
        return get_object_or_404(User, username=unquote(self.kwargs["user_name"]))

    def get_summaries(self, profile, hide_forum_activity):
        """
        Returns a summary of this profile's activity, as a list of list of tuples.
        Each first-level list item is an activity category (e.g. contents, forums, etc.)
        Each second-level list item is a stat in this activity category.
        Each tuple is (link url, count, displayed name of the item), where the link url can be None if it's not a link.

        :param profile: The profile.
        :param hide_forum_activity: if true, don't populate the values related to forum activity
        :return: The summary data.
        """
        summaries = []

        if self.request.user.has_perm("member.change_post"):
            count_post = profile.get_post_count_as_staff()
        else:
            count_post = profile.get_post_count()

        count_topic = profile.get_topic_count()
        count_followed_topic = profile.get_followed_topic_count()
        count_tutorials = profile.get_public_tutos().count()
        count_articles = profile.get_public_articles().count()
        count_opinions = profile.get_public_opinions().count()

        summary = []
        if count_tutorials + count_articles + count_opinions == 0:
            summary.append((None, 0, __("Aucun contenu publié")))

        if count_tutorials > 0:
            summary.append(
                (
                    reverse_lazy("tutorial:find-tutorial", args=(profile.user.username,)),
                    count_tutorials,
                    __("tutoriel{}").format(pluralize_fr(count_tutorials)),
                )
            )
        if count_articles > 0:
            summary.append(
                (
                    reverse_lazy("article:find-article", args=(profile.user.username,)),
                    count_articles,
                    __("article{}").format(pluralize_fr(count_articles)),
                )
            )
        if count_opinions > 0:
            summary.append(
                (
                    reverse_lazy("opinion:find-opinion", args=(profile.user.username,)),
                    count_opinions,
                    __("billet{}").format(pluralize_fr(count_opinions)),
                )
            )
        summaries.append(summary)

        summary = []
        if not hide_forum_activity:
            if count_post > 0:
                summary.append(
                    (
                        reverse_lazy("forum:post-find", args=(profile.user.pk,)),
                        count_post,
                        __("message{}").format(pluralize_fr(count_post)),
                    )
                )
            else:
                summary.append((None, 0, __("Aucun message")))
        if not hide_forum_activity and count_topic > 0:
            summary.append(
                (
                    reverse_lazy("forum:topic-find", args=(profile.user.pk,)),
                    count_topic,
                    __("sujet{} créé{}").format(pluralize_fr(count_topic), pluralize_fr(count_topic)),
                )
            )
        user = self.request.user
        is_user_profile = user.is_authenticated and User.objects.get(pk=user.pk).profile == profile
        if count_followed_topic > 0 and is_user_profile:
            summary.append(
                (
                    reverse_lazy("forum:followed-topic-find"),
                    count_followed_topic,
                    __("sujet{} suivi{}").format(
                        pluralize_fr(count_followed_topic), pluralize_fr(count_followed_topic)
                    ),
                )
            )
        if summary:
            summaries.append(summary)

        return summaries

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usr = context["usr"]
        profile = usr.profile
        context["profile"] = profile
        context["topics"] = list(Topic.objects.last_topics_of_a_member(usr, self.request.user))
        followed_query_set = TopicAnswerSubscription.objects.get_objects_followed_by(self.request.user.id)
        followed_topics = list(set(followed_query_set) & set(context["topics"]))
        for topic in context["topics"]:
            topic.is_followed = topic in followed_topics
        context["articles"] = PublishedContent.objects.last_articles_of_a_member_loaded(usr)
        context["opinions"] = PublishedContent.objects.last_opinions_of_a_member_loaded(usr)
        context["tutorials"] = PublishedContent.objects.last_tutorials_of_a_member_loaded(usr)
        context["articles_and_tutorials"] = PublishedContent.objects.last_tutorials_and_articles_of_a_member_loaded(usr)
        context["topic_read"] = TopicRead.objects.list_read_topic_pk(self.request.user, context["topics"])
        context["subscriber_count"] = NewPublicationSubscription.objects.get_subscriptions(self.object).count()
        context["contribution_articles_count"] = (
            ContentContribution.objects.filter(
                user__pk=usr.pk, content__sha_public__isnull=False, content__type=CONTENT_TYPES[1]["name"]
            )
            .values_list("content", flat=True)
            .distinct()
            .count()
        )
        context["contribution_tutorials_count"] = (
            ContentContribution.objects.filter(
                user__pk=usr.pk, content__sha_public__isnull=False, content__type=CONTENT_TYPES[0]["name"]
            )
            .values_list("content", flat=True)
            .distinct()
            .count()
        )
        context["hide_because_banned"] = (
            not profile.end_ban_read
            and not profile.can_read
            and not self.request.user.has_perm("member.change_profile")
        )
        context["content_reactions_count"] = ContentReaction.objects.filter(author=usr).count()
        hide_forum_activity = (
            profile.hide_forum_activity
            and not self.request.user.has_perm("member.change_profile")
            and not profile.user == self.request.user
        )
        context["hide_forum_activity"] = hide_forum_activity

        if self.request.user.has_perm("member.change_profile"):
            sanctions = list(Ban.objects.filter(user=usr).select_related("moderator"))
            notes = list(KarmaNote.objects.filter(user=usr).select_related("moderator"))
            actions = sanctions + notes
            actions.sort(key=lambda action: action.pubdate)
            actions.reverse()
            context["actions"] = actions
            context["karmaform"] = KarmaForm(profile)
            context["alerts"] = profile.alerts_on_this_profile.all().order_by("-pubdate")
            context["has_unsolved_alerts"] = profile.alerts_on_this_profile.filter(solved=False).exists()

        if self.request.user.has_perm("user.change_bannedemailprovider"):
            new_provider = NewEmailProvider.objects.filter(user=usr).first()
            if new_provider is not None:
                context["provider_to_ban"] = new_provider

        context["summaries"] = self.get_summaries(profile, hide_forum_activity)

        return context


def redirect_old_profile_to_new(request, user_name):
    user = get_object_or_404(User, username=user_name)
    return redirect(user.profile, permanent=True)


class UpdateMember(UpdateView):
    """Update a profile."""

    form_class = ProfileForm
    template_name = "member/settings/profile.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_object(self, queryset=None):
        return get_object_or_404(Profile, user=self.request.user)

    def get_form(self, form_class=ProfileForm):
        profile = self.get_object()
        form = form_class(
            initial={
                "biography": profile.biography,
                "site": profile.site,
                "avatar_url": profile.avatar_url,
                "show_sign": profile.show_sign,
                "hide_forum_activity": profile.hide_forum_activity,
                "is_hover_enabled": profile.is_hover_enabled,
                "allow_temp_visual_changes": profile.allow_temp_visual_changes,
                "show_markdown_help": profile.show_markdown_help,
                "email_for_answer": profile.email_for_answer,
                "email_for_new_mp": profile.email_for_new_mp,
                "sign": profile.sign,
                "licence": profile.licence,
            }
        )

        return form

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if "preview" in request.POST and is_ajax(request):
            content = render(request, "misc/preview.part.html", {"text": request.POST.get("text")})
            return StreamingHttpResponse(content)

        if form.is_valid():
            return self.form_valid(form)

        return render(request, self.template_name, {"form": form})

    def form_valid(self, form):
        profile = self.get_object()
        self.update_profile(profile, form)
        self.save_profile(profile)

        response = redirect(self.get_success_url())
        return response

    def update_profile(self, profile, form):
        cleaned_data_options = form.cleaned_data.get("options")
        profile.biography = form.data["biography"]
        profile.site = form.data["site"]
        profile.show_sign = "show_sign" in cleaned_data_options
        profile.is_hover_enabled = "is_hover_enabled" in cleaned_data_options
        profile.allow_temp_visual_changes = "allow_temp_visual_changes" in cleaned_data_options
        profile.show_markdown_help = "show_markdown_help" in cleaned_data_options
        profile.email_for_answer = "email_for_answer" in cleaned_data_options
        profile.email_for_new_mp = "email_for_new_mp" in cleaned_data_options
        profile.hide_forum_activity = "hide_forum_activity" in cleaned_data_options
        profile.avatar_url = form.data["avatar_url"]
        profile.sign = form.data["sign"]
        profile.licence = form.cleaned_data["licence"]

    def get_success_url(self):
        return reverse("update-member")

    def save_profile(self, profile):
        try:
            profile.save()
            profile.user.save()
        except Profile.DoesNotExist:
            messages.error(self.request, self.get_error_message())
            return redirect(reverse("update-member"))
        messages.success(self.request, self.get_success_message())

    def get_success_message(self):
        return _("Le profil a correctement été mis à jour.")

    def get_error_message(self):
        return _("Une erreur est survenue.")


class UpdateGitHubToken(UpdateView):
    """Update the GitHub token."""

    form_class = GitHubTokenForm
    template_name = "member/settings/github.html"

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not request.user.profile.is_dev():
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return get_object_or_404(Profile, user=self.request.user)

    def get_form(self, form_class=GitHubTokenForm):
        return form_class()

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            return self.form_valid(form)

        return render(request, self.template_name, {"form": form})

    def form_valid(self, form):
        profile = self.get_object()
        profile.github_token = form.data["github_token"]
        profile.save()
        messages.success(self.request, self.get_success_message())

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("update-github")

    def get_success_message(self):
        return _("Votre token GitHub a été mis à jour.")

    def get_error_message(self):
        return _("Une erreur est survenue.")


@require_POST
@login_required
def remove_github_token(request):
    """Remove the current user token."""

    profile = get_object_or_404(Profile, user=request.user)
    if not profile.is_dev():
        raise PermissionDenied

    profile.github_token = ""
    profile.save()

    messages.success(request, _("Votre token GitHub a été supprimé."))
    return redirect("update-github")


class UpdateAvatarMember(UpdateMember):
    """Update the avatar of a logged in user."""

    form_class = ImageAsAvatarForm

    def get_success_url(self):
        profile = self.get_object()

        return reverse("member-detail", args=[profile.user.username])

    def get_form(self, form_class=ImageAsAvatarForm):
        return form_class(self.request.POST)

    def update_profile(self, profile, form):
        profile.avatar_url = form.data["avatar_url"]

    def get_success_message(self):
        return _("L'avatar a correctement été mis à jour.")


class UpdatePasswordMember(UpdateMember):
    """Password-related user settings."""

    form_class = ChangePasswordForm
    template_name = "member/settings/account.html"

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.user, request.POST)

        if form.is_valid():
            return self.form_valid(form)

        return render(request, self.template_name, {"form": form})

    def get_form(self, form_class=ChangePasswordForm):
        return form_class(self.request.user)

    def update_profile(self, profile, form):
        profile.user.set_password(form.data["password_new"])
        # to avoid being disconnected after changing the password:
        update_session_auth_hash(self.request, profile.user)

    def get_success_message(self):
        return _("Le mot de passe a correctement été mis à jour.")

    def get_success_url(self):
        return reverse("update-password-member")


class UpdateUsernameEmailMember(UpdateMember):
    """Settings related to username and email."""

    form_class = ChangeUserForm
    template_name = "member/settings/user.html"

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.user, request.POST)

        if form.is_valid():
            return self.form_valid(form)

        return render(request, self.template_name, {"form": form})

    def get_form(self, form_class=ChangeUserForm):
        return form_class(self.request.user)

    def update_profile(self, profile, form):
        profile.show_email = "show_email" in form.cleaned_data.get("options")
        new_username = form.cleaned_data.get("username")
        previous_username = form.cleaned_data.get("previous_username")
        new_email = form.cleaned_data.get("email")
        previous_email = form.cleaned_data.get("previous_email")
        if new_username and new_username != previous_username:
            # Add a karma message for the staff
            bot = get_bot_account()
            KarmaNote(
                user=profile.user,
                moderator=bot,
                note=_("{} s'est renommé {}").format(profile.user.username, new_username),
                karma=0,
            ).save()
            # Change the username
            profile.user.username = new_username
            # update skeleton
            profile.username_skeleton = Profile.find_username_skeleton(new_username)
        if new_email and new_email != previous_email:
            profile.user.email = new_email
            # Create an alert for the staff if it's a new provider
            provider = provider = new_email.split("@")[-1].lower()
            if (
                not NewEmailProvider.objects.filter(provider=provider).exists()
                and not User.objects.filter(email__iendswith=f"@{provider}").exclude(pk=profile.user.pk).exists()
            ):
                NewEmailProvider.objects.create(user=profile.user, provider=provider, use=EMAIL_EDIT)

    def get_success_url(self):
        profile = self.get_object()

        return profile.get_absolute_url()
