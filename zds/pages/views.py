# coding: utf-8

import os.path
import random

from django.contrib.auth.models import Group, User
from django.core.urlresolvers import reverse

from zds.article.models import get_last_articles
from zds.forum.models import get_last_topics
from zds.member.decorator import can_read_now
from zds.settings import SITE_ROOT
from zds.tutorial.models import get_last_tutorials
from zds.utils import render_template, slugify


@can_read_now
def home(request):
    """Display the home page with last topics added."""

    tutos = []
    for tuto in get_last_tutorials():
        data = tuto.load_json_for_public()
        data['pk'] = tuto.pk
        data['image'] = tuto.image
        data['gallery'] = tuto.gallery
        data['pubdate'] = tuto.pubdate
        data['update'] = tuto.update
        data['subcategory'] = tuto.subcategory
        data['get_absolute_url_online'] = reverse(
            'zds.tutorial.views.view_tutorial_online',
            args=[
                tuto.pk,
                slugify(
                    data['title'])])

        tutos.append(data)
        
    try:
        with open(os.path.join(SITE_ROOT, 'quotes.txt'), 'r') as fh:
            quote = random.choice(fh.readlines())
    except:
        quote = u'Zeste de Savoir, la connaissance sans les pépins'

    return render_template('home.html', {
        'last_topics': get_last_topics(request.user),
        'last_tutorials': tutos,
        'last_articles': get_last_articles(),
        'quote': quote,
    })


@can_read_now
def index(request):
    return render_template('pages/index.html')


@can_read_now
def about(request):
    """Display many informations about the website."""
    return render_template('pages/about.html')


@can_read_now
def association(request):
    """Display association's presentation."""
    return render_template('pages/association.html')


@can_read_now
def contact(request):
    """Display contact page."""
    staffs = User.objects.filter(groups__in=Group.objects.filter(name__contains='staff')).all()
    devs = User.objects.filter(groups__in=Group.objects.filter(name__contains='dev')).all()
    return render_template('pages/contact.html', {
        'staffs': staffs,
        'devs': devs
    })


@can_read_now
def eula(request):
    '''
    End-User Licence Agreement
    '''
    return render_template('pages/eula.html')
