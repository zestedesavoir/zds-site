# coding: utf-8
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, SiteProfileNotAvailable
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import redirect, get_object_or_404, render_to_response
from django.template import RequestContext
import os
import uuid

import pygal
from zds.tutorial.models import Tutorial
from zds.utils import render_template
from zds.utils.tokens import generate_token

from .forms import LoginForm, ProfileForm, RegisterForm, ChangePasswordForm, \
    ChangeUserForm
from .models import Profile, Ban


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
    #       zds.pages.views.home since it will be more coherent to give an
    #       enhanced homepage for registered users

    return render_template('member/actions.html')


def details(request, user_name):
    '''Displays details about a profile'''
    usr = get_object_or_404(User, username=user_name)

    try:
        profile = usr.get_profile()
        bans= Ban.objects.filter(user=usr).order_by('-pubdate')
        
    except SiteProfileNotAvailable:
        raise Http404
    
    #refresh moderation chart
    dot_chart = pygal.Dot(x_label_rotation=30)
    dot_chart.title = u'Messages postés par période'
    dot_chart.x_labels = [u'Lundi', u'Mardi', u'Mercredi', u'Jeudi', u'Vendredi', u'Samedi', u'Dimanche']
    dot_chart.show_legend = False
    
    dates = date_to_chart(profile.get_posts())
    
    for i in range(0,24):
        dot_chart.add(str(i+1)+' h', dates[i])
    
    fchart = os.path.join(settings.MEDIA_ROOT, os.path.join('pygal', 'mod-{}.svg'.format(str(usr.pk))))
    
    dot_chart.render_to_file(fchart)
    

    return render_template('member/profile.html', {
        'usr': usr, 'profile': profile, 'bans': bans
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
            profile.show_sign = 'show_sign' in data
            profile.hover_or_click = 'hover_or_click' in data

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

@login_required
def modify_profile(request, user_pk):
    profile = get_object_or_404(Profile, user__pk=user_pk)
    if request.method == 'POST':
        ban= Ban()
        ban.moderator=request.user
        ban.user=profile.user
        ban.pubdate = datetime.now()
        
        if 'ls' in request.POST:
            profile.can_write=False
            ban.type='Lecture Seule'
            ban.text = request.POST['ls-text']
        if 'ls-temp' in request.POST:
            ban.type='Lecture Seule Temporaire'
            ban.text = request.POST['ls-temp-text']
            profile.can_write=False
            profile.end_ban_write = datetime.now() + timedelta(days=int(request.POST['ls-jrs']),hours=0, minutes=0, seconds=0) 
        if 'ban-temp' in request.POST:
            ban.type='Ban Temporaire'
            ban.text = request.POST['ban-temp-text']
            profile.can_read=False
            profile.end_ban_read = datetime.now() + timedelta(days=int(request.POST['ban-jrs']),hours=0, minutes=0, seconds=0)
        if 'ban' in request.POST:
            ban.type='Ban définitif'
            ban.text = request.POST['ban-text']
            profile.can_read=False
        if 'un-ls' in request.POST:
            ban.type='Authorisation d\'écrire'
            ban.text = request.POST['unls-text']
            profile.can_write=True
        if 'un-ban' in request.POST:
            ban.type='Authorisation de se connecter'
            ban.text = request.POST['unban-text']
            profile.can_read=True
            
        profile.save()
        ban.save()
        
    return redirect(profile.get_absolute_url())
    
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
                
                try:
                    profile = get_object_or_404(Profile, user=request.user)
                    profile.last_ip_address = get_client_ip(request)
                    profile.save()
                    if not profile.can_read_now():
                        logout_view(request)
                except :
                    profile= None
                return redirect(reverse('zds.pages.views.home'))
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
    return redirect(reverse('zds.pages.views.home'))


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            data = form.data
            user = User.objects.create_user(
                data['username'],
                data['email'],
                data['password'])
            profile = Profile(user=user, show_email=False, show_sign=True, hover_or_click=True)
            profile.last_ip_address = get_client_ip(request)
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
            profile.show_sign = 'show_sign' in form.data
            profile.hover_or_click = 'hover_or_click' in form.data
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
            'show_sign': profile.show_sign,
            'hover_or_click': profile.hover_or_click,
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
def settings_user(request):
    profile = get_object_or_404(Profile, user__pk=request.user.pk)
    
    if request.method == 'POST':
        form = ChangeUserForm(request.user, request.POST)
        c = {
            'form': form,
        }
        if form.is_valid():
            email_exist = User.objects.filter(email = form.data['username_new']).count()
            username_exist = User.objects.filter(username = form.data['username_new']).count()
            
            old = User.objects.filter(pk = request.user.pk).all()[0]
            if form.data['username_new'] and username_exist > 0:
                raise Http404
            elif form.data['username_new']:
                if form.data['username_new'].strip() != '':
                    old.username = form.data['username_new']
                
            if form.data['email_new'] and email_exist > 0:
                raise Http404
            elif form.data['email_new']:
                if form.data['email_new'].strip() != '':
                    old.email = form.data['email_new']
                
            old.save()
            
            return redirect(profile.get_absolute_url())
        
        else:
            return render_to_response('member/settings_user.html', c, RequestContext(request))
    else:
        form = ChangeUserForm(request.user)
        c = {
            'form': form,
        }
        return render_to_response('member/settings_user.html', c, RequestContext(request))

@login_required
def publications(request):
    if request.user.is_authenticated():
        user_tutorials = Tutorial.objects.filter(authors__in = [request.user])
    else:
        user_tutorials = None    
    c = {
         'user_tutorials': user_tutorials,
    }
    return render_to_response('member/publications.html', c, RequestContext(request))


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def date_to_chart(posts):
    lst = 24*[0]
    for i in range(len(lst)):
        lst[i] = 7*[0]
    
    for post in posts:
        t = post.pubdate.timetuple()
        lst[t.tm_hour+1][t.tm_wday+1]=lst[t.tm_hour+1][t.tm_wday+1]+1
        
    return lst
