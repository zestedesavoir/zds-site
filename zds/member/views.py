# coding: utf-8

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
from django.core.urlresolvers import reverse
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
from zds.member.commons import ProfileCreate, TemporaryReadingOnlySanction, ReadingOnlySanction, \
    DeleteReadingOnlySanction, TemporaryBanSanction, BanSanction, DeleteBanSanction, TokenGenerator
from zds.member.decorator import can_write_and_read_now
from zds.member.forms import LoginForm, MiniProfileForm, ProfileForm, RegisterForm, \
    ChangePasswordForm, ChangeUserForm, NewPasswordForm, \
    PromoteMemberForm, KarmaForm, UsernameAndEmailForm, GitHubTokenForm
from zds.member.models import Profile, TokenForgotPassword, TokenRegister, KarmaNote, Ban
from zds.mp.models import PrivatePost, PrivateTopic
from zds.tutorialv2.models.models_database import PublishableContent
from zds.notification.models import TopicAnswerSubscription, NewPublicationSubscription
from zds.tutorialv2.models.models_database import PublishedContent
from zds.utils.models import Comment, CommentVote, Alert
from zds.utils.mps import send_mp
from zds.utils.paginator import ZdSPagingListView
from zds.utils.tokens import generate_token
import logging


class MemberList(ZdSPagingListView):
    """Displays the list of registered users."""

    context_object_name = 'members'
    paginate_by = settings.ZDS_APP['member']['members_per_page']
    template_name = 'member/index.html'

    def get_queryset(self):
        self.queryset = Profile.objects.contactable_members()
        return super(MemberList, self).get_queryset()


class MemberDetail(DetailView):
    """Displays details about a profile."""

    context_object_name = 'usr'
    model = User
    template_name = 'member/profile.html'

    def get_object(self, queryset=None):
        # Use urlunquote to accept quoted twice URLs (for instance in MPs send
        # through emarkdown parser)
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
    """Updates a profile."""

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
            'allow_temp_visual_changes': profile.allow_temp_visual_changes,
            'email_for_answer': profile.email_for_answer,
            'sign': profile.sign,
            'is_dev': profile.is_dev(),
        })

        return form

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if 'preview' in request.POST and request.is_ajax():
            content = render_to_response('misc/previsualization.part.html', {'text': request.POST.get('text')})
            return StreamingHttpResponse(content)

        if form.is_valid():
            return self.form_valid(form)

        return render(request, self.template_name, {'form': form})

    def form_valid(self, form):
        profile = self.get_object()
        self.update_profile(profile, form)
        self.save_profile(profile)

        return redirect(self.get_success_url())

    def update_profile(self, profile, form):
        cleaned_data_options = form.cleaned_data.get('options')
        profile.biography = form.data['biography']
        profile.site = form.data['site']
        profile.show_sign = 'show_sign' in cleaned_data_options
        profile.is_hover_enabled = 'is_hover_enabled' in cleaned_data_options
        profile.allow_temp_visual_changes = 'allow_temp_visual_changes' in cleaned_data_options
        profile.email_for_answer = 'email_for_answer' in cleaned_data_options
        profile.avatar_url = form.data['avatar_url']
        profile.sign = form.data['sign']

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
        return _(u'Le profil a correctement été mis à jour.')

    def get_error_message(self):
        return _(u'Une erreur est survenue.')


class UpdateGitHubToken(UpdateView):
    """Updates the GitHub token."""

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
        return _(u'Votre token GitHub a été mis à jour.')

    def get_error_message(self):
        return _(u'Une erreur est survenue.')


@require_POST
@login_required
def remove_github_token(request):
    """
    Removes the current user's token
    """

    profile = get_object_or_404(Profile, user=request.user)
    if not profile.is_dev():
        raise PermissionDenied

    profile.github_token = ''
    profile.save()

    messages.success(request, _(u'Votre token GitHub a été supprimé.'))
    return redirect('update-github')


class UpdateAvatarMember(UpdateMember):
    """Update avatar of a user logged."""

    form_class = ImageAsAvatarForm

    def get_success_url(self):
        profile = self.get_object()

        return reverse('member-detail', args=[profile.user.username])

    def get_form(self, form_class=ImageAsAvatarForm):
        return form_class(self.request.POST)

    def update_profile(self, profile, form):
        profile.avatar_url = form.data['avatar_url']

    def get_success_message(self):
        return _(u'L\'avatar a correctement été mis à jour.')


class UpdatePasswordMember(UpdateMember):
    """User's settings about his password."""

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
        return _(u'Le mot de passe a correctement été mis à jour.')

    def get_success_url(self):
        return reverse('update-password-member')


class UpdateUsernameEmailMember(UpdateMember):
    """User's settings about his username and email."""

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
                      note=_(u"{} s'est renommé {}").format(profile.user.username, new_username),
                      karma=0).save()
            # Change the pseudo
            profile.user.username = new_username
        if new_email and new_email != previous_email:
            profile.user.email = new_email

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
    """Send a validation email on demand. """

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

            # User should not be already active
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
        if token.count >= 1:
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
    Displays a warning page showing what will happen when user unregisters.
    """
    return render(request, 'member/settings/unregister.html', {'user': request.user})


@login_required
@require_POST
@transaction.atomic
def unregister(request):
    """allow members to unregister"""

    anonymous = get_object_or_404(User, username=settings.ZDS_APP['member']['anonymous_account'])
    external = get_object_or_404(User, username=settings.ZDS_APP['member']['external_account'])
    current = request.user
    # Nota : as of v21 all about content paternity is held by a proper receiver in zds.tutorialv2.models.models_database
    # comments likes / dislikes
    votes = CommentVote.objects.filter(user=current)
    for vote in votes:
        if vote.positive:
            vote.comment.like -= 1
        else:
            vote.comment.dislike -= 1
        vote.comment.save()
    votes.delete()
    # all messages anonymisation (forum, article and tutorial posts)
    Comment.objects.filter(author=current).update(author=anonymous)
    PrivatePost.objects.filter(author=current).update(author=anonymous)
    # karma notes, alerts and sanctions anonymisation (to keep them)
    KarmaNote.objects.filter(moderator=current).update(moderator=anonymous)
    Ban.objects.filter(moderator=current).update(moderator=anonymous)
    Alert.objects.filter(author=current).update(author=anonymous)
    Alert.objects.filter(moderator=current).update(moderator=anonymous)
    # in case current has been moderator in his old day
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
    Topic.objects.filter(author=current).update(author=anonymous)
    # Before deleting gallery let's summurize what we deleted
    # - unpublished tutorials with only the unregistering member as an author
    # - unpublished articles with only the unregistering member as an author
    # - all category associated with those entites (have a look on article.delete_entity_and_tree
    # and tutorial.delete_entity_and_tree
    # So concerning galleries, we just have for us
    # - "personnal galleries" with only one owner (unregistering user)
    # - "personnal galleries" with more than one owner
    # so we will just delete the unretistering user ownership and give it to anonymous in the only case
    # he was alone so that gallery is not lost
    galleries = UserGallery.objects.filter(user=current)
    for gallery in UserGallery.objects.filter(user=current):
        if gallery.gallery.get_linked_users().count() == 1:
            anonymous_gallery = UserGallery()
            anonymous_gallery.user = external
            anonymous_gallery.mode = 'w'
            anonymous_gallery.gallery = gallery.gallery
            anonymous_gallery.save()
    galleries.delete()

    # remove API access (tokens + applications)
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
    """Modifies sanction of a user if there is a POST request."""

    profile = get_object_or_404(Profile, user__pk=user_pk)
    if profile.is_private():
        raise PermissionDenied
    if request.user.profile == profile:
        messages.error(request, _(u'Vous ne pouvez pas vous sanctionner vous-même !'))
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
                     settings.ZDS_APP['site']['litteral_name'])

    state.notify_member(ban, msg)
    return redirect(profile.get_absolute_url())


@login_required
def tutorials(request):
    """Returns all tutorials of the authenticated user."""

    # The type indicate what the user would like to display. We can display
    # public, draft, beta, validate or all user's tutorials.

    try:
        state = request.GET['type']
    except KeyError:
        state = None

    # The sort indicate the order of tutorials.

    try:
        sort_tuto = request.GET['sort']
    except KeyError:
        sort_tuto = 'abc'

    # Retrieves all tutorials of the current user.

    profile = request.user.profile
    if state == 'draft':
        user_tutorials = profile.get_draft_tutos()
    elif state == 'beta':
        user_tutorials = profile.get_beta_tutos()
    elif state == 'validate':
        user_tutorials = profile.get_validate_tutos()
    elif state == 'public':
        user_tutorials = profile.get_public_tutos()
    else:
        user_tutorials = profile.get_tutos()

    # Order articles (abc by default)

    if sort_tuto == 'creation':
        pass  # nothing to do. Tutorials are already sort by creation date
    elif sort_tuto == 'modification':
        user_tutorials = user_tutorials.order_by('-update')
    else:
        user_tutorials = user_tutorials.extra(select={'lower_title': 'lower(title)'}).order_by('lower_title')

    return render(
        request,
        'tutorial/member/index.html',
        {'tutorials': user_tutorials, 'type': state, 'sort': sort_tuto}
    )


@login_required
def articles(request):
    """Returns all articles of the authenticated user."""

    # The type indicate what the user would like to display. We can display public, draft or all user's articles.

    try:
        state = request.GET['type']
    except KeyError:
        state = None

    # The sort indicate the order of articles.

    try:
        sort_articles = request.GET['sort']
    except KeyError:
        sort_articles = 'abc'

    # Retrieves all articles of the current user.

    profile = request.user.profile
    if state == 'draft':
        user_articles = profile.get_draft_articles()
    elif state == 'validate':
        user_articles = profile.get_validate_articles()
    elif state == 'public':
        user_articles = profile.get_public_articles()
    else:
        user_articles = PublishableContent.objects\
            .filter(authors__pk__in=[request.user.pk], type='ARTICLE')\
            .prefetch_related('authors', 'authors__profile')

    # Order articles (abc by default)

    if sort_articles == 'creation':
        pass  # nothing to do. Articles are already sort by creation date
    elif sort_articles == 'modification':
        user_articles = user_articles.order_by('-update')
    else:
        user_articles = user_articles.extra(select={'lower_title': 'lower(title)'}).order_by('lower_title')
    user_articles = [raw_article.load_dic(raw_article.load_json(None, raw_article.on_line()))
                     for raw_article in user_articles]
    return render(
        request,
        'article/member/index.html',
        {'articles': user_articles, 'type': type, 'sort': sort_articles}
    )


# settings for public profile

@can_write_and_read_now
@login_required
@permission_required('member.change_profile', raise_exception=True)
def settings_mini_profile(request, user_name):
    """Minimal settings of users for staff."""

    # extra information about the current user
    profile = get_object_or_404(Profile, user__username=user_name)
    if request.method == 'POST':
        form = MiniProfileForm(request.POST)
        data = {'form': form, 'profile': profile}
        if form.is_valid():
            profile.biography = form.data['biography']
            profile.site = form.data['site']
            profile.avatar_url = form.data['avatar_url']
            profile.sign = form.data['sign']

            # Save the profile and redirect the user to the configuration space
            # with message indicate the state of the operation

            try:
                profile.save()
            except:
                messages.error(request, _(u'Une erreur est survenue.'))
                return redirect(reverse('member-settings-mini-profile'))

            messages.success(request, _(u'Le profil a correctement été mis à jour.'))
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
            u'Le profil que vous éditez n\'est pas le vôtre. '
            u'Soyez encore plus prudent lors de l\'édition de celui-ci !'))
        return render(request, 'member/settings/profile.html', data)


def login_view(request):
    """Log in user."""

    csrf_tk = {}
    csrf_tk.update(csrf(request))
    error = False
    initial = {}

    # Redirecting user once logged in?

    if 'next' in request.GET:
        next_page = request.GET['next']
    else:
        next_page = None
    if request.method == 'POST':
        form = LoginForm(request.POST)
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            profile = get_object_or_404(Profile, user=user)
            if user.is_active:
                if profile.can_read_now():
                    login(request, user)
                    request.session['get_token'] = generate_token()
                    if 'remember' not in request.POST:
                        request.session.set_expiry(0)
                    profile.last_ip_address = get_client_ip(request)
                    profile.save()
                    # redirect the user if needed
                    try:
                        return redirect(next_page)
                    except:
                        return redirect(reverse('homepage'))
                else:
                    messages.error(request,
                                   _(u'Vous n\'êtes pas autorisé à vous connecter '
                                     u'sur le site, vous avez été banni par un '
                                     u'modérateur.'))
            else:
                messages.error(request,
                               _(u'Vous n\'avez pas encore activé votre compte, '
                                 u'vous devez le faire pour pouvoir vous '
                                 u'connecter sur le site. Regardez dans vos '
                                 u'mails : {}.').format(user.email))
        else:
            messages.error(request,
                           _(u'Les identifiants fournis ne sont pas valides.'))
            initial = {'username': username}

    form = LoginForm(initial=initial)
    if next_page is not None:
        form.helper.form_action += '?next=' + next_page

    csrf_tk['error'] = error
    csrf_tk['form'] = form
    csrf_tk['next_page'] = next_page
    return render(request, 'member/login.html',
                  {'form': form,
                   'csrf_tk': csrf_tk})


@login_required
@require_POST
def logout_view(request):
    """Log out user."""

    logout(request)
    request.session.clear()
    return redirect(reverse('homepage'))


def forgot_password(request):
    """If the user forgot his password, he can have a new one."""

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

            # Generate a valid token during one hour.
            uuid_token = str(uuid.uuid4())
            date_end = datetime.now() + timedelta(days=0, hours=1, minutes=0,
                                                  seconds=0)
            token = TokenForgotPassword(user=usr, token=uuid_token,
                                        date_end=date_end)
            token.save()

            # send email
            subject = _(u'{} - Mot de passe oublié').format(settings.ZDS_APP['site']['litteral_name'])
            from_email = '{} <{}>'.format(settings.ZDS_APP['site']['litteral_name'],
                                          settings.ZDS_APP['site']['email_noreply'])
            context = {
                'username': usr.username,
                'site_name': settings.ZDS_APP['site']['litteral_name'],
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
            # User can't confirm his request if it is too late.

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
    """Active token for a user."""
    try:
        token = request.GET['token']
    except KeyError:
        return redirect(reverse('homepage'))
    token = get_object_or_404(TokenRegister, token=token)
    usr = token.user

    # User can't confirm their request if their account is already active
    if usr.is_active:
        return render(request, 'member/register/token_already_used.html')

    # User can't confirm their request if it is too late.
    if datetime.now() > token.date_end:
        return render(request, 'member/register/token_failed.html',
                      {'token': token})
    usr.is_active = True
    usr.save()

    # send welcome message
    bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
    msg = render_to_string(
        'member/messages/account_activated.md',
        {
            'username': usr.username,
            'tutorials_url': settings.ZDS_APP['site']['url'] + reverse('tutorial:list'),
            'articles_url': settings.ZDS_APP['site']['url'] + reverse('article:list'),
            'opinions_url': settings.ZDS_APP['site']['url'] + reverse('opinion:list'),
            'members_url': settings.ZDS_APP['site']['url'] + reverse('member-list'),
            'forums_url': settings.ZDS_APP['site']['url'] + reverse('cats-forums-list'),
            'site_name': settings.ZDS_APP['site']['litteral_name']
        }
    )

    send_mp(bot,
            [usr],
            _(u'Bienvenue sur {}').format(settings.ZDS_APP['site']['litteral_name']),
            _(u'Le manuel du nouveau membre'),
            msg,
            False,
            True,
            False)
    token.delete()
    form = LoginForm(initial={'username': usr.username})
    return render(request, 'member/register/token_success.html', {'usr': usr, 'form': form})


def generate_token_account(request):
    """Generate token for account."""

    try:
        token = request.GET['token']
    except KeyError:
        return redirect(reverse('homepage'))
    token = get_object_or_404(TokenRegister, token=token)

    # push date

    date_end = datetime.now() + timedelta(days=0, hours=1, minutes=0,
                                          seconds=0)
    token.date_end = date_end
    token.save()

    # send email
    subject = _(u"{} - Confirmation d'inscription").format(settings.ZDS_APP['site']['litteral_name'])
    from_email = '{} <{}>'.format(settings.ZDS_APP['site']['litteral_name'],
                                  settings.ZDS_APP['site']['email_noreply'])
    context = {
        'username': token.user.username,
        'site_url': settings.ZDS_APP['site']['url'],
        'site_name': settings.ZDS_APP['site']['litteral_name'],
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
        # should never happend
        return '0.0.0.0'


@login_required
def settings_promote(request, user_pk):
    """ Manage the admin right of user. Only super user can access """

    if not request.user.is_superuser:
        raise PermissionDenied

    profile = get_object_or_404(Profile, user__pk=user_pk)
    user = profile.user

    if request.method == 'POST':
        form = PromoteMemberForm(request.POST)
        data = dict(form.data.iterlists())

        groups = Group.objects.all()
        usergroups = user.groups.all()

        if 'groups' in data:
            for group in groups:
                if unicode(group.id) in data['groups']:
                    if group not in usergroups:
                        user.groups.add(group)
                        messages.success(request, _(u'{0} appartient maintenant au groupe {1}.')
                                         .format(user.username, group.name))
                else:
                    if group in usergroups:
                        user.groups.remove(group)
                        messages.warning(request, _(u'{0} n\'appartient maintenant plus au groupe {1}.')
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
            messages.warning(request, _(u'{0} n\'appartient (plus ?) à aucun groupe.')
                             .format(user.username))

        if 'activation' in data and u'on' in data['activation']:
            user.is_active = True
            messages.success(request, _(u'{0} est maintenant activé.')
                             .format(user.username))
        else:
            user.is_active = False
            messages.warning(request, _(u'{0} est désactivé.')
                             .format(user.username))

        user.save()

        usergroups = user.groups.all()
        bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
        msg = _(u'Bonjour {0},\n\n'
                u'Un administrateur vient de modifier les groupes '
                u'auxquels vous appartenez.  \n').format(user.username)
        if len(usergroups) > 0:
            msg = string_concat(msg, _(u'Voici la liste des groupes dont vous faites dorénavant partie :\n\n'))
            for group in usergroups:
                msg += u'* {0}\n'.format(group.name)
        else:
            msg = string_concat(msg, _(u'* Vous ne faites partie d\'aucun groupe'))
        send_mp(
            bot,
            [user],
            _(u'Modification des groupes'),
            u'',
            msg,
            True,
            True,
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
    """ Get list of user connected from a particular ip """

    members = Profile.objects.filter(last_ip_address=ip_address).order_by('-last_visit')
    return render(request, 'member/settings/memberip.html', {
        'members': members,
        'ip': ip_address
    })


@login_required
@permission_required('member.change_profile', raise_exception=True)
@require_POST
def modify_karma(request):
    """ Add a Karma note to the user profile """

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
        logging.getLogger('zds.member').warn('ValueError: modifying karma failed because {}'.format(e))

    return redirect(reverse('member-detail', args=[profile.user.username]))
