import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, FormView
from oauth2_provider.models import AccessToken

from zds.forum.models import Topic
from zds.gallery.models import GALLERY_WRITE, UserGallery
from zds.member import NEW_ACCOUNT
from zds.member.commons import ProfileCreate, TokenGenerator
from zds.member.forms import LoginForm, RegisterForm, UnregisterForm, UsernameAndEmailForm
from zds.member.models import Ban, BannedEmailProvider, KarmaNote, NewEmailProvider, Profile, TokenRegister
from zds.member.utils import get_anonymous_account, get_bot_account, get_external_account
from zds.member.views import get_client_ip
from zds.mp.models import PrivatePost, PrivateTopic
from zds.mp.utils import send_mp
from zds.tutorialv2.models.database import PickListOperation
from zds.tutorialv2.models.events import Event
from zds.utils.models import Alert, Comment, CommentEdit, CommentVote, HatRequest, get_hat_from_settings


class RegisterView(CreateView, ProfileCreate, TokenGenerator):
    """Create a profile."""

    form_class = RegisterForm
    template_name = "member/register/index.html"

    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_object(self, queryset=None):
        return get_object_or_404(Profile, user=self.request.user)

    def get_form(self, form_class=RegisterForm):
        return form_class()

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            return self.form_valid(form)
        return render(request, self.template_name, {"form": form})

    def form_valid(self, form):
        profile = self.create_profile(form.data)
        profile.last_ip_address = get_client_ip(self.request)
        profile.username_skeleton = Profile.find_username_skeleton(profile.user.username)
        self.save_profile(profile)
        token = self.generate_token(profile.user)
        try:
            self.send_email(token, profile.user)
        except Exception as e:
            logging.getLogger(__name__).warning("Mail not sent", exc_info=e)
            messages.warning(self.request, _("Impossible d'envoyer l'email."))
            self.object = None
            return self.form_invalid(form)
        return render(self.request, self.get_success_template())

    def get_success_template(self):
        return "member/register/success.html"


class SendValidationEmailView(FormView, TokenGenerator):
    """Send a validation email on demand."""

    form_class = UsernameAndEmailForm
    template_name = "member/register/send_validation_email.html"

    usr = None

    def get_user(self, username, email):
        if username:
            self.usr = get_object_or_404(User, username=username)

        elif email:
            self.usr = get_object_or_404(User, email=email)

    def get_form(self, form_class=UsernameAndEmailForm):
        return form_class()

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            # Fetch the user
            self.get_user(form.data["username"], form.data["email"])

            # User should not already be active
            if not self.usr.is_active:
                return self.form_valid(form)
            else:
                if form.data["username"]:
                    form.errors["username"] = form.error_class([self.get_error_message()])
                else:
                    form.errors["email"] = form.error_class([self.get_error_message()])

        return render(request, self.template_name, {"form": form})

    def form_valid(self, form):
        # Delete old token
        token = TokenRegister.objects.filter(user=self.usr)
        if token.count() >= 1:
            token.all().delete()

        # Generate new token and send email
        token = self.generate_token(self.usr)
        try:
            self.send_email(token, self.usr)
        except Exception as e:
            logging.getLogger(__name__).warning("Mail not sent", exc_info=e)
            messages.warning(_("Impossible d'envoyer l'email."))
            return self.form_invalid(form)

        return render(self.request, self.get_success_template())

    def get_success_template(self):
        return "member/register/send_validation_email_success.html"

    def get_error_message(self):
        return _("Le compte est déjà activé.")


@login_required
def warning_unregister(request):
    """
    Display a warning page showing what will happen when the user
    unregisters.
    """
    unregister_form = UnregisterForm(request.user)
    return render(
        request, "member/settings/unregister.html", {"user": request.user, "unregister_form": unregister_form}
    )


@login_required
@require_POST
@transaction.atomic
def unregister(request):
    """Allow members to unregister."""

    unregister_form = UnregisterForm(request.user, data=request.POST)

    if not unregister_form.is_valid():
        for field, errors in unregister_form.errors.items():
            for error in errors:
                messages.error(request, error)
        return render(
            request, "member/settings/unregister.html", {"user": request.user, "unregister_form": unregister_form}
        )

    anonymous = get_anonymous_account()
    external = get_external_account()
    current = request.user
    # Nota : as of v21 all about content paternity is held by a proper receiver in zds.tutorialv2.models.database
    PickListOperation.objects.filter(staff_user=current).update(staff_user=anonymous)
    PickListOperation.objects.filter(canceler_user=current).update(canceler_user=anonymous)

    Event.objects.filter(performer=current).update(performer=external)
    Event.objects.filter(author=current).update(author=external)
    Event.objects.filter(contributor=current).update(contributor=external)

    # Comments likes / dislikes
    votes = CommentVote.objects.filter(user=current)
    for vote in votes:
        if vote.positive:
            vote.comment.like -= 1
        else:
            vote.comment.dislike -= 1
        vote.comment.save()
    votes.delete()
    # All contents anonymization
    Comment.objects.filter(author=current).update(author=anonymous)
    PrivatePost.objects.filter(author=current).update(author=anonymous)
    CommentEdit.objects.filter(editor=current).update(editor=anonymous)
    CommentEdit.objects.filter(deleted_by=current).update(deleted_by=anonymous)
    # Karma notes, alerts and sanctions anonymization (to keep them)
    KarmaNote.objects.filter(moderator=current).update(moderator=anonymous)
    Ban.objects.filter(moderator=current).update(moderator=anonymous)
    Alert.objects.filter(author=current).update(author=anonymous)
    Alert.objects.filter(moderator=current).update(moderator=anonymous)
    BannedEmailProvider.objects.filter(moderator=current).update(moderator=anonymous)
    # Solved hat requests anonymization
    HatRequest.objects.filter(moderator=current).update(moderator=anonymous)
    # In case current user has been moderator in the past
    Comment.objects.filter(editor=current).update(editor=anonymous)
    for topic in PrivateTopic.objects.filter(Q(author=current) | Q(participants__in=[current])):
        if topic.one_participant_remaining():
            topic.delete()
        else:
            topic.remove_participant(current)
            topic.save()
    Topic.objects.filter(solved_by=current).update(solved_by=anonymous)
    Topic.objects.filter(author=current).update(author=anonymous)

    # Any content exclusively owned by the unregistering member will
    # be deleted just before the User object (using a pre_delete
    # receiver).
    #
    # Regarding galleries, there are two cases:
    #
    # - "personal galleries" with one owner (the unregistering
    #   user). The user's ownership is removed and replaced by an
    #   anonymous user in order not to lost the gallery.
    #
    # - "personal galleries" with many other owners. It is safe to
    #   remove the user's ownership, the gallery won't be lost.

    galleries = UserGallery.objects.filter(user=current)
    for gallery in galleries:
        if gallery.gallery.get_linked_users().count() == 1:
            anonymous_gallery = UserGallery()
            anonymous_gallery.user = external
            anonymous_gallery.mode = GALLERY_WRITE
            anonymous_gallery.gallery = gallery.gallery
            anonymous_gallery.save()
    galleries.delete()

    # Remove API access (tokens + applications)
    for token in AccessToken.objects.filter(user=current):
        token.revoke()

    logout(request)
    User.objects.filter(pk=current.pk).delete()
    return redirect(reverse("homepage"))


def activate_account(request):
    """Activate an account with a token."""
    try:
        token = request.GET["token"]
    except KeyError:
        return redirect(reverse("homepage"))
    token = get_object_or_404(TokenRegister, token=token)
    usr = token.user

    # User can't confirm their request if their account is already active
    if usr.is_active:
        return render(request, "member/register/token_already_used.html")

    # User can't confirm their request if it is too late
    if datetime.now() > token.date_end:
        return render(request, "member/register/token_failed.html", {"token": token})
    usr.is_active = True
    usr.save()

    # Send welcome message
    bot = get_bot_account()
    msg = render_to_string(
        "member/messages/account_activated.md",
        {
            "username": usr.username,
            "site_name": settings.ZDS_APP["site"]["literal_name"],
            "library_url": settings.ZDS_APP["site"]["url"] + reverse("publication:list"),
            "opinions_url": settings.ZDS_APP["site"]["url"] + reverse("opinion:list"),
            "forums_url": settings.ZDS_APP["site"]["url"] + reverse("forum:cats-forums-list"),
        },
    )

    send_mp(
        bot,
        [usr],
        _("Bienvenue sur {}").format(settings.ZDS_APP["site"]["literal_name"]),
        _("Le manuel du nouveau membre"),
        msg,
        send_by_mail=False,
        leave=True,
        hat=get_hat_from_settings("moderation"),
    )
    token.delete()

    # Create an alert for the staff if it's a new provider
    if usr.email:
        provider = usr.email.split("@")[-1].lower()
        if (
            not NewEmailProvider.objects.filter(provider=provider).exists()
            and not User.objects.filter(email__iendswith=f"@{provider}").exclude(pk=usr.pk).exists()
        ):
            NewEmailProvider.objects.create(user=usr, provider=provider, use=NEW_ACCOUNT)

    form = LoginForm(initial={"username": usr.username})
    return render(request, "member/register/token_success.html", {"usr": usr, "form": form})


def generate_token_account(request):
    """Generate a token for an account."""

    try:
        token = request.GET["token"]
    except KeyError:
        return redirect(reverse("homepage"))
    token = get_object_or_404(TokenRegister, token=token)

    # Push date

    date_end = datetime.now() + timedelta(days=0, hours=1, minutes=0, seconds=0)
    token.date_end = date_end
    token.save()

    # Send email
    subject = _("{} - Confirmation d'inscription").format(settings.ZDS_APP["site"]["literal_name"])
    from_email = "{} <{}>".format(settings.ZDS_APP["site"]["literal_name"], settings.ZDS_APP["site"]["email_noreply"])
    context = {
        "username": token.user.username,
        "site_url": settings.ZDS_APP["site"]["url"],
        "site_name": settings.ZDS_APP["site"]["literal_name"],
        "url": settings.ZDS_APP["site"]["url"] + token.get_absolute_url(),
    }
    message_html = render_to_string("email/member/confirm_registration.html", context)
    message_txt = render_to_string("email/member/confirm_registration.txt", context)

    msg = EmailMultiAlternatives(subject, message_txt, from_email, [token.user.email])
    msg.attach_alternative(message_html, "text/html")
    try:
        msg.send()
    except:
        msg = None
    return render(request, "member/register/success.html", {})
