import uuid
from datetime import datetime, timedelta

from oauth2_provider.models import AccessToken

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User, Group
from django.template.context_processors import csrf
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse, reverse_lazy, resolve, Resolver404, NoReverseMatch
from django.db import transaction
from django.db.models import Q
from django.http import Http404, HttpResponseBadRequest, StreamingHttpResponse
from django.shortcuts import redirect, render, get_object_or_404, render_to_response
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.utils.http import urlunquote
from django.utils.translation import string_concat
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, UpdateView, CreateView, FormView

from zds.forum.models import Topic, TopicRead
from zds.gallery.forms import ImageAsAvatarForm
from zds.gallery.models import UserGallery
from zds.member import NEW_ACCOUNT, EMAIL_EDIT
from zds.member.commons import ProfileCreate, TemporaryReadingOnlySanction, ReadingOnlySanction, \
    DeleteReadingOnlySanction, TemporaryBanSanction, BanSanction, DeleteBanSanction, TokenGenerator
from zds.member.decorator import can_write_and_read_now, LoginRequiredMixin, PermissionRequiredMixin
from zds.member.forms import LoginForm, MiniProfileForm, ProfileForm, RegisterForm, \
    ChangePasswordForm, ChangeUserForm, NewPasswordForm, \
    PromoteMemberForm, KarmaForm, UsernameAndEmailForm, GitHubTokenForm, \
    BannedEmailProviderForm, HatRequestForm
from zds.member.models import Profile, TokenForgotPassword, TokenRegister, KarmaNote, Ban, \
    BannedEmailProvider, NewEmailProvider, set_old_smileys_cookie, remove_old_smileys_cookie
from zds.mp.models import PrivatePost, PrivateTopic
from zds.notification.models import TopicAnswerSubscription, NewPublicationSubscription
from zds.tutorialv2.models.database import PublishedContent, PickListOperation
from zds.utils.models import Comment, CommentVote, Alert, CommentEdit, Hat, HatRequest, get_hat_from_settings, \
    get_hat_to_add
from zds.utils.mps import send_mp
from zds.utils.paginator import ZdSPagingListView
from zds.utils.tokens import generate_token
import logging


class MemberList(ZdSPagingListView):
    """Display the list of registered users."""

    context_object_name = 'members'
    paginate_by = settings.ZDS_APP['member']['members_per_page']
    template_name = 'member/index.html'

    def get_queryset(self):
        self.queryset = Profile.objects.contactable_members()
        return super(MemberList, self).get_queryset()


class MemberDetail(DetailView):
    """Display details about a profile."""

    context_object_name = 'usr'
    model = User
    template_name = 'member/profile.html'

    def get_object(self, queryset=None):
        # Use urlunquote to accept twicely quoted URLs (for instance in MPs
        # sent through emarkdown parser).
        return get_object_or_404(User, username=urlunquote(self.kwargs['user_name']))

    def get_context_data(self, **kwargs):
        context = super(MemberDetail, self).get_context_data(**kwargs)
        usr = context['usr']
        profile = usr.profile
        context['profile'] = profile
        context['topics'] = list(Topic.objects.last_topics_of_a_member(usr, self.request.user))
        followed_query_set = TopicAnswerSubscription.objects.get_objects_followed_by(self.request.user.id)
        followed_topics = list(set(followed_query_set) & set(context['topics']))
        for topic in context['topics']:
            topic.is_followed = topic in followed_topics
        context['articles'] = PublishedContent.objects.last_articles_of_a_member_loaded(usr)
        context['opinions'] = PublishedContent.objects.last_opinions_of_a_member_loaded(usr)
        context['tutorials'] = PublishedContent.objects.last_tutorials_of_a_member_loaded(usr)
        context['topic_read'] = TopicRead.objects.list_read_topic_pk(self.request.user, context['topics'])
        context['subscriber_count'] = NewPublicationSubscription.objects.get_subscriptions(self.object).count()
        if self.request.user.has_perm('member.change_profile'):
            sanctions = list(Ban.objects.filter(user=usr).select_related('moderator'))
            notes = list(KarmaNote.objects.filter(user=usr).select_related('moderator'))
            actions = sanctions + notes
            actions.sort(key=lambda action: action.pubdate)
            actions.reverse()
            context['actions'] = actions
            context['karmaform'] = KarmaForm(profile)
        return context


class UpdateMember(UpdateView):
    """Update a profile."""

    form_class = ProfileForm
    template_name = 'member/settings/profile.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UpdateMember, self).dispatch(*args, **kwargs)

    def get_object(self, queryset=None):
        return get_object_or_404(Profile, user=self.request.user)

    def get_form(self, form_class=ProfileForm):
        profile = self.get_object()
        form = form_class(initial={
            'biography': profile.biography,
            'site': profile.site,
            'avatar_url': profile.avatar_url,
            'show_sign': profile.show_sign,
            'is_hover_enabled': profile.is_hover_enabled,
            'use_old_smileys': profile.use_old_smileys,
            'allow_temp_visual_changes': profile.allow_temp_visual_changes,
            'show_markdown_help': profile.show_markdown_help,
            'email_for_answer': profile.email_for_answer,
            'sign': profile.sign,
            'licence': profile.licence,
        })

        return form

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if 'preview' in request.POST and request.is_ajax():
            content = render_to_response('misc/preview.part.html', {'text': request.POST.get('text')})
            return StreamingHttpResponse(content)

        if form.is_valid():
            return self.form_valid(form)

        return render(request, self.template_name, {'form': form})

    def form_valid(self, form):
        profile = self.get_object()
        self.update_profile(profile, form)
        self.save_profile(profile)

        response = redirect(self.get_success_url())
        set_old_smileys_cookie(response, profile)
        return response

    def update_profile(self, profile, form):
        cleaned_data_options = form.cleaned_data.get('options')
        profile.biography = form.data['biography']
        profile.site = form.data['site']
        profile.show_sign = 'show_sign' in cleaned_data_options
        profile.is_hover_enabled = 'is_hover_enabled' in cleaned_data_options
        profile.use_old_smileys = 'use_old_smileys' in cleaned_data_options
        profile.allow_temp_visual_changes = 'allow_temp_visual_changes' in cleaned_data_options
        profile.show_markdown_help = 'show_markdown_help' in cleaned_data_options
        profile.email_for_answer = 'email_for_answer' in cleaned_data_options
        profile.avatar_url = form.data['avatar_url']
        profile.sign = form.data['sign']
        profile.licence = form.cleaned_data['licence']

    def get_success_url(self):
        return reverse('update-member')

    def save_profile(self, profile):
        try:
            profile.save()
            profile.user.save()
        except Profile.DoesNotExist:
            messages.error(self.request, self.get_error_message())
            return redirect(reverse('update-member'))
        messages.success(self.request, self.get_success_message())

    def get_success_message(self):
        return _('Le profil a correctement été mis à jour.')

    def get_error_message(self):
        return _('Une erreur est survenue.')


class UpdateGitHubToken(UpdateView):
    """Update the GitHub token."""

    form_class = GitHubTokenForm
    template_name = 'member/settings/github.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not request.user.profile.is_dev():
            raise PermissionDenied
        return super(UpdateGitHubToken, self).dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return get_object_or_404(Profile, user=self.request.user)

    def get_form(self, form_class=GitHubTokenForm):
        return form_class()

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            return self.form_valid(form)

        return render(request, self.template_name, {'form': form})

    def form_valid(self, form):
        profile = self.get_object()
        profile.github_token = form.data['github_token']
        profile.save()
        messages.success(self.request, self.get_success_message())

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('update-github')

    def get_success_message(self):
        return _('Votre token GitHub a été mis à jour.')

    def get_error_message(self):
        return _('Une erreur est survenue.')


@require_POST
@login_required
def remove_github_token(request):
    """Remove the current user token."""

    profile = get_object_or_404(Profile, user=request.user)
    if not profile.is_dev():
        raise PermissionDenied

    profile.github_token = ''
    profile.save()

    messages.success(request, _('Votre token GitHub a été supprimé.'))
    return redirect('update-github')


class UpdateAvatarMember(UpdateMember):
    """Update the avatar of a logged in user."""

    form_class = ImageAsAvatarForm

    def get_success_url(self):
        profile = self.get_object()

        return reverse('member-detail', args=[profile.user.username])

    def get_form(self, form_class=ImageAsAvatarForm):
        return form_class(self.request.POST)

    def update_profile(self, profile, form):
        profile.avatar_url = form.data['avatar_url']

    def get_success_message(self):
        return _('L\'avatar a correctement été mis à jour.')


class UpdatePasswordMember(UpdateMember):
    """Password-related user settings."""

    form_class = ChangePasswordForm
    template_name = 'member/settings/account.html'

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.user, request.POST)

        if form.is_valid():
            return self.form_valid(form)

        return render(request, self.template_name, {'form': form})

    def get_form(self, form_class=ChangePasswordForm):
        return form_class(self.request.user)

    def update_profile(self, profile, form):
        profile.user.set_password(form.data['password_new'])

    def get_success_message(self):
        return _('Le mot de passe a correctement été mis à jour.')

    def get_success_url(self):
        return reverse('update-password-member')


class UpdateUsernameEmailMember(UpdateMember):
    """Settings related to username and email."""

    form_class = ChangeUserForm
    template_name = 'member/settings/user.html'

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.user, request.POST)

        if form.is_valid():
            return self.form_valid(form)

        return render(request, self.template_name, {'form': form})

    def get_form(self, form_class=ChangeUserForm):
        return form_class(self.request.user)

    def update_profile(self, profile, form):
        profile.show_email = 'show_email' in form.cleaned_data.get('options')
        new_username = form.cleaned_data.get('username')
        previous_username = form.cleaned_data.get('previous_username')
        new_email = form.cleaned_data.get('email')
        previous_email = form.cleaned_data.get('previous_email')
        if new_username and new_username != previous_username:
            # Add a karma message for the staff
            bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
            KarmaNote(user=profile.user,
                      moderator=bot,
                      note=_("{} s'est renommé {}").format(profile.user.username, new_username),
                      karma=0).save()
            # Change the username
            profile.user.username = new_username
        if new_email and new_email != previous_email:
            profile.user.email = new_email
            # Create an alert for the staff if it's a new provider
            provider = provider = new_email.split('@')[-1].lower()
            if not NewEmailProvider.objects.filter(provider=provider).exists() \
                    and not User.objects.filter(email__iendswith='@{}'.format(provider)) \
                    .exclude(pk=profile.user.pk).exists():
                NewEmailProvider.objects.create(user=profile.user, provider=provider, use=EMAIL_EDIT)

    def get_success_url(self):
        profile = self.get_object()

        return profile.get_absolute_url()


class RegisterView(CreateView, ProfileCreate, TokenGenerator):
    """Create a profile."""

    form_class = RegisterForm
    template_name = 'member/register/index.html'

    def dispatch(self, *args, **kwargs):
        return super(RegisterView, self).dispatch(*args, **kwargs)

    def get_object(self, queryset=None):
        return get_object_or_404(Profile, user=self.request.user)

    def get_form(self, form_class=RegisterForm):
        return form_class()

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            return self.form_valid(form)
        return render(request, self.template_name, {'form': form})

    def form_valid(self, form):
        profile = self.create_profile(form.data)
        profile.last_ip_address = get_client_ip(self.request)
        self.save_profile(profile)
        token = self.generate_token(profile.user)
        self.send_email(token, profile.user)

        return render(self.request, self.get_success_template())

    def get_success_template(self):
        return 'member/register/success.html'


class SendValidationEmailView(FormView, TokenGenerator):
    """Send a validation email on demand."""

    form_class = UsernameAndEmailForm
    template_name = 'member/register/send_validation_email.html'

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
            self.get_user(form.data['username'], form.data['email'])

            # User should not already be active
            if not self.usr.is_active:
                return self.form_valid(form)
            else:
                if form.data['username']:
                    form.errors['username'] = form.error_class([self.get_error_message()])
                else:
                    form.errors['email'] = form.error_class([self.get_error_message()])

        return render(request, self.template_name, {'form': form})

    def form_valid(self, form):
        # Delete old token
        token = TokenRegister.objects.filter(user=self.usr)
        if token.count() >= 1:
            token.all().delete()

        # Generate new token and send email
        token = self.generate_token(self.usr)
        self.send_email(token, self.usr)

        return render(self.request, self.get_success_template())

    def get_success_template(self):
        return 'member/register/send_validation_email_success.html'

    def get_error_message(self):
        return _('Le compte est déjà activé.')


@login_required
def warning_unregister(request):
    """
    Display a warning page showing what will happen when the user
    unregisters.
    """
    return render(request, 'member/settings/unregister.html', {'user': request.user})


@login_required
@require_POST
@transaction.atomic
def unregister(request):
    """Allow members to unregister."""

    anonymous = get_object_or_404(User, username=settings.ZDS_APP['member']['anonymous_account'])
    external = get_object_or_404(User, username=settings.ZDS_APP['member']['external_account'])
    current = request.user
    # Nota : as of v21 all about content paternity is held by a proper receiver in zds.tutorialv2.models.database
    PickListOperation.objects.filter(staff_user=current).update(staff_user=anonymous)
    PickListOperation.objects.filter(canceler_user=current).update(canceler_user=anonymous)
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
    for topic in PrivateTopic.objects.filter(author=current):
        topic.participants.remove(current)
        if topic.participants.count() > 0:
            topic.author = topic.participants.first()
            topic.participants.remove(topic.author)
            topic.save()
        else:
            topic.delete()
    for topic in PrivateTopic.objects.filter(participants__in=[current]):
        topic.participants.remove(current)
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
            anonymous_gallery.mode = 'w'
            anonymous_gallery.gallery = gallery.gallery
            anonymous_gallery.save()
    galleries.delete()

    # Remove API access (tokens + applications)
    for token in AccessToken.objects.filter(user=current):
        token.revoke()

    logout(request)
    User.objects.filter(pk=current.pk).delete()
    return redirect(reverse('homepage'))


@require_POST
@can_write_and_read_now
@login_required
@permission_required('member.change_profile', raise_exception=True)
@transaction.atomic
def modify_profile(request, user_pk):
    """Modify the sanction of a user if there is a POST request."""

    profile = get_object_or_404(Profile, user__pk=user_pk)
    if profile.is_private():
        raise PermissionDenied
    if request.user.profile == profile:
        messages.error(request, _('Vous ne pouvez pas vous sanctionner vous-même !'))
        raise PermissionDenied

    if 'ls' in request.POST:
        state = ReadingOnlySanction(request.POST)
    elif 'ls-temp' in request.POST:
        state = TemporaryReadingOnlySanction(request.POST)
    elif 'ban' in request.POST:
        state = BanSanction(request.POST)
    elif 'ban-temp' in request.POST:
        state = TemporaryBanSanction(request.POST)
    elif 'un-ls' in request.POST:
        state = DeleteReadingOnlySanction(request.POST)
    else:
        # un-ban
        state = DeleteBanSanction(request.POST)

    try:
        ban = state.get_sanction(request.user, profile.user)
    except ValueError:
        raise HttpResponseBadRequest

    state.apply_sanction(profile, ban)

    if 'un-ls' in request.POST or 'un-ban' in request.POST:
        msg = state.get_message_unsanction()
    else:
        msg = state.get_message_sanction()

    msg = msg.format(ban.user,
                     ban.moderator,
                     ban.type,
                     state.get_detail(),
                     ban.note,
                     settings.ZDS_APP['site']['literal_name'])

    state.notify_member(ban, msg)
    return redirect(profile.get_absolute_url())


# Settings for public profile

@can_write_and_read_now
@login_required
@permission_required('member.change_profile', raise_exception=True)
def settings_mini_profile(request, user_name):
    """Minimal settings of users for staff."""

    # Extra information about the current user
    profile = get_object_or_404(Profile, user__username=user_name)
    if request.method == 'POST':
        form = MiniProfileForm(request.POST)
        data = {'form': form, 'profile': profile}
        if form.is_valid():
            profile.biography = form.data['biography']
            profile.site = form.data['site']
            profile.avatar_url = form.data['avatar_url']
            profile.sign = form.data['sign']

            # Save profile and redirect user to the settings page
            # with a message indicating the operation state.

            try:
                profile.save()
            except:
                messages.error(request, _('Une erreur est survenue.'))
                return redirect(reverse('member-settings-mini-profile'))

            messages.success(request, _('Le profil a correctement été mis à jour.'))
            return redirect(reverse('member-detail', args=[profile.user.username]))
        else:
            return render(request, 'member/settings/profile.html', data)
    else:
        form = MiniProfileForm(initial={
            'biography': profile.biography,
            'site': profile.site,
            'avatar_url': profile.avatar_url,
            'sign': profile.sign,
        })
        data = {'form': form, 'profile': profile}
        messages.warning(request, _(
            'Le profil que vous éditez n\'est pas le vôtre. '
            'Soyez encore plus prudent lors de l\'édition de celui-ci !'))
        return render(request, 'member/settings/profile.html', data)


class NewEmailProvidersList(LoginRequiredMixin, PermissionRequiredMixin, ZdSPagingListView):
    permissions = ['member.change_bannedemailprovider']
    paginate_by = settings.ZDS_APP['member']['providers_per_page']

    model = NewEmailProvider
    context_object_name = 'providers'
    template_name = 'member/settings/new_email_providers.html'
    queryset = NewEmailProvider.objects \
        .select_related('user') \
        .select_related('user__profile') \
        .order_by('-date')


@require_POST
@login_required
@permission_required('member.change_bannedemailprovider', raise_exception=True)
def check_new_email_provider(request, provider_pk):
    """Remove an alert about a new provider."""

    provider = get_object_or_404(NewEmailProvider, pk=provider_pk)
    if 'ban' in request.POST \
            and not BannedEmailProvider.objects.filter(provider=provider.provider).exists():
        BannedEmailProvider.objects.create(provider=provider.provider, moderator=request.user)
    provider.delete()

    messages.success(request, _('Action effectuée.'))
    return redirect('new-email-providers')


class BannedEmailProvidersList(LoginRequiredMixin, PermissionRequiredMixin, ZdSPagingListView):
    """List the banned email providers."""

    permissions = ['member.change_bannedemailprovider']
    paginate_by = settings.ZDS_APP['member']['providers_per_page']

    model = BannedEmailProvider
    context_object_name = 'providers'
    template_name = 'member/settings/banned_email_providers.html'
    queryset = BannedEmailProvider.objects \
        .select_related('moderator') \
        .select_related('moderator__profile') \
        .order_by('-date')


class MembersWithProviderList(LoginRequiredMixin, PermissionRequiredMixin, ZdSPagingListView):
    """List users using a banned email provider."""

    permissions = ['member.change_bannedemailprovider']
    paginate_by = settings.ZDS_APP['member']['members_per_page']

    model = User
    context_object_name = 'members'
    template_name = 'member/settings/members_with_provider.html'

    def get_object(self):
        return get_object_or_404(BannedEmailProvider, pk=self.kwargs['provider_pk'])

    def get_context_data(self, **kwargs):
        context = super(MembersWithProviderList, self).get_context_data(**kwargs)
        context['provider'] = self.get_object()
        return context

    def get_queryset(self):
        provider = self.get_object()
        return Profile.objects \
            .select_related('user') \
            .order_by('-last_visit') \
            .filter(user__email__icontains='@{}'.format(provider.provider))


class AddBannedEmailProvider(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Add an email provider to the banned list."""

    permissions = ['member.change_bannedemailprovider']

    model = BannedEmailProvider
    template_name = 'member/settings/add_banned_email_provider.html'
    form_class = BannedEmailProviderForm
    success_url = reverse_lazy('banned-email-providers')

    def form_valid(self, form):
        form.instance.moderator = self.request.user
        messages.success(self.request, _('Le fournisseur a été banni.'))
        return super(AddBannedEmailProvider, self).form_valid(form)


@require_POST
@login_required
@permission_required('member.change_bannedemailprovider', raise_exception=True)
def remove_banned_email_provider(request, provider_pk):
    """Unban an email provider."""

    provider = get_object_or_404(BannedEmailProvider, pk=provider_pk)
    provider.delete()

    messages.success(request, _('Le fournisseur « {} » a été débanni.').format(provider.provider))
    return redirect('banned-email-providers')


class HatsList(ZdSPagingListView):
    """Display the list of hats."""

    context_object_name = 'hats'
    paginate_by = settings.ZDS_APP['member']['hats_per_page']
    template_name = 'member/hats.html'
    queryset = Hat.objects \
                  .order_by('name') \
                  .select_related('group') \
                  .prefetch_related('group__user_set') \
                  .prefetch_related('group__user_set__profile') \
                  .prefetch_related('profile_set') \
                  .prefetch_related('profile_set__user')


class HatDetail(DetailView):
    model = Hat
    context_object_name = 'hat'
    template_name = 'member/hat.html'

    def get_context_data(self, **kwargs):
        context = super(HatDetail, self).get_context_data(**kwargs)
        hat = context['hat']
        if self.request.user.is_authenticated:
            context['is_required'] = HatRequest.objects \
                .filter(user=self.request.user, hat__iexact=hat.name, is_granted__isnull=True).exists()
        if hat.group:
            context['users'] = hat.group.user_set.select_related('profile')
        else:
            context['users'] = [p.user for p in hat.profile_set.select_related('user')]
        return context


class HatsSettings(LoginRequiredMixin, CreateView):
    model = HatRequest
    template_name = 'member/settings/hats.html'
    form_class = HatRequestForm

    def get_initial(self):
        initial = super(HatsSettings, self).get_initial()
        if 'ask' in self.request.GET:
            try:
                hat = Hat.objects.get(pk=int(self.request.GET['ask']))
                initial['hat'] = hat.name
            except (ValueError, Hat.DoesNotExist):
                pass
        return initial

    def post(self, request, *args, **kwargs):
        if 'preview' in request.POST and request.is_ajax():
            content = render_to_response('misc/preview.part.html', {'text': request.POST.get('text')})
            return StreamingHttpResponse(content)

        return super(HatsSettings, self).post(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, _('Votre demande a bien été envoyée.'))
        return super(HatsSettings, self).form_valid(form)

    def get_success_url(self):
        # To remove #send-request HTML-anchor.
        return '{}#'.format(reverse('hats-settings'))


class RequestedHatsList(LoginRequiredMixin, PermissionRequiredMixin, ZdSPagingListView):
    permissions = ['utils.change_hat']
    paginate_by = settings.ZDS_APP['member']['requested_hats_per_page']

    model = HatRequest
    context_object_name = 'requests'
    template_name = 'member/settings/requested_hats.html'
    queryset = HatRequest.objects \
        .filter(is_granted__isnull=True) \
        .select_related('user') \
        .select_related('user__profile') \
        .order_by('-date')


class SolvedHatRequestsList(LoginRequiredMixin, PermissionRequiredMixin, ZdSPagingListView):
    permissions = ['utils.change_hat']
    paginate_by = settings.ZDS_APP['member']['requested_hats_per_page']

    model = HatRequest
    context_object_name = 'requests'
    template_name = 'member/settings/solved_hat_requests.html'
    queryset = (HatRequest.objects
                .filter(is_granted__isnull=False)
                .select_related('user')
                .select_related('user__profile')
                .select_related('moderator')
                .select_related('moderator__profile')
                .order_by('-solved_at'))


class HatRequestDetail(LoginRequiredMixin, DetailView):
    model = HatRequest
    context_object_name = 'hat_request'
    template_name = 'member/settings/hat_request.html'

    def get_object(self, queryset=None):
        request = super(HatRequestDetail, self).get_object()
        if request.user != self.request.user \
                and not self.request.user.has_perm('utils.change_hat'):
            raise PermissionDenied
        return request


@require_POST
@login_required
@permission_required('utils.change_hat', raise_exception=True)
@transaction.atomic
def solve_hat_request(request, request_pk):
    """
    Solve a hat request by granting or denying the requested hat
    according to moderator's decision.
    """

    hat_request = get_object_or_404(HatRequest, pk=request_pk)

    if hat_request.is_granted is not None:
        raise PermissionDenied

    try:
        hat_request.solve('grant' in request.POST, request.user,
                          request.POST.get('comment', ''), request.POST.get('hat', None))
        messages.success(request, _('La demande a été résolue.'))
        return redirect('requested-hats')
    except ValueError as e:
        messages.error(request, str(e))
        return redirect(hat_request.get_absolute_url())


@require_POST
@login_required
@permission_required('utils.change_hat', raise_exception=True)
@transaction.atomic
def add_hat(request, user_pk):
    """
    Add a hat to a user.
    Creates the hat if it doesn't exist.
    """

    user = get_object_or_404(User, pk=user_pk)

    hat_name = request.POST.get('hat', '')

    try:
        hat = get_hat_to_add(hat_name, user)
        user.profile.hats.add(hat)
        try:  # if hat was requested, remove the relevant request
            hat_request = HatRequest.objects.get(user=user, hat__iexact=hat.name, is_granted__isnull=True)
            hat_request.solve(is_granted=False,
                              comment=_('La demande a été automatiquement annulée car '
                                        'la casquette vous a été accordée manuellement.'))
        except HatRequest.DoesNotExist:
            pass
        messages.success(request, _('La casquette a bien été ajoutée.'))
    except ValueError as e:
        messages.error(request, str(e))

    return redirect(user.profile.get_absolute_url())


@require_POST
@login_required
@transaction.atomic
def remove_hat(request, user_pk, hat_pk):
    """Remove a hat from a user."""

    user = get_object_or_404(User, pk=user_pk)
    hat = get_object_or_404(Hat, pk=hat_pk)
    if user != request.user and not request.user.has_perm('utils.change_hat'):
        raise PermissionDenied
    if hat not in user.profile.hats.all():
        raise Http404

    user.profile.hats.remove(hat)

    messages.success(request, _('La casquette a bien été retirée.'))
    return redirect(user.profile.get_absolute_url())


def login_view(request):
    """Logs user in."""
    next_page = request.GET.get('next', '/')
    csrf_tk = {'next_page': next_page}
    csrf_tk.update(csrf(request))
    error = False

    if request.method != 'POST':
        form = LoginForm()
    else:
        form = LoginForm(request.POST)
    if form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(username=username, password=password)
        if user is None:
            initial = {'username': username}
            if User.objects.filter(username=username).exists():
                messages.error(
                    request, _(
                        'Le mot de passe saisi est incorrect. '
                        'Cliquez sur le lien « Mot de passe oublié ? » '
                        'si vous ne vous en souvenez plus.'
                    )
                )
            else:
                messages.error(
                    request, _(
                        'Ce nom d’utilisateur est inconnu. '
                        'Si vous ne possédez pas de compte, '
                        'vous pouvez vous inscrire.'
                    )
                )
            form = LoginForm(initial=initial)
            if next_page is not None:
                form.helper.form_action += '?next=' + next_page
            csrf_tk['error'] = error
            csrf_tk['form'] = form
            return render(request, 'member/login.html', {
                'form': form,
                'csrf_tk': csrf_tk
            })
        profile = get_object_or_404(Profile, user=user)
        if not user.is_active:
            messages.error(
                request,
                _(
                    'Vous n\'avez pas encore activé votre compte, '
                    'vous devez le faire pour pouvoir vous '
                    'connecter sur le site. Regardez dans vos '
                    'mails : {}.'
                ).format(user.email)
            )
        elif not profile.can_read_now():
            messages.error(
                request,
                _(
                    'Vous n\'êtes pas autorisé à vous connecter '
                    'sur le site, vous avez été banni par un '
                    'modérateur.'
                )
            )
        else:
            login(request, user)
            request.session['get_token'] = generate_token()
            if 'remember' not in request.POST:
                request.session.set_expiry(0)
            profile.last_ip_address = get_client_ip(request)
            profile.save()
            # Redirect the user if needed.
            # Set the cookie for Clem smileys.
            # (For people switching account or clearing cookies
            # after a browser session.)
            try:
                response = redirect(resolve(next_page).url_name)
            except NoReverseMatch:
                response = redirect(next_page)
            except Resolver404:
                response = redirect(reverse('homepage'))
            set_old_smileys_cookie(response, profile)
            return response

    if next_page is not None:
        form.helper.form_action += '?next=' + next_page
    csrf_tk['error'] = error
    csrf_tk['form'] = form
    return render(request, 'member/login.html', {
        'form': form,
        'csrf_tk': csrf_tk
    })


@login_required
@require_POST
def logout_view(request):
    """Log user out."""

    logout(request)
    request.session.clear()
    response = redirect(reverse('homepage'))
    # disable Clem smileys:
    remove_old_smileys_cookie(response)
    return response


def forgot_password(request):
    """If the user has forgotten his password, they can get a new one."""

    if request.method == 'POST':
        form = UsernameAndEmailForm(request.POST)
        if form.is_valid():

            # Get data from form
            data = form.data
            username = data['username']
            email = data['email']

            # Fetch the user, we need his email address
            usr = None
            if username:
                usr = get_object_or_404(User, Q(username=username))

            if email:
                usr = get_object_or_404(User, Q(email=email))

            # Generate a valid token during one hour
            uuid_token = str(uuid.uuid4())
            date_end = datetime.now() + timedelta(days=0, hours=1, minutes=0,
                                                  seconds=0)
            token = TokenForgotPassword(user=usr, token=uuid_token,
                                        date_end=date_end)
            token.save()

            # Send email
            subject = _('{} - Mot de passe oublié').format(settings.ZDS_APP['site']['literal_name'])
            from_email = '{} <{}>'.format(settings.ZDS_APP['site']['literal_name'],
                                          settings.ZDS_APP['site']['email_noreply'])
            context = {
                'username': usr.username,
                'site_name': settings.ZDS_APP['site']['literal_name'],
                'site_url': settings.ZDS_APP['site']['url'],
                'url': settings.ZDS_APP['site']['url'] + token.get_absolute_url()
            }
            message_html = render_to_string('email/member/confirm_forgot_password.html', context)
            message_txt = render_to_string('email/member/confirm_forgot_password.txt', context)

            msg = EmailMultiAlternatives(subject, message_txt, from_email, [usr.email])
            msg.attach_alternative(message_html, 'text/html')
            msg.send()
            return render(request, 'member/forgot_password/success.html')
        else:
            return render(request, 'member/forgot_password/index.html',
                          {'form': form})
    form = UsernameAndEmailForm()
    return render(request, 'member/forgot_password/index.html', {'form': form})


def new_password(request):
    """Create a new password for a user."""

    try:
        token = request.GET['token']
    except KeyError:
        return redirect(reverse('homepage'))
    token = get_object_or_404(TokenForgotPassword, token=token)
    if request.method == 'POST':
        form = NewPasswordForm(token.user.username, request.POST)
        if form.is_valid():
            data = form.data
            password = data['password']
            # User can't confirm his request if it is too late

            if datetime.now() > token.date_end:
                return render(request, 'member/new_password/failed.html')
            token.user.set_password(password)
            token.user.save()
            token.delete()
            return render(request, 'member/new_password/success.html')
        else:
            return render(request, 'member/new_password/index.html', {'form': form})
    form = NewPasswordForm(identifier=token.user.username)
    return render(request, 'member/new_password/index.html', {'form': form})


def activate_account(request):
    """Activate an account with a token."""
    try:
        token = request.GET['token']
    except KeyError:
        return redirect(reverse('homepage'))
    token = get_object_or_404(TokenRegister, token=token)
    usr = token.user

    # User can't confirm their request if their account is already active
    if usr.is_active:
        return render(request, 'member/register/token_already_used.html')

    # User can't confirm their request if it is too late
    if datetime.now() > token.date_end:
        return render(request, 'member/register/token_failed.html',
                      {'token': token})
    usr.is_active = True
    usr.save()

    # Send welcome message
    bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
    msg = render_to_string(
        'member/messages/account_activated.md',
        {
            'username': usr.username,
            'site_name': settings.ZDS_APP['site']['literal_name'],
            'library_url': settings.ZDS_APP['site']['url'] + reverse('publication:list'),
            'opinions_url': settings.ZDS_APP['site']['url'] + reverse('opinion:list'),
            'forums_url': settings.ZDS_APP['site']['url'] + reverse('cats-forums-list')
        }
    )

    send_mp(bot,
            [usr],
            _('Bienvenue sur {}').format(settings.ZDS_APP['site']['literal_name']),
            _('Le manuel du nouveau membre'),
            msg,
            False,
            True,
            False,
            hat=get_hat_from_settings('moderation'))
    token.delete()

    # Create an alert for the staff if it's a new provider
    if usr.email:
        provider = usr.email.split('@')[-1].lower()
        if not NewEmailProvider.objects.filter(provider=provider).exists() \
                and not User.objects.filter(email__iendswith='@{}'.format(provider)) \
                .exclude(pk=usr.pk).exists():
            NewEmailProvider.objects.create(user=usr, provider=provider, use=NEW_ACCOUNT)

    form = LoginForm(initial={'username': usr.username})
    return render(request, 'member/register/token_success.html', {'usr': usr, 'form': form})


def generate_token_account(request):
    """Generate a token for an account."""

    try:
        token = request.GET['token']
    except KeyError:
        return redirect(reverse('homepage'))
    token = get_object_or_404(TokenRegister, token=token)

    # Push date

    date_end = datetime.now() + timedelta(days=0, hours=1, minutes=0,
                                          seconds=0)
    token.date_end = date_end
    token.save()

    # Send email
    subject = _("{} - Confirmation d'inscription").format(settings.ZDS_APP['site']['literal_name'])
    from_email = '{} <{}>'.format(settings.ZDS_APP['site']['literal_name'],
                                  settings.ZDS_APP['site']['email_noreply'])
    context = {
        'username': token.user.username,
        'site_url': settings.ZDS_APP['site']['url'],
        'site_name': settings.ZDS_APP['site']['literal_name'],
        'url': settings.ZDS_APP['site']['url'] + token.get_absolute_url()
    }
    message_html = render_to_string('email/member/confirm_registration.html', context)
    message_txt = render_to_string('email/member/confirm_registration.txt', context)

    msg = EmailMultiAlternatives(subject, message_txt, from_email, [token.user.email])
    msg.attach_alternative(message_html, 'text/html')
    try:
        msg.send()
    except:
        msg = None
    return render(request, 'member/register/success.html', {})


def get_client_ip(request):
    """Retrieve the real IP address of the client."""

    if 'HTTP_X_REAL_IP' in request.META:  # nginx
        return request.META.get('HTTP_X_REAL_IP')
    elif 'REMOTE_ADDR' in request.META:
        # other
        return request.META.get('REMOTE_ADDR')
    else:
        # Should never happen
        return '0.0.0.0'


@login_required
def settings_promote(request, user_pk):
    """
    Manage groups and activation status of a user.
    Only superusers are allowed to use this.
    """

    if not request.user.is_superuser:
        raise PermissionDenied

    profile = get_object_or_404(Profile, user__pk=user_pk)
    user = profile.user

    if request.method == 'POST':
        form = PromoteMemberForm(request.POST)
        data = dict(form.data)

        groups = Group.objects.all()
        usergroups = user.groups.all()

        if 'groups' in data:
            for group in groups:
                if str(group.id) in data['groups']:
                    if group not in usergroups:
                        user.groups.add(group)
                        messages.success(request, _('{0} appartient maintenant au groupe {1}.')
                                         .format(user.username, group.name))
                else:
                    if group in usergroups:
                        user.groups.remove(group)
                        messages.warning(request, _('{0} n\'appartient maintenant plus au groupe {1}.')
                                         .format(user.username, group.name))
                        topics_followed = TopicAnswerSubscription.objects.get_objects_followed_by(user)
                        for topic in topics_followed:
                            if isinstance(topic, Topic) and group in topic.forum.groups.all():
                                TopicAnswerSubscription.objects.toggle_follow(topic, user)
        else:
            for group in usergroups:
                topics_followed = TopicAnswerSubscription.objects.get_objects_followed_by(user)
                for topic in topics_followed:
                    if isinstance(topic, Topic) and group in topic.forum.groups.all():
                        TopicAnswerSubscription.objects.toggle_follow(topic, user)
            user.groups.clear()
            messages.warning(request, _('{0} n\'appartient (plus ?) à aucun groupe.')
                             .format(user.username))

        if 'activation' in data and 'on' in data['activation']:
            user.is_active = True
            messages.success(request, _('{0} est maintenant activé.')
                             .format(user.username))
        else:
            user.is_active = False
            messages.warning(request, _('{0} est désactivé.')
                             .format(user.username))

        user.save()

        usergroups = user.groups.all()
        bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
        msg = _('Bonjour {0},\n\n'
                'Un administrateur vient de modifier les groupes '
                'auxquels vous appartenez.  \n').format(user.username)
        if len(usergroups) > 0:
            msg = string_concat(msg, _('Voici la liste des groupes dont vous faites dorénavant partie :\n\n'))
            for group in usergroups:
                msg += '* {0}\n'.format(group.name)
        else:
            msg = string_concat(msg, _('* Vous ne faites partie d\'aucun groupe'))
        send_mp(
            bot,
            [user],
            _('Modification des groupes'),
            '',
            msg,
            True,
            True,
            hat=get_hat_from_settings('moderation'),
        )

        return redirect(profile.get_absolute_url())

    form = PromoteMemberForm(initial={
        'groups': user.groups.all(),
        'activation': user.is_active
    })
    return render(request, 'member/settings/promote.html', {
        'usr': user,
        'profile': profile,
        'form': form
    })


@login_required
@permission_required('member.change_profile', raise_exception=True)
def member_from_ip(request, ip_address):
    """List users connected from a particular IP."""

    members = Profile.objects.filter(last_ip_address=ip_address).order_by('-last_visit')
    return render(request, 'member/settings/memberip.html', {
        'members': members,
        'ip': ip_address
    })


@login_required
@permission_required('member.change_profile', raise_exception=True)
@require_POST
def modify_karma(request):
    """Add a Karma note to a user profile."""

    try:
        profile_pk = int(request.POST['profile_pk'])
    except (KeyError, ValueError):
        raise Http404

    profile = get_object_or_404(Profile, pk=profile_pk)
    if profile.is_private():
        raise PermissionDenied

    note = KarmaNote(
        user=profile.user,
        moderator=request.user,
        note=request.POST.get('note', '').strip())

    try:
        note.karma = int(request.POST['karma'])
    except (KeyError, ValueError):
        note.karma = 0

    try:
        if not note.note:
            raise ValueError('note cannot be empty')
        elif note.karma > 100 or note.karma < -100:
            raise ValueError('Max karma amount has to be between -100 and 100, you entered {}'.format(note.karma))
        else:
            note.save()
            profile.karma += note.karma
            profile.save()
    except ValueError as e:
        logging.getLogger(__name__).warn('ValueError: modifying karma failed because {}'.format(e))

    return redirect(reverse('member-detail', args=[profile.user.username]))
