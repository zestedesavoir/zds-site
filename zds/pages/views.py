# coding: utf-8

import os.path
import random
from django.contrib import messages

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.template import Context
from django.template.loader import get_template
from django.shortcuts import render
from zds import settings

from zds.article.models import get_last_articles
from zds.member.decorator import can_write_and_read_now
from zds.pages.forms import AssocSubscribeForm
from zds.settings import SITE_ROOT
from zds.tutorial.models import get_last_tutorials
from zds.utils.models import Alert
from django.utils.translation import ugettext as _


def home(request):
    """Display the home page with last topics added."""

    tutos = []
    for tuto in get_last_tutorials():
        data = tuto.load_json_for_public()
        tuto.load_dic(data)
        tutos.append(data)

    articles = []
    for article in get_last_articles():
        data = article.load_json_for_public()
        data = article.load_dic(data)
        articles.append(data)

    try:
        with open(os.path.join(SITE_ROOT, 'quotes.txt'), 'r') as fh:
            quote = random.choice(fh.readlines())
    except IOError:
        quote = settings.ZDS_APP['site']['slogan']

    return render(request, 'home.html', {
        'last_tutorials': tutos,
        'last_articles': articles,
        'quote': quote,
    })


def index(request):
    return render(request, 'pages/index.html')


def about(request):
    """Display many informations about the website."""
    return render(request, 'pages/about.html')


@can_write_and_read_now
@login_required
def assoc_subscribe(request):
    if request.method == "POST":
        form = AssocSubscribeForm(request.POST)
        if form.is_valid():
            user = request.user
            data = form.data
            context = {
                'full_name': data['full_name'],
                'email': data['email'],
                'naissance': data['naissance'],
                'adresse': data['adresse'],
                'justification': data['justification'],
                'username': user.username,
                'profile_url': settings.ZDS_APP['site']['url'] + reverse('member-detail',
                                                                         kwargs={'user_name': user.username})
            }
            # Send email
            subject = "Demande d'adhésion de {}".format(user.username)
            from_email = "{} <{}>".format(settings.ZDS_APP['site']['litteral_name'],
                                          settings.ZDS_APP['site']['email_noreply'])
            message_html = get_template("email/assoc/subscribe.html").render(Context(context))
            message_txt = get_template("email/assoc/subscribe.txt") .render(Context(context))
            msg = EmailMultiAlternatives(
                subject,
                message_txt,
                from_email,
                [settings.ZDS_APP['site']['association']['email_ca']])
            msg.attach_alternative(message_html, "text/html")
            try:
                msg.send()
                messages.success(request, _(u"Votre demande d'adhésion a bien été envoyée et va être étudiée."))
            except:
                msg = None
                messages.error(request, u"Une erreur est survenue.")

            # reset the form after successfull validation
            form = AssocSubscribeForm()
        return render(request, "pages/assoc_subscribe.html", {"form": form})

    form = AssocSubscribeForm(initial={'email': request.user.email})
    return render(request, "pages/assoc_subscribe.html", {"form": form})


def association(request):
    """Display association's presentation."""
    return render(request, 'pages/association.html')


def contact(request):
    """Display contact page."""
    staffs = User.objects.filter(
        groups__in=Group.objects.filter(
            name__contains='staff')).all()
    devs = User.objects.filter(
        groups__in=Group.objects.filter(
            name__contains='dev')).all()
    return render(request, 'pages/contact.html', {
        'staffs': staffs,
        'devs': devs
    })


def eula(request):
    """End-User Licence Agreement."""
    return render(request, 'pages/eula.html')


def cookies(request):
    """Cookies explaination page."""
    return render(request, 'pages/cookies.html')


@can_write_and_read_now
@login_required
def alerts(request):
    # only staff can see alerts list
    if not request.user.has_perm('forum.change_post'):
        raise PermissionDenied

    alerts = Alert.objects.all().order_by('-pubdate')

    return render(request, 'pages/alerts.html', {
        'alerts': alerts,
    })


def custom_error_500(request):
    """Custom view for 500 errors"""
    return render(request, '500.html')
