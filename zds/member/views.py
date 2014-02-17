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
from django.template.loader import get_template
from django.core.mail import EmailMultiAlternatives
from django.template import Context
import os
import uuid

import pygal
from zds.member.decorator import can_read_now, can_write_and_read_now
from zds.tutorial.models import Tutorial
from zds.utils import render_template
from zds.utils.tokens import generate_token

from .forms import LoginForm, ProfileForm, RegisterForm, ChangePasswordForm, \
    ChangeUserForm, ForgotPasswordForm, NewPasswordForm
from .models import Profile, TokenForgotPassword, Ban, TokenRegister

@can_read_now
def index(request):
    '''Displays the list of registered users'''
    members = User.objects.order_by('date_joined')
    return render_template('member/index.html', {
        'members': members
    })

@can_read_now
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
    dot_chart.x_labels = [u'Dimanche', u'Lundi', u'Mardi', u'Mercredi', u'Jeudi', u'Vendredi', u'Samedi']
    dot_chart.show_legend = False
    
    dates = date_to_chart(profile.get_posts()) 
    
    for i in range(0,24):
        dot_chart.add(str(i)+' h', dates[(i+1)%24])
    img_path = os.path.join(settings.MEDIA_ROOT, 'pygal')
    if not os.path.isdir(img_path) :
        os.makedirs(img_path, mode=0777)
    fchart = os.path.join(img_path, 'mod-{}.svg'.format(str(usr.pk)))
    
    dot_chart.render_to_file(fchart)

    return render_template('member/profile.html', {
        'usr': usr, 'profile': profile, 'bans': bans
    })

@can_write_and_read_now
@login_required
def modify_profile(request, user_pk):
    '''Modifies sanction of a user if there is a POST request'''
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

@can_read_now
@login_required
def tutorials(request):
    '''Returns all tutorials of the authenticated user'''
    profile = Profile.objects.get(user=request.user)

    user_tutorials = profile.get_tutos()
    
    return render_template('member/publications.html', {
        'user_tutorials': user_tutorials,
    })

@can_read_now
@login_required
def articles(request):
    '''Returns all articles of the authenticated user'''
    # The type indicate what the user would like to display.
    # We can display public, draft or all user's articles.
    try:
        type = request.GET['type']
    except KeyError:
        type = None

    # Retrieves all articles of the current user.
    profile = Profile.objects.get(user=request.user)
    if type == 'draft':
        user_articles = profile.get_draft_articles()
    elif type == 'public':
        user_articles = profile.get_public_articles()
    else:
        user_articles = profile.get_articles()

    return render_template('article/index_member.html', {
        'articles': user_articles,
    })

# settings for public profile

@can_write_and_read_now
@login_required
def settings_profile(request):
    '''User's settings about his personal information'''
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
                return redirect(reverse('zds.member.views.settings_profile'))

            messages.success(
                request, 'Le profil a correctement été mis à jour.')
            return redirect(reverse('zds.member.views.settings_profile'))
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

@can_write_and_read_now
@login_required
def settings_account(request):
    '''User's settings about his account'''
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
                return redirect(reverse('zds.member.views.settings_account'))
            except:
                messages.error(request, 'Une erreur est survenue.')
                return redirect(reverse('zds.member.views.settings_account'))
        else:
            return render_to_response('member/settings_account.html', c, RequestContext(request))
    else:
        form = ChangePasswordForm(request.user)
        c = {
            'form': form,
        }
        return render_to_response('member/settings_account.html', c, RequestContext(request))

@can_write_and_read_now
@login_required
def settings_user(request):
    '''User's settings about his email'''
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

@can_read_now
def login_view(request):
    '''Log in user'''
    csrf_tk = {}
    csrf_tk.update(csrf(request))

    error = False

    # Redirecting user once logged in?
    if request.GET.has_key('next'):
        next_page = request.GET['next']
    else:
        next_page = None

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
                    # Annotation isn't possible for this method. So we check
                    # if the user is ban when we retrieved him.
                    if not profile.can_read_now():
                        logout_view(request)
                except :
                    profile= None

                # redirect the user if needed
                try:
                    return redirect(next_page)
                except:
                    return redirect(reverse('zds.pages.views.home'))
            else:
                error = 'Les identifiants fournis ne sont pas valides'
        else:
            error = 'Veuillez spécifier votre identifiant et votre mot de passe'
    else:

        form = LoginForm()
    csrf_tk['error'] = error
    csrf_tk['form'] = form
    csrf_tk['next_page'] = next_page
    return render_template('member/login.html', csrf_tk)

@login_required
def logout_view(request):
    '''Log out user'''
    logout(request)
    request.session.clear()
    return redirect(reverse('zds.pages.views.home'))


def register_view(request):
    '''Register a new user'''
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            data = form.data
            user = User.objects.create_user(
                data['username'],
                data['email'],
                data['password'])
            user.is_active=False
            user.save()
            profile = Profile(user=user, show_email=False, show_sign=True, hover_or_click=True)
            profile.last_ip_address = get_client_ip(request)
            profile.save()
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            
            # Generate a valid token during one hour.
            uuidToken = str(uuid.uuid4())
            date_end = datetime.now() + timedelta(days=0, hours=1, minutes=0, seconds=0)
            token = TokenRegister(user=user, token = uuidToken, date_end = date_end)
            token.save()

            #send email
            subject = "ZDS - Confirmation d'inscription"
            from_email = 'ZesteDeSavoir <noreply@zestedesavoir.com>'
            message_html = get_template('email/confirm_register.html').render(
                            Context({
                                'username': user.username,
                                'url': settings.SITE_URL+token.get_absolute_url(),
                            })
                        )
            message_txt = get_template('email/confirm_register.txt').render(
                            Context({
                                'username': user.username,
                                'url': settings.SITE_URL+token.get_absolute_url(),
                            })
                        )

            msg = EmailMultiAlternatives(subject, message_txt, from_email, [user.email])
            msg.attach_alternative(message_html, "text/html")
            msg.send()
            
            return render_template('member/register_success.html', {
                'user': user
            })


    form = RegisterForm()
    return render_template('member/register.html', {
        'form': form
    })

@can_read_now
def forgot_password(request):
    '''If the user forgot his password, he can have a new one'''
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            data = form.data
            username = data['username']

            usr = get_object_or_404(User, username=username)

            # Generate a valid token during one hour.
            uuidToken = str(uuid.uuid4())
            date_end = datetime.now() + timedelta(days=0, hours=1, minutes=0, seconds=0)
            token = TokenForgotPassword(user=usr, token = uuidToken, date_end = date_end)
            token.save()

            #send email
            subject = "ZDS - Mot de passe oublié"
            from_email = 'ZesteDeSavoir <noreply@zestedesavoir.com>'
            message_html = get_template('email/confirm_forgot_password.html').render(
                            Context({
                                'username': usr.username,
                                'url': settings.SITE_URL+token.get_absolute_url(),
                            })
                        )
            message_txt = get_template('email/confirm_forgot_password.txt').render(
                            Context({
                                'username': usr.username,
                                'url': settings.SITE_URL+token.get_absolute_url(),
                            })
                        )
                
            msg = EmailMultiAlternatives(subject, message_txt, from_email, [usr.email])
            msg.attach_alternative(message_html, "text/html")
            msg.send()
            return render_template('member/forgot_password_success.html')
        else:
            return render_template('member/forgot_password.html', {'form': form})

    form = ForgotPasswordForm()
    return render_template('member/forgot_password.html', {
        'form': form
    })

@can_read_now
def new_password(request):
    '''Create a new password for a user'''
    try:
        token = request.GET['token']
    except KeyError:
        return redirect(reverse('zds.pages.views.home'))

    if request.method == 'POST':
        form = NewPasswordForm(request.POST)
        if form.is_valid():
            data = form.data
            password = data['password']

            token = get_object_or_404(TokenForgotPassword, token = token)

            # User can't confirm his request if it is too late.
            if datetime.now() > token.date_end:
                return render_template('member/new_password_failed.html')

            token.user.set_password(password)
            token.user.save()
            token.delete()

            return render_template('member/new_password_success.html')
        else:
            return render_template('member/new_password.html', {'form': form})

    form = NewPasswordForm()
    return render_template('member/new_password.html', {
        'form': form
    })

def active_account(request):
    '''Active token for a user'''
    try:
        token = request.GET['token']
    except KeyError:
        return redirect(reverse('zds.pages.views.home'))

    token = get_object_or_404(TokenRegister, token = token)
    usr = token.user
    # User can't confirm his request if it is too late.
    if datetime.now() > token.date_end:
        return render_template('member/token_account_failed.html')    
    
    usr.is_active = True
    usr.save()
    
    token.delete()
    
    
    return render_template('member/token_account_success.html', {'user':usr})
    
def get_client_ip(request):
    '''Retrieve the real IP address of the client'''
    if request.META.has_key('HTTP_X_REAL_IP'): # nginx
        return request.META.get('HTTP_X_REAL_IP')
    elif request.META.has_key('REMOTE_ADDR'): # other
        return request.META.get('REMOTE_ADDR')
    else: # should never happend
        return '0.0.0.0'

def date_to_chart(posts):
    lst = 24*[0]
    for i in range(len(lst)):
        lst[i] = 7*[0]
    
    for post in posts:
        t = post.pubdate.timetuple()
        lst[t.tm_hour+1][(t.tm_wday+1)%7]=lst[t.tm_hour+1][(t.tm_wday+1)%7]+1
        
    return lst
