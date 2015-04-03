# coding: utf-8

from datetime import datetime, timedelta
import uuid

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.core.context_processors import csrf
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Q
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import redirect, render, get_object_or_404
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, UpdateView, CreateView
from forms import LoginForm, MiniProfileForm, ProfileForm, RegisterForm, \
    ChangePasswordForm, ChangeUserForm, ForgotPasswordForm, NewPasswordForm, \
    OldTutoForm, PromoteMemberForm, KarmaForm
from zds.utils.models import Comment, CommentLike, CommentDislike
from models import Profile, TokenForgotPassword, TokenRegister, KarmaNote
from zds.article.models import Article
from zds.gallery.forms import ImageAsAvatarForm
from zds.gallery.models import UserGallery
from zds.forum.models import Topic, follow, TopicFollowed
from zds.member.decorator import can_write_and_read_now
from zds.member.commons import ProfileCreate, TemporaryReadingOnlySanction, ReadingOnlySanction, \
    DeleteReadingOnlySanction, TemporaryBanSanction, BanSanction, DeleteBanSanction, TokenGenerator
from zds.mp.models import PrivatePost, PrivateTopic
from zds.tutorial.models import Tutorial
from zds.utils.mps import send_mp
from zds.utils.paginator import ZdSPagingListView
from zds.utils.tokens import generate_token


class MemberList(ZdSPagingListView):
    """Displays the list of registered users."""

    context_object_name = 'members'
    paginate_by = settings.ZDS_APP['member']['members_per_page']
    # TODO When User will be no more used, you can make this request with
    # Profile.objects.all_members_ordered_by_date_joined()
    queryset = User.objects.order_by('-date_joined').all().select_related("profile")
    template_name = 'member/index.html'


class MemberDetail(DetailView):
    """Displays details about a profile."""

    context_object_name = 'usr'
    model = User
    template_name = 'member/profile.html'

    def get_object(self, queryset=None):
        return get_object_or_404(User, username=self.kwargs['user_name'])

    def get_context_data(self, **kwargs):
        context = super(MemberDetail, self).get_context_data(**kwargs)
        usr = context['usr']
        profile = usr.profile
        context['profile'] = profile
        context['topics'] = Topic.objects.last_topics_of_a_member(usr, self.request.user)
        context['articles'] = Article.objects.last_articles_of_a_member_loaded(usr)
        context['tutorials'] = Tutorial.objects.last_tutorials_of_a_member_loaded(usr)
        context['old_tutos'] = Profile.objects.all_old_tutos_from_site_du_zero(profile)
        context['karmanotes'] = KarmaNote.objects.filter(user=usr).order_by('-create_at')
        context['karmaform'] = KarmaForm(profile)
        context['form'] = OldTutoForm(profile)

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

    def get_form(self, form_class):
        profile = self.get_object()
        form = form_class(initial={
            'biography': profile.biography,
            'site': profile.site,
            'avatar_url': profile.avatar_url,
            'show_email': profile.show_email,
            'show_sign': profile.show_sign,
            'hover_or_click': profile.hover_or_click,
            'email_for_answer': profile.email_for_answer,
            'sign': profile.sign
        })

        return form

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

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
        profile.show_email = 'show_email' in cleaned_data_options
        profile.show_sign = 'show_sign' in cleaned_data_options
        profile.hover_or_click = 'hover_or_click' in cleaned_data_options
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


class UpdateAvatarMember(UpdateMember):
    """Update avatar of a user logged."""

    form_class = ImageAsAvatarForm

    def get_success_url(self):
        profile = self.get_object()

        return reverse('member-detail', args=[profile.user.username])

    def get_form(self, form_class):
        return form_class(self.request.POST)

    def update_profile(self, profile, form):
        profile.avatar_url = form.data['avatar_url']

    def get_success_message(self):
        return _(u'L\'avatar a correctement été mis à jour.')


class UpdatePasswordMember(UpdateMember):
    """User's settings about his password."""

    form_class = ChangePasswordForm

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.user, request.POST)

        if form.is_valid():
            return self.form_valid(form)

        return render(request, self.template_name, {'form': form})

    def get_form(self, form_class):
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

    def get_form(self, form_class):
        return form_class(self.request.POST)

    def update_profile(self, profile, form):
        if form.data['username']:
            profile.user.username = form.data['username']
        if form.data['email']:
            if form.data['email'].strip() != '':
                profile.user.email = form.data['email']

    def get_success_url(self):
        profile = self.get_object()

        return profile.get_absolute_url()


class RegisterView(CreateView, ProfileCreate, TokenGenerator):
    """Create a profile."""

    form_class = RegisterForm
    template_name = 'member/register/index.html'

    def get_object(self, queryset=None):
        return get_object_or_404(Profile, user=self.request.user)

    def get_form(self, form_class):
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

    anonymous = get_object_or_404(User, username=settings.ZDS_APP["member"]["anonymous_account"])
    external = get_object_or_404(User, username=settings.ZDS_APP["member"]["external_account"])
    current = request.user
    for tuto in request.user.profile.get_tutos():
        # we delete article only if not published with only one author
        if not tuto.on_line() and tuto.authors.count() == 1:
            if tuto.in_beta():
                beta_topic = Topic.objects.get(key=tuto.pk)
                first_post = beta_topic.first_post()
                first_post.update_content(_(u"# Le tutoriel présenté par ce topic n\'existe plus."))
            tuto.delete_entity_and_tree()
        else:
            if tuto.authors.count() == 1:
                tuto.authors.add(external)
                external_gallery = UserGallery()
                external_gallery.user = external
                external_gallery.gallery = tuto.gallery
                external_gallery.mode = 'W'
                external_gallery.save()
                UserGallery.objects.filter(user=current).filter(gallery=tuto.gallery).delete()

            tuto.authors.remove(current)
            tuto.save()
    for article in request.user.profile.get_articles():
        # we delete article only if not published with only one author
        if not article.on_line() and article.authors.count() == 1:
            article.delete_entity_and_tree()
        else:
            if article.authors.count() == 1:
                article.authors.add(external)
            article.authors.remove(current)
            article.save()
    # comments likes / dislikes
    for like in CommentLike.objects.filter(user=current):
        like.comments.like -= 1
        like.comments.save()
        like.delete()
    for dislike in CommentDislike.objects.filter(user=current):
        dislike.comments.dislike -= 1
        dislike.comments.save()
        dislike.delete()
    # all messages anonymisation (forum, article and tutorial posts)
    for message in Comment.objects.filter(author=current):
        message.author = anonymous
        message.save()
    for message in PrivatePost.objects.filter(author=current):
        message.author = anonymous
        message.save()
    # in case current has been moderator in his old day
    for message in Comment.objects.filter(editor=current):
        message.editor = anonymous
        message.save()
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
    for topic in Topic.objects.filter(author=current):
        topic.author = anonymous
        topic.save()
    TopicFollowed.objects.filter(user=current).delete()
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
    for gallery in UserGallery.objects.filter(user=current):
        if gallery.gallery.get_linked_users().count() == 1:
            anonymous_gallery = UserGallery()
            anonymous_gallery.user = external
            anonymous_gallery.mode = "w"
            anonymous_gallery.gallery = gallery.gallery
            anonymous_gallery.save()
        gallery.delete()

    logout(request)
    User.objects.filter(pk=current.pk).delete()
    return redirect(reverse("zds.pages.views.home"))


@require_POST
@can_write_and_read_now
@login_required
@transaction.atomic
def modify_profile(request, user_pk):
    """Modifies sanction of a user if there is a POST request."""

    profile = get_object_or_404(Profile, user__pk=user_pk)
    if profile.is_private():
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
                     ban.text,
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
        user_articles = profile.get_articles()

    # Order articles (abc by default)

    if sort_articles == 'creation':
        pass  # nothing to do. Articles are already sort by creation date
    elif sort_articles == 'modification':
        user_articles = user_articles.order_by('-update')
    else:
        user_articles = user_articles.extra(select={'lower_title': 'lower(title)'}).order_by('lower_title')

    return render(
        request,
        'article/member/index.html',
        {'articles': user_articles, 'type': type, 'sort': sort_articles}
    )


# settings for public profile

@can_write_and_read_now
@login_required
def settings_mini_profile(request, user_name):
    """Minimal settings of users for staff."""

    # extra information about the current user
    profile = get_object_or_404(Profile, user__username=user_name)
    if request.method == "POST":
        form = MiniProfileForm(request.POST)
        c = {"form": form, "profile": profile}
        if form.is_valid():
            profile.biography = form.data["biography"]
            profile.site = form.data["site"]
            profile.avatar_url = form.data["avatar_url"]
            profile.sign = form.data["sign"]

            # Save the profile and redirect the user to the configuration space
            # with message indicate the state of the operation

            try:
                profile.save()
            except:
                messages.error(request, u"Une erreur est survenue.")
                return redirect(reverse("zds.member.views.settings_mini_profil"
                                        "e"))
            messages.success(request,
                             _(u"Le profil a correctement été mis à jour."))
            return redirect(reverse("member-detail",
                                    args=[profile.user.username]))
        else:
            return render(request, "member/settings/profile.html", c)
    else:
        form = MiniProfileForm(initial={
            "biography": profile.biography,
            "site": profile.site,
            "avatar_url": profile.avatar_url,
            "sign": profile.sign,
        })
        c = {"form": form, "profile": profile}
        return render(request, "member/settings/profile.html", c)


def login_view(request):
    """Log in user."""

    csrf_tk = {}
    csrf_tk.update(csrf(request))
    error = False

    # Redirecting user once logged in?

    if "next" in request.GET:
        next_page = request.GET["next"]
    else:
        next_page = None
    if request.method == "POST":
        form = LoginForm(request.POST)
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(username=username, password=password)
        if user is not None:
            profile = get_object_or_404(Profile, user=user)
            if user.is_active:
                if profile.can_read_now():
                    login(request, user)
                    request.session["get_token"] = generate_token()
                    if "remember" not in request.POST:
                        request.session.set_expiry(0)
                    profile.last_ip_address = get_client_ip(request)
                    profile.save()
                    # redirect the user if needed
                    try:
                        return redirect(next_page)
                    except:
                        return redirect(reverse("zds.pages.views.home"))
                else:
                    messages.error(request,
                                   _(u"Vous n'êtes pas autorisé à vous connecter "
                                     u"sur le site, vous avez été banni par un "
                                     u"modérateur."))
            else:
                messages.error(request,
                               _(u"Vous n'avez pas encore activé votre compte, "
                                 u"vous devez le faire pour pouvoir vous "
                                 u"connecter sur le site. Regardez dans vos "
                                 u"mails : {}.").format(user.email))
        else:
            messages.error(request,
                           _(u"Les identifiants fournis ne sont pas valides."))

    if next_page is not None:
        form = LoginForm()
        form.helper.form_action += "?next=" + next_page
    else:
        form = LoginForm()

    csrf_tk["error"] = error
    csrf_tk["form"] = form
    csrf_tk["next_page"] = next_page
    return render(request, "member/login.html",
                  {"form": form,
                   "csrf_tk": csrf_tk})


@login_required
@require_POST
def logout_view(request):
    """Log out user."""

    logout(request)
    request.session.clear()
    return redirect(reverse("zds.pages.views.home"))


def forgot_password(request):
    """If the user forgot his password, he can have a new one."""

    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():

            # Get data from form
            data = form.data
            username = data["username"]
            email = data["email"]

            # Fetch the user, we need his email adress
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
            subject = _(u"{} - Mot de passe oublié").format(settings.ZDS_APP['site']['litteral_name'])
            from_email = "{} <{}>".format(settings.ZDS_APP['site']['litteral_name'],
                                          settings.ZDS_APP['site']['email_noreply'])
            context = {
                "username": usr.username,
                "site_name": settings.ZDS_APP['site']['litteral_name'],
                "site_url": settings.ZDS_APP['site']['url'],
                "url": settings.ZDS_APP['site']['url'] + token.get_absolute_url()
            }
            message_html = render_to_string("email/member/confirm_forgot_password.html", context)
            message_txt = render_to_string("email/member/confirm_forgot_password.txt", context)

            msg = EmailMultiAlternatives(subject, message_txt, from_email, [usr.email])
            msg.attach_alternative(message_html, "text/html")
            msg.send()
            return render(request, "member/forgot_password/success.html")
        else:
            return render(request, "member/forgot_password/index.html",
                          {"form": form})
    form = ForgotPasswordForm()
    return render(request, "member/forgot_password/index.html", {"form": form})


def new_password(request):
    """Create a new password for a user."""

    try:
        token = request.GET["token"]
    except KeyError:
        return redirect(reverse("zds.pages.views.home"))
    token = get_object_or_404(TokenForgotPassword, token=token)
    if request.method == "POST":
        form = NewPasswordForm(token.user.username, request.POST)
        if form.is_valid():
            data = form.data
            password = data["password"]
            # User can't confirm his request if it is too late.

            if datetime.now() > token.date_end:
                return render(request, "member/new_password/failed.html")
            token.user.set_password(password)
            token.user.save()
            token.delete()
            return render(request, "member/new_password/success.html")
        else:
            return render(request, "member/new_password/index.html", {"form": form})
    form = NewPasswordForm(identifier=token.user.username)
    return render(request, "member/new_password/index.html", {"form": form})


def active_account(request):
    """Active token for a user."""

    try:
        token = request.GET["token"]
    except KeyError:
        return redirect(reverse("zds.pages.views.home"))
    token = get_object_or_404(TokenRegister, token=token)
    usr = token.user

    # User can't confirm his request if he is already activated.

    if usr.is_active:
        return render(request, "member/register/token_already_used.html")

    # User can't confirm his request if it is too late.

    if datetime.now() > token.date_end:
        return render(request, "member/register/token_failed.html",
                      {"token": token})
    usr.is_active = True
    usr.save()

    # send register message

    bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
    msg = _(
        u'Bonjour **{username}**,'
        u'\n\n'
        u'Ton compte a été activé, et tu es donc officiellement '
        u'membre de la communauté de {site_name}.'
        u'\n\n'
        u'{site_name} est une communauté dont le but est de diffuser des '
        u'connaissances au plus grand nombre.'
        u'\n\n'
        u'Sur ce site, tu trouveras un ensemble de [tutoriels]({tutorials_url}) dans '
        u'plusieurs domaines et plus particulièrement autour de l\'informatique '
        u'et des sciences. Tu y retrouveras aussi des [articles]({articles_url}) '
        u'traitant de sujets d\'actualité ou non, qui, tout comme les tutoriels, '
        u'sont écrits par des [membres]({members_url}) de la communauté. '
        u'Pendant tes lectures et ton apprentissage, si jamais tu as des '
        u'questions à poser, tu retrouveras sur les [forums]({forums_url}) des personnes '
        u'prêtes à te filer un coup de main et ainsi t\'éviter de passer '
        u'plusieurs heures sur un problème.'
        u'\n\n'
        u'L\'ensemble du contenu disponible sur le site est et sera toujours gratuit, '
        u'car la communauté de {site_name} est attachée aux valeurs du libre '
        u'partage et désire apporter le savoir à tout le monde quels que soient ses moyens.'
        u'\n\n'
        u'En espérant que tu te plairas ici, '
        u'je te laisse maintenant faire un petit tour.'
        u'\n\n'
        u'Clem\'') \
        .format(username=usr.username,
                tutorials_url=settings.ZDS_APP['site']['url'] + reverse("zds.tutorial.views.index"),
                articles_url=settings.ZDS_APP['site']['url'] + reverse("zds.article.views.index"),
                members_url=settings.ZDS_APP['site']['url'] + reverse("member-list"),
                forums_url=settings.ZDS_APP['site']['url'] + reverse("zds.forum.views.index"),
                site_name=settings.ZDS_APP['site']['litteral_name'])
    send_mp(
        bot,
        [usr],
        _(u"Bienvenue sur {}").format(settings.ZDS_APP['site']['litteral_name']),
        _(u"Le manuel du nouveau membre"),
        msg,
        True,
        True,
        False,
    )
    token.delete()
    form = LoginForm(initial={'username': usr.username})
    return render(request, "member/register/token_success.html", {"usr": usr, "form": form})


def generate_token_account(request):
    """Generate token for account."""

    try:
        token = request.GET["token"]
    except KeyError:
        return redirect(reverse("zds.pages.views.home"))
    token = get_object_or_404(TokenRegister, token=token)

    # push date

    date_end = datetime.now() + timedelta(days=0, hours=1, minutes=0,
                                          seconds=0)
    token.date_end = date_end
    token.save()

    # send email
    subject = _(u"{} - Confirmation d'inscription").format(settings.ZDS_APP['site']['litteral_name'])
    from_email = "{} <{}>".format(settings.ZDS_APP['site']['litteral_name'],
                                  settings.ZDS_APP['site']['email_noreply'])
    context = {
        "username": token.user.username,
        "site_url": settings.ZDS_APP['site']['url'],
        "site_name": settings.ZDS_APP['site']['litteral_name'],
        "url": settings.ZDS_APP['site']['url'] + token.get_absolute_url()
    }
    message_html = render_to_string("email/member/confirm_registration.html", context)
    message_txt = render_to_string("email/member/confirm_registration.txt", context)

    msg = EmailMultiAlternatives(subject, message_txt, from_email, [token.user.email])
    msg.attach_alternative(message_html, "text/html")
    try:
        msg.send()
    except:
        msg = None
    return render(request, 'member/register/success.html', {})


def get_client_ip(request):
    """Retrieve the real IP address of the client."""

    if "HTTP_X_REAL_IP" in request.META:  # nginx
        return request.META.get("HTTP_X_REAL_IP")
    elif "REMOTE_ADDR" in request.META:
        # other
        return request.META.get("REMOTE_ADDR")
    else:
        # should never happend
        return "0.0.0.0"


def date_to_chart(posts):
    lst = 24 * [0]
    for i in range(len(lst)):
        lst[i] = 7 * [0]
    for post in posts:
        t = post.pubdate.timetuple()
        lst[t.tm_hour][(t.tm_wday + 1) % 7] = lst[t.tm_hour][(t.tm_wday + 1)
                                                             % 7] + 1
    return lst


@login_required
@require_POST
def add_oldtuto(request):
    id = request.POST["id"]
    profile_pk = request.POST["profile_pk"]
    profile = get_object_or_404(Profile, pk=profile_pk)
    if profile.sdz_tutorial:
        olds = profile.sdz_tutorial.strip().split(":")
    else:
        olds = []
    last = str(id)
    for old in olds:
        last += ":{0}".format(old)
    profile.sdz_tutorial = last
    profile.save()
    messages.success(request,
                     _(u'Le tutoriel a bien été lié au '
                       u'membre {0}.').format(profile.user.username))
    return redirect(reverse("member-detail",
                            args=[profile.user.username]))


@login_required
def remove_oldtuto(request):
    if "id" in request.GET:
        id = request.GET["id"]
    else:
        raise Http404
    if "profile" in request.GET:
        profile_pk = request.GET["profile"]
    else:
        raise Http404
    profile = get_object_or_404(Profile, pk=profile_pk)
    if profile.sdz_tutorial \
            or not request.user.has_perm("member.change_profile"):
        olds = profile.sdz_tutorial.strip().split(":")
        olds.remove(str(id))
    else:
        raise PermissionDenied
    last = ""
    for i in range(len(olds)):
        if i > 0:
            last += ":"
        last += "{0}".format(str(olds[i]))
    profile.sdz_tutorial = last
    profile.save()

    messages.success(request,
                     _(u'Le tutoriel a bien été retiré '
                       u'au membre {0}.').format(profile.user.username))
    return redirect(reverse("member-detail",
                            args=[profile.user.username]))


@login_required
def settings_promote(request, user_pk):
    """ Manage the admin right of user. Only super user can access """

    if not request.user.is_superuser:
        raise PermissionDenied

    profile = get_object_or_404(Profile, user__pk=user_pk)
    user = profile.user

    if request.method == "POST":
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
                        topics_followed = Topic.objects.filter(topicfollowed__user=user,
                                                               forum__group=group)
                        for topic in topics_followed:
                            follow(topic, user)
        else:
            for group in usergroups:
                topics_followed = Topic.objects.filter(topicfollowed__user=user,
                                                       forum__group=group)
                for topic in topics_followed:
                    follow(topic, user)
            user.groups.clear()
            messages.warning(request, _(u'{0} n\'appartient (plus ?) à aucun groupe.')
                             .format(user.username))

        if 'superuser' in data and u'on' in data['superuser']:
            if not user.is_superuser:
                user.is_superuser = True
                messages.success(request, _(u'{0} est maintenant super-utilisateur.')
                                 .format(user.username))
        else:
            if user == request.user:
                messages.error(request, _(u'Un super-utilisateur ne peux pas se retirer des super-utilisateurs.'))
            else:
                if user.is_superuser:
                    user.is_superuser = False
                    messages.warning(request, _(u'{0} n\'est maintenant plus super-utilisateur.')
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
            msg += _(u'Voici la liste des groupes dont vous faites dorénavant partie :\n\n')
            for group in usergroups:
                msg += u'* {0}\n'.format(group.name)
        else:
            msg += _(u'* Vous ne faites partie d\'aucun groupe')
        msg += u'\n\n'
        if user.is_superuser:
            msg += _(u'Vous avez aussi rejoint le rang des super utilisateurs. '
                     u'N\'oubliez pas, un grand pouvoir entraine de grandes responsabiltiés !')
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
        'superuser': user.is_superuser,
        'groups': user.groups.all(),
        'activation': user.is_active
    })
    return render(request, 'member/settings/promote.html', {
        "usr": user,
        "profile": profile,
        "form": form
    })


@login_required
def member_from_ip(request, ip):
    """ Get list of user connected from a particular ip """

    if not request.user.has_perm("member.change_profile"):
        raise PermissionDenied

    members = Profile.objects.filter(last_ip_address=ip).order_by('-last_visit')
    return render(request, 'member/settings/memberip.html', {
        "members": members,
        "ip": ip
    })


@login_required
@require_POST
def modify_karma(request):
    """ Add a Karma note to the user profile """

    if not request.user.has_perm("member.change_profile"):
        raise PermissionDenied

    try:
        profile_pk = request.POST["profile_pk"]
    except (KeyError, ValueError):
        raise Http404

    profile = get_object_or_404(Profile, pk=profile_pk)
    if profile.is_private():
        raise PermissionDenied

    note = KarmaNote()
    note.user = profile.user
    note.staff = request.user
    note.comment = request.POST["warning"]
    try:
        note.value = int(request.POST["points"])
    except (KeyError, ValueError):
        note.value = 0

    note.save()

    profile.karma += note.value
    profile.save()

    return redirect(reverse("member-detail", args=[profile.user.username]))
