#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import os
import uuid

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, SiteProfileNotAvailable
from django.core.context_processors import csrf
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMultiAlternatives
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import Http404
from django.shortcuts import redirect, get_object_or_404, render_to_response
from django.template import Context, RequestContext
from django.template.loader import get_template
from django.views.decorators.http import require_POST
import pygal

from forms import LoginForm, MiniProfileForm, ProfileForm, RegisterForm, \
    ChangePasswordForm, ChangeUserForm, ForgotPasswordForm, NewPasswordForm, \
    OldTutoForm
from models import Profile, TokenForgotPassword, Ban, TokenRegister, \
    get_info_old_tuto
from zds.gallery.forms import ImageAsAvatarForm
from zds.article.models import Article
from zds.forum.models import Topic
from zds.member.decorator import can_read_now, can_write_and_read_now
from zds.tutorial.models import Tutorial
from zds.utils import render_template
from zds.utils.mps import send_mp
from zds.utils.paginator import paginator_range
from zds.utils.tokens import generate_token


@can_read_now
def index(request):
    """Displays the list of registered users."""

    if request.is_ajax():
        q = request.GET.get('q', '')
        members = User.objects.filter(username__icontains = q )[:20]
        results = []
        for member in members:
            member_json = {}
            member_json['id'] = member.pk
            member_json['label'] = member.username
            member_json['value'] = member.username
            results.append(member_json)
        data = json.dumps(results)

        return HttpResponse(data, mimetype)
    
    else:
        members = User.objects.order_by("-date_joined")
        # Paginator
    
        paginator = Paginator(members, settings.MEMBERS_PER_PAGE)
        page = request.GET.get("page")
        try:
            shown_members = paginator.page(page)
            page = int(page)
        except PageNotAnInteger:
            shown_members = paginator.page(1)
            page = 1
        except EmptyPage:
            shown_members = paginator.page(paginator.num_pages)
            page = paginator.num_pages
        return render_template("member/index.html", {
            "members": shown_members,
            "count": members.count(),
            "pages": paginator_range(page, paginator.num_pages),
            "nb": page,
        })


@can_read_now
def details(request, user_name):
    """Displays details about a profile."""

    usr = get_object_or_404(User, username=user_name)
    try:
        profile = usr.profile
        bans = Ban.objects.filter(user=usr).order_by("-pubdate")
    except SiteProfileNotAvailable:
        raise Http404

    # refresh moderation chart

    dot_chart = pygal.Dot(x_label_rotation=30)
    dot_chart.title = u"Messages postés par période"
    dot_chart.x_labels = [
        u"Dimanche",
        u"Lundi",
        u"Mardi",
        u"Mercredi",
        u"Jeudi",
        u"Vendredi",
        u"Samedi",
    ]
    dot_chart.show_legend = False
    dates = date_to_chart(profile.get_posts())
    for i in range(0, 24):
        dot_chart.add(str(i) + " h", dates[(i + 1) % 24])
    img_path = os.path.join(settings.MEDIA_ROOT, "pygal")
    if not os.path.isdir(img_path):
        os.makedirs(img_path, mode=0o777)
    fchart = os.path.join(img_path, "mod-{}.svg".format(str(usr.pk)))
    dot_chart.render_to_file(fchart)
    my_articles = Article.objects.filter(sha_public__isnull=False).order_by(
        "-pubdate").filter(authors__in=[usr]).all()
    my_tutorials = \
        Tutorial.objects.filter(sha_public__isnull=False) \
        .filter(authors__in=[usr]) \
        .order_by("-pubdate"
                  ).all()
    my_topics = Topic.objects.filter(author__pk=usr.pk).order_by("-pubdate"
                                                                 ).all()
    tops = []
    for top in my_topics:
        if not top.forum.can_read(request.user):
            continue
        else:
            tops.append(top)
            if len(tops) >= 5:
                break
    form = OldTutoForm(profile)
    oldtutos = []
    if profile.sdz_tutorial:
        olds = profile.sdz_tutorial.strip().split(":")
    else:
        olds = []
    for old in olds:
        oldtutos.append(get_info_old_tuto(old))
    return render_template("member/profile.html", {
        "usr": usr,
        "profile": profile,
        "bans": bans,
        "articles": my_articles,
        "tutorials": my_tutorials,
        "topics": tops,
        "form": form,
        "old_tutos": oldtutos,
    })


@can_write_and_read_now
@login_required
@transaction.atomic
def modify_profile(request, user_pk):
    """Modifies sanction of a user if there is a POST request."""

    profile = get_object_or_404(Profile, user__pk=user_pk)
    if request.method == "POST":
        ban = Ban()
        ban.moderator = request.user
        ban.user = profile.user
        ban.pubdate = datetime.now()
        if "ls" in request.POST:
            profile.can_write = False
            ban.type = u"Lecture Seule"
            ban.text = request.POST["ls-text"]
            detail = \
                u"vous ne pouvez plus poster dans les forums, ni dans les u\
                ucommentaires d'articles et de tutoriels."
        if "ls-temp" in request.POST:
            ban.type = u"Lecture Seule Temporaire"
            ban.text = request.POST["ls-temp-text"]
            profile.can_write = False
            profile.end_ban_write = datetime.now() \
                + timedelta(days=int(request.POST["ls-jrs"]), hours=0,
                            minutes=0, seconds=0)
            detail = \
                u"vous ne pouvez plus poster dans les forums, ni dans les u\
                ucommentaires d'articles et de tutoriels pendant " \
                + request.POST["ls-jrs"] + " jours."
        if "ban-temp" in request.POST:
            ban.type = u"Ban Temporaire"
            ban.text = request.POST["ban-temp-text"]
            profile.can_read = False
            profile.end_ban_read = datetime.now() \
                + timedelta(days=int(request.POST["ban-jrs"]), hours=0,
                            minutes=0, seconds=0)
            detail = \
                u"vous ne pouvez plus vous connecter sur ZesteDeSavoir u\
                upendant " + request.POST["ban-jrs"] + " jours."
        if "ban" in request.POST:
            ban.type = u"Ban définitif"
            ban.text = request.POST["ban-text"]
            profile.can_read = False
            detail = u"vous ne pouvez plus vous connecter sur ZesteDeSavoir."
        if "un-ls" in request.POST:
            ban.type = u"Autorisation d'écrire"
            ban.text = request.POST["unls-text"]
            profile.can_write = True
            detail = \
                u"vous pouvez désormais poster sur les forums, dans les u\
                ucommentaires d'articles et tutoriels."
        if "un-ban" in request.POST:
            ban.type = u"Autorisation de se connecter"
            ban.text = request.POST["unban-text"]
            profile.can_read = True
            detail = u"vous pouvez désormais vous connecter sur le site."
        profile.save()
        ban.save()

        # send register message

        if "un-ls" in request.POST or "un-ban" in request.POST:
            msg = \
                u"""Bonjour **{0}**,

**Bonne Nouvelle**, la sanction qui pesait sur vous a été levée par **{1}**.

Ce qui signifie que {2}

Le motif de votre sanction est :

`{3}`

Cordialement, L'équipe ZesteDeSavoir.

""".format(ban.user,
                    ban.moderator, detail, ban.text)
        else:
            msg = \
                u"""Bonjour **{0}**,

Vous avez été santionné par **{1}**.

La sanction est de type *{2}*, ce qui signifie que {3}

Le motif de votre sanction est :

`{4}`

Cordialement, L'équipe ZesteDeSavoir.

""".format(ban.user,
                    ban.moderator, ban.type, detail, ban.text)
        bot = get_object_or_404(User, username=settings.BOT_ACCOUNT)
        send_mp(
            bot,
            [ban.user],
            ban.type,
            "Sanction",
            msg,
            True,
            direct=True,
        )
    return redirect(profile.get_absolute_url())


@can_read_now
@login_required
def tutorials(request):
    """Returns all tutorials of the authenticated user."""

    # The type indicate what the user would like to display. We can display
    # public, draft or all user's tutorials.

    try:
        type = request.GET["type"]
    except KeyError:
        type = None

    # Retrieves all tutorials of the current user.

    profile = request.user.profile
    if type == "draft":
        user_tutorials = profile.get_draft_tutos()
    elif type == "public":
        user_tutorials = profile.get_public_tutos()
    else:
        user_tutorials = profile.get_tutos()
    return render_template("tutorial/index_member.html",
                           {"tutorials": user_tutorials, "type": type})


@can_read_now
@login_required
def articles(request):
    """Returns all articles of the authenticated user."""

    # The type indicate what the user would like to display. We can display
    # public, draft or all user's articles.

    try:
        type = request.GET["type"]
    except KeyError:
        type = None

    # Retrieves all articles of the current user.

    profile = request.user.profile
    if type == "draft":
        user_articles = profile.get_draft_articles()
    elif type == "public":
        user_articles = profile.get_public_articles()
    else:
        user_articles = profile.get_articles()
    return render_template("article/index_member.html",
                           {"articles": user_articles, "type": type})


@can_read_now
@login_required
def actions(request):
    """Show avaible actions for current user, like a customized homepage.

    This may be very temporary.

    """

    # TODO: Seriously improve this page, and see if cannot be merged in
    # zds.pages.views.home since it will be more coherent to give an enhanced
    # homepage for registered users

    return render_template("member/actions.html")


# settings for public profile

@can_write_and_read_now
@login_required
def settings_mini_profile(request, user_name):
    """Minimal settings of users for staff."""

    # extra information about the current user

    profile = Profile.objects.get(user__username=user_name)
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
                messages.error(request, "Une erreur est survenue.")
                return redirect(reverse("zds.member.views.settings_mini_profil"
                                        "e"))
            messages.success(request,
                             "Le profil a correctement été mis à jour.")
            return redirect(reverse("zds.member.views.details",
                                    args=[profile.user.username]))
        else:
            return render_to_response("member/settings_mini_profile.html", c,
                                      RequestContext(request))
    else:
        form = MiniProfileForm(initial={
            "biography": profile.biography,
            "site": profile.site,
            "avatar_url": profile.avatar_url,
            "sign": profile.sign,
        })
        c = {"form": form, "profile": profile}
        return render_to_response("member/settings_mini_profile.html", c,
                                  RequestContext(request))


@can_write_and_read_now
@login_required
def settings_profile(request):
    """User's settings about his personal information."""

    # extra information about the current user

    profile = request.user.profile
    if request.method == "POST":
        form = ProfileForm(request.POST)
        c = {"form": form}
        if form.is_valid():
            profile.biography = form.data["biography"]
            profile.site = form.data["site"]
            profile.show_email = "show_email" \
                in form.cleaned_data.get("options")
            profile.show_sign = "show_sign" in form.cleaned_data.get("options")
            profile.hover_or_click = "hover_or_click" \
                in form.cleaned_data.get("options")
            profile.email_for_answer = "email_for_answer" \
                in form.cleaned_data.get("options")
            profile.avatar_url = form.data["avatar_url"]
            profile.sign = form.data["sign"]

            # Save the profile and redirect the user to the configuration space
            # with message indicate the state of the operation

            try:
                profile.save()
            except:
                messages.error(request, "Une erreur est survenue.")
                return redirect(reverse("zds.member.views.settings_profile"))
            messages.success(request,
                             "Le profil a correctement été mis à jour.")
            return redirect(reverse("zds.member.views.settings_profile"))
        else:
            return render_to_response("member/settings_profile.html", c,
                                      RequestContext(request))
    else:
        form = ProfileForm(initial={
            "biography": profile.biography,
            "site": profile.site,
            "avatar_url": profile.avatar_url,
            "show_email": profile.show_email,
            "show_sign": profile.show_sign,
            "hover_or_click": profile.hover_or_click,
            "email_for_answer": profile.email_for_answer,
            "sign": profile.sign,
        })
        c = {"form": form}
        return render_to_response("member/settings_profile.html", c,
                                  RequestContext(request))


@can_write_and_read_now
@login_required
@require_POST
def update_avatar(request):
    """
    Update avatar from gallery.
    Specific method instead using settings_profile() to avoid to handle all required fields.
    """
    profile = request.user.profile
    form = ImageAsAvatarForm(request.POST)
    if form.is_valid():
        profile.avatar_url = form.data["avatar_url"]
        try:
            profile.save()
        except:
            messages.error(request, "Une erreur est survenue.")
            return redirect(reverse("zds.member.views.settings_profile"))
        messages.success(request, "L'avatar a correctement été mis à jour.")

    return redirect(reverse("zds.member.views.settings_profile"))


@can_write_and_read_now
@login_required
def settings_account(request):
    """User's settings about his account."""

    if request.method == "POST":
        form = ChangePasswordForm(request.user, request.POST)
        c = {"form": form}
        if form.is_valid():
            try:
                request.user.set_password(form.data["password_new"])
                request.user.save()
                messages.success(request, "Le mot de passe a bien été modifié."
                                 )
                return redirect(reverse("zds.member.views.settings_account"))
            except:
                messages.error(request, "Une erreur est survenue.")
                return redirect(reverse("zds.member.views.settings_account"))
        else:
            return render_to_response("member/settings_account.html", c,
                                      RequestContext(request))
    else:
        form = ChangePasswordForm(request.user)
        c = {"form": form}
        return render_to_response("member/settings_account.html", c,
                                  RequestContext(request))


@can_write_and_read_now
@login_required
def settings_user(request):
    """User's settings about his email."""

    profile = request.user.profile
    if request.method == "POST":
        form = ChangeUserForm(request.POST)
        c = {"form": form}
        if form.is_valid():
            email_exist = User.objects.filter(email=form.data["username_new"
                                                              ]).count()
            username_exist = \
                User.objects.filter(username=form.data["username_new"]).count()
            old = User.objects.filter(pk=request.user.pk).all()[0]
            if form.data["username_new"] and username_exist > 0:
                raise Http404
            elif form.data["username_new"]:
                if form.data["username_new"].strip() != "":
                    old.username = form.data["username_new"]
            if form.data["email_new"] and email_exist > 0:
                raise Http404
            elif form.data["email_new"]:
                if form.data["email_new"].strip() != "":
                    old.email = form.data["email_new"]
            old.save()
            return redirect(profile.get_absolute_url())
        else:
            return render_to_response("member/settings_user.html", c,
                                      RequestContext(request))
    else:
        form = ChangeUserForm()
        c = {"form": form}
        return render_to_response("member/settings_user.html", c,
                                  RequestContext(request))


@can_read_now
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

                    # redirect the user if needed

                    try:
                        return redirect(next_page)
                    except:
                        return redirect(reverse("zds.pages.views.home"))
                else:
                    messages.error(request,
                                   "Vous n'êtes pas autorisé à vous connecter "
                                   "sur le site, vous avez été banni par un "
                                   "modérateur")
            else:
                messages.error(request,
                               "Vous n'avez pas encore activé votre compte, "
                               "vous devez le faire pour pouvoir vous "
                               "connecter sur le site. Regardez dans vos "
                               "mails : " + str(user.email))
        else:
            messages.error(request,
                           "Les identifiants fournis ne sont pas valides")
    form = LoginForm()
    form.helper.form_action = reverse("zds.member.views.login_view") \
        + "?next=" + str(next_page)
    csrf_tk["error"] = error
    csrf_tk["form"] = form
    csrf_tk["next_page"] = next_page
    return render_template("member/login.html",
                           {"form": form,
                            "csrf_tk": csrf_tk,
                            "next_page": next_page})


@login_required
@require_POST
def logout_view(request):
    """Log out user."""

    logout(request)
    request.session.clear()
    return redirect(reverse("zds.pages.views.home"))


def register_view(request):
    """Register a new user."""

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            data = form.data
            user = User.objects.create_user(data["username"], data["email"],
                                            data["password"])
            user.is_active = False
            user.save()
            profile = Profile(user=user, show_email=False, show_sign=True,
                              hover_or_click=True, email_for_answer=False)
            profile.last_ip_address = get_client_ip(request)
            profile.save()
            user.backend = "django.contrib.auth.backends.ModelBackend"

            # Generate a valid token during one hour.

            uuidToken = str(uuid.uuid4())
            date_end = datetime.now() + timedelta(days=0, hours=1, minutes=0,
                                                  seconds=0)
            token = TokenRegister(user=user, token=uuidToken,
                                  date_end=date_end)
            token.save()

            # send email

            subject = "ZDS - Confirmation d'inscription"
            from_email = "ZesteDeSavoir <noreply@zestedesavoir.com>"
            message_html = get_template("email/confirm_register.html").render(Context(
                {"username": user.username, "url": settings.SITE_URL + token.get_absolute_url()}))
            message_txt = get_template("email/confirm_register.txt") .render(Context(
                {"username": user.username, "url": settings.SITE_URL + token.get_absolute_url()}))
            msg = EmailMultiAlternatives(subject, message_txt, from_email,
                                         [user.email])
            msg.attach_alternative(message_html, "text/html")
            try:
                msg.send()
            except:
                msg = None
            return render_template("member/register_success.html", {})
        else:
            return render_template("member/register.html", {"form": form})
    form = RegisterForm()
    return render_template("member/register.html", {"form": form})


@can_read_now
def forgot_password(request):
    """If the user forgot his password, he can have a new one."""

    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            data = form.data
            username = data["username"]
            usr = get_object_or_404(User, username=username)

            # Generate a valid token during one hour.

            uuidToken = str(uuid.uuid4())
            date_end = datetime.now() + timedelta(days=0, hours=1, minutes=0,
                                                  seconds=0)
            token = TokenForgotPassword(user=usr, token=uuidToken,
                                        date_end=date_end)
            token.save()

            # send email

            subject = "ZDS - Mot de passe oublié"
            from_email = "ZesteDeSavoir <noreply@zestedesavoir.com>"
            message_html = get_template("email/confirm_forgot_password.html").render(Context(
                {"username": usr.username, "url": settings.SITE_URL + token.get_absolute_url()}))
            message_txt = get_template("email/confirm_forgot_password.txt") .render(Context(
                {"username": usr.username, "url": settings.SITE_URL + token.get_absolute_url()}))
            msg = EmailMultiAlternatives(subject, message_txt, from_email,
                                         [usr.email])
            msg.attach_alternative(message_html, "text/html")
            msg.send()
            return render_template("member/forgot_password_success.html")
        else:
            return render_template("member/forgot_password.html",
                                   {"form": form})
    form = ForgotPasswordForm()
    return render_template("member/forgot_password.html", {"form": form})


@can_read_now
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
                return render_template("member/new_password_failed.html")
            token.user.set_password(password)
            token.user.save()
            token.delete()
            return render_template("member/new_password_success.html")
        else:
            return render_template("member/new_password.html", {"form": form})
    form = NewPasswordForm(identifier=token.user.username)
    return render_template("member/new_password.html", {"form": form})


def active_account(request):
    """Active token for a user."""

    try:
        token = request.GET["token"]
    except KeyError:
        return redirect(reverse("zds.pages.views.home"))
    token = get_object_or_404(TokenRegister, token=token)
    usr = token.user

    # User can't confirm his request if it is too late.

    if datetime.now() > token.date_end:
        return render_template("member/token_account_failed.html",
                               {"token": token})
    usr.is_active = True
    usr.save()

    # send register message

    bot = get_object_or_404(User, username=settings.BOT_ACCOUNT)
    msg = \
        u"""Bonjour **{0}**,

Ton compte a été activé, et tu es donc officiellement u\
umembre de la communauté de ZesteDeSavoir.

ZesteDeSavoir est une communauté dont le but est de diffuser des u\
uconnaissances au plus grand nombre.

Sur ce site, tu trouveras un ensemble de [tutoriels]({1}) dans u\
uplusieurs domaines et plus particulièrement autour de l'informatique u\
uet des sciences. Tu y retrouveras aussi des [articles]({2}) u\
utraitant de sujets d'actualités ou non, qui, tout comme les tutoriels, su\
uont écrits par des [membres]({3}) de la communauté. u\
uPendant tes lectures et ton apprentissage, si jamais tu as des u\
uquestions à poser, tu retrouveras sur les [forums]({4}) des personnes u\
uprêtes à te filer un coup de main et ainsi t'éviter de passer u\
uplusieurs heures sur un problème.

L'ensemble du contenu disponible sur le site est et sera toujours gratuit, u\
ucar la communauté de ZesteDeSavoir est attachée aux valeurs du libre u\
upartage et désire apporter le savoir à tout le monde quelques soit ses moyens.

En espérant que tu t'y plaira ici, u\
uje te laisse maintenant faire le tour""".format(usr.username,
                                                 settings.SITE_URL + reverse("zds.tutorial.views.index"),
                                                 settings.SITE_URL + reverse("zds.article.views.index"),
                                                 settings.SITE_URL + reverse("zds.member.views.index"),
                                                 settings.SITE_URL + reverse("zds.forum.views.index"))
    send_mp(
        bot,
        [usr],
        u"Bienvenue sur ZesteDeSavoir",
        u"Le manuel du nouveau membre",
        msg,
        True,
        True,
        False,
    )
    return render_template("member/token_account_success.html", {"usr": usr})
    token.delete()


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

    subject = "ZDS - Confirmation d'inscription"
    from_email = "ZesteDeSavoir <noreply@zestedesavoir.com>"
    message_html = get_template("email/confirm_register.html"
                                ) \
        .render(Context({"username": token.user.username,
                         "url": settings.SITE_URL + token.get_absolute_url()}))
    message_txt = get_template("email/confirm_register.txt"
                               ) \
        .render(Context({"username": token.user.username,
                         "url": settings.SITE_URL + token.get_absolute_url()}))
    msg = EmailMultiAlternatives(subject, message_txt, from_email,
                                 [token.user.email])
    msg.attach_alternative(message_html, "text/html")
    try:
        msg.send()
    except:
        msg = None
    return render_template("member/register_success.html", {})


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


@can_read_now
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
                     "Le tutoriel a bien été lié au u\
                     umembre {0}".format(profile.user.username))
    return redirect(reverse("zds.member.views.details",
                            args=[profile.user.username]))


@can_read_now
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
                     "Le tutoriel a bien été retiré u\
                     uau membre {0}".format(profile.user.username))
    return redirect(reverse("zds.member.views.details",
                            args=[profile.user.username]))
