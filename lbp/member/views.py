# coding: utf-8

from django.shortcuts import redirect, get_object_or_404, render_to_response
from django.http import Http404

from django.contrib.auth.models import User, SiteProfileNotAvailable
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

from django.core.context_processors import csrf
from django.core.urlresolvers import reverse
from django.template import RequestContext

from lbp.utils.tokens import generate_token
from lbp.utils import render_template

from .models import Profile
from lbp.news.models import News
from .forms import LoginForm, ProfileForm, RegisterForm, ChangePasswordForm


def index(request):
    '''Displays the list of registered users'''
    members = User.objects.order_by('date_joined')
    return render_template('member/index.html', {
        'members': members
    })


@login_required
def actions(request):
    '''
    Show avaible actions for current user, like a customized homepage.
    This may be very temporary.
    '''

    # TODO: Seriously improve this page, and see if cannot be merged in
    #       lbp.pages.views.home since it will be more coherent to give an
    #       enhanced homepage for registered users

    return render_template('member/actions.html')


def details(request, user_name):
    '''Displays details about a profile'''
    usr = get_object_or_404(User, username=user_name)

    try:
        profile = usr.get_profile()
    except SiteProfileNotAvailable:
        raise Http404

    return render_template('member/profile.html', {
        'usr': usr, 'profile': profile
    })


@login_required
def edit_profile(request):
    try:
        profile_pk = int(request.GET['profil'])
        profile = get_object_or_404(Profile, pk=profile_pk)
    except KeyError:
        profile = get_object_or_404(Profile, user=request.user)

    # Making sure the user is allowed to do that
    if not request.user == profile.user:
        raise Http404
    if request.method == 'POST':
        form = ProfileForm(request.POST)
        if form.is_valid():
            data = form.data
            profile.biography = data['biography']
            profile.site = data['site']
            profile.user.email = data['email']
            profile.show_email = 'show_email' in data

            # Save the user and it's associated profile
            profile.user.save()
            profile.save()
            return redirect(profile.get_absolute_url())
        else:
            raise Http404
    else:
        return render_template('member/edit_profile.html', {
            'profile': profile
        })


def login_view(request):
    csrf_tk = {}
    csrf_tk.update(csrf(request))

    error = False
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                request.session['get_token'] = generate_token()
                if not 'remember' in request.POST:
                    request.session.set_expiry(0)
                return redirect(reverse('lbp.pages.views.home'))
            else:
                error = 'Les identifiants fournis ne sont pas valides'
        else:
            error = 'Veuillez spécifier votre identifiant et votre mot de passe'
    else:
        form = LoginForm()
    csrf_tk['error'] = error
    csrf_tk['form'] = form

    return render_template('member/login.html', csrf_tk)


@login_required
def logout_view(request):
    logout(request)
    request.session.clear()
    return redirect(reverse('lbp.pages.views.home'))


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            data = form.data
            user = User.objects.create_user(
                data['username'],
                data['email'],
                data['password'])
            profile = Profile(user=user, show_email=False)
            profile.save()
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            return render_template('member/register_success.html')
        else:
            return render_template('member/register.html', {'form': form})

    form = RegisterForm()
    return render_template('member/register.html', {
        'form': form
    })


# settings for public profile

@login_required
def settings_profile(request):
    # extra information about the current user
    profile = Profile.objects.get(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.user, request.POST)
        c = {
            'form': form,
        }
        if form.is_valid():
            profile.biography = form.data['biography']
            profile.site = form.data['site']
            profile.show_email = 'show_email' in form.data
            profile.avatar_url = form.data['avatar_url']
            profile.sign = form.data['sign']

            # Save the profile
            # and redirect the user to the configuration space
            # with message indicate the state of the operation
            try:
                profile.save()
            except:
                messages.error(request, 'Une erreur est survenue.')
                return redirect('/membres/parametres/profil')

            messages.success(
                request, 'Le profil a correctement été mis à jour.')
            return redirect('/membres/parametres/profil')
        else:
            return render_to_response('member/settings_profile.html', c, RequestContext(request))
    else:
        form = ProfileForm(request.user, initial={
            'biography': profile.biography,
            'site': profile.site,
            'avatar_url': profile.avatar_url,
            'show_email': profile.show_email,
            'sign': profile.sign}
        )
        c = {
            'form': form
        }
        return render_to_response('member/settings_profile.html', c, RequestContext(request))


@login_required
def settings_account(request):
    if request.method == 'POST':
        form = ChangePasswordForm(request.user, request.POST)
        c = {
            'form': form,
        }
        if form.is_valid():
            try:
                request.user.set_password(form.data['password_new'])
                request.user.save()
                messages.success(
                    request, 'Le mot de passe a bien été modifié.')
                return redirect('/membres/parametres/profil')
            except:
                messages.error(request, 'Une erreur est survenue.')
                return redirect('/membres/parametres/profil')
        else:
            return render_to_response('member/settings_account.html', c, RequestContext(request))
    else:
        form = ChangePasswordForm(request.user)
        c = {
            'form': form,
        }
        return render_to_response('member/settings_account.html', c, RequestContext(request))


@login_required
def publications(request):
    if request.user.is_authenticated():
        user_news = News.objects.filter(authors__in = [request.user])
    else:
        user_news = None
        
    c = {
         'user_news': user_news
    }
    return render_to_response('member/publications.html', c, RequestContext(request))
