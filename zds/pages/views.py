# coding: utf-8

import os.path
import random
from django.contrib import messages

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.shortcuts import render
from zds import settings

from zds.forum.models import Topic
from zds.member.decorator import can_write_and_read_now
from zds.featured.models import FeaturedResource, FeaturedMessage
from zds.pages.forms import AssocSubscribeForm
from zds.settings import BASE_DIR
from zds.tutorialv2.models.models_database import PublishableContent, PublishedContent
from zds.utils.models import Alert
from django.utils.translation import ugettext_lazy as _


def home(request):
    """Display the home page with last topics added."""

    tutos = PublishableContent.objects.get_last_tutorials()
    articles = PublishableContent.objects.get_last_articles()

    try:
        with open(os.path.join(BASE_DIR, 'quotes.txt'), 'r') as quotes_file:
            quote = random.choice(quotes_file.readlines())
    except IOError:
        quote = settings.ZDS_APP['site']['slogan']

    try:
        with open(os.path.join(BASE_DIR, 'suggestions.txt'), 'r') as suggestions_file:
            suggestions = ', '.join(random.sample(suggestions_file.readlines(), 5)) + '...'
    except IOError:
        suggestions = 'Mathématiques, Droit, UDK, Langues, Python...'

    return render(request, 'home.html', {
        'featured_message': FeaturedMessage.objects.get_last_message(),
        'last_tutorials': tutos,
        'last_articles': articles,
        'last_featured_resources': FeaturedResource.objects.get_last_featured(),
        'last_topics': Topic.objects.get_last_topics(),
        'tutorials_count': PublishedContent.objects.get_tutorials_count(),
        'quote': quote.replace('\n', ''),
        'suggestions': suggestions,
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

            # Send email
            subject = _(u"Demande d'adhésion de {}").format(user.username)
            from_email = "{} <{}>".format(settings.ZDS_APP['site']['litteral_name'],
                                          settings.ZDS_APP['site']['email_noreply'])
            context = {
                'full_name': data['full_name'],
                'email': data['email'],
                'naissance': data['naissance'],
                'adresse': data['adresse'],
                'justification': data['justification'],
                'username': user.username,
                'profile_url': settings.ZDS_APP['site']['url'] + reverse('member-detail',
                                                                         kwargs={'user_name': user.username}),
                'bot_name': settings.ZDS_APP['member']['bot_account'],
                'asso_name': settings.ZDS_APP['site']['association']['name']
            }
            message_html = render_to_string("email/pages/assoc_subscribe.html", context)
            message_txt = render_to_string("email/pages/assoc_subscribe.txt", context)

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
                messages.error(request, _(u"Une erreur est survenue."))

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
    """Cookies explanation page."""
    return render(request, 'pages/cookies.html')


@can_write_and_read_now
@login_required
def alerts(request):
    # only staff can see alerts list
    if not request.user.has_perm('forum.change_post'):
        raise PermissionDenied

    all_alerts = Alert.objects.all().order_by('-pubdate')

    return render(request, 'pages/alerts.html', {
        'alerts': all_alerts,
    })


def custom_error_500(request):
    """Custom view for 500 errors"""
    return render(request, '500.html')
