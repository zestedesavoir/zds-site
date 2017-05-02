# coding: utf-8

import os.path
import random

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView
from django.views.generic.edit import FormView

from zds.featured.models import FeaturedResource, FeaturedMessage
from zds.forum.models import Forum, Topic
from zds.member.decorator import can_write_and_read_now
from zds.pages.forms import AssocSubscribeForm
from zds.pages.models import GroupContact
from zds.settings import BASE_DIR, ZDS_APP
from zds.searchv2.forms import SearchForm
from zds.tutorialv2.models.models_database import PublishableContent, PublishedContent
from zds.utils.forums import create_topic
from zds.utils.models import Alert


def home(request):
    """Display the home page with last topics added."""

    tutos = PublishableContent.objects.get_last_tutorials()
    articles = PublishableContent.objects.get_last_articles()
    opinions = PublishableContent.objects.get_last_opinions()

    try:
        with open(os.path.join(BASE_DIR, 'quotes.txt'), 'r') as quotes_file:
            quote = random.choice(quotes_file.readlines())
    except IOError:
        quote = ZDS_APP['site']['slogan']

    return render(request, 'home.html', {
        'featured_message': FeaturedMessage.objects.get_last_message(),
        'last_tutorials': tutos,
        'last_articles': articles,
        'last_opinions': opinions,
        'last_featured_resources': FeaturedResource.objects.get_last_featured(),
        'last_topics': Topic.objects.get_last_topics(),
        'contents_count': PublishedContent.objects.get_contents_count(),
        'quote': quote.replace('\n', ''),
        'search_form': SearchForm(initial={}),
    })


def index(request):
    return render(request, 'pages/index.html')


def about(request):
    """Display many informations about the website."""
    return render(request, 'pages/about.html')


class AssocSubscribeView(FormView):

    template_name = 'pages/assoc_subscribe.html'
    form_class = AssocSubscribeForm

    def form_valid(self, form):
        user = self.request.user
        data = form.data

        bot = get_object_or_404(User, username=ZDS_APP['member']['bot_account'])
        forum = get_object_or_404(Forum, pk=ZDS_APP['site']['association']['forum_ca_pk'])

        # create the topic
        title = _(u'Demande d\'adhésion de {}').format(user.username)
        subtitle = _(u'Sujet créé automatiquement pour la demande d\'adhésion à l\'association du membre {} via le form'
                     u'ulaire du site').format(user.username)
        context = {
            'full_name': data['full_name'],
            'email': data['email'],
            'birthdate': data['birthdate'],
            'address': data['address'],
            'justification': data['justification'],
            'username': user.username,
            'profile_url': ZDS_APP['site']['url'] + reverse('member-detail', kwargs={'user_name': user.username}),

        }
        text = render_to_string('pages/messages/association_subscribre.md', context)
        create_topic(self.request, bot, forum, title, subtitle, text)

        messages.success(self.request, _(u'Votre demande d\'adhésion a bien été envoyée et va être étudiée.'))

        return super(AssocSubscribeView, self).form_valid(form)

    @method_decorator(login_required)
    @method_decorator(can_write_and_read_now)
    def dispatch(self, *args, **kwargs):
        return super(AssocSubscribeView, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse('pages-assoc-subscribe')


def association(request):
    """Display association's presentation."""
    return render(request, 'pages/association.html')


class ContactView(ListView):
    """
    Display contact page.
    """
    model = GroupContact
    queryset = GroupContact.objects.order_by('position').prefetch_related('group')
    template_name = 'pages/contact.html'
    context_object_name = 'groups'


def eula(request):
    """End-User Licence Agreement."""
    return render(request, 'pages/eula.html')


def cookies(request):
    """Cookies explanation page."""
    return render(request, 'pages/cookies.html')


@can_write_and_read_now
@login_required
@permission_required('forum.change_post', raise_exception=True)
def alerts(request):
    outstanding = Alert.objects.filter(solved=False).order_by('-pubdate')
    solved = Alert.objects.filter(solved=True).order_by('-pubdate')[:15]

    return render(request, 'pages/alerts.html', {
        'alerts': outstanding,
        'solved': solved,
    })


def custom_error_500(request):
    """Custom view for 500 errors"""
    return render(request, '500.html')
