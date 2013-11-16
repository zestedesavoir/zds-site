# coding: utf-8

from zds.forum.models import get_last_topics
from zds.tutorial.models import get_last_tutorials
from zds.utils import render_template


def home(request):
    '''
    Display the home page with last topics added
    '''
    return render_template('home.html', {
        'last_topics': get_last_topics(),
        'last_tutorials': get_last_tutorials(),
    })


def index(request):
    return render_template('pages/index.html')


def help_markdown(request):
    '''
    Display a page with a markdown helper
    '''
    return render_template('pages/help_markdown.html')


def about(request):
    '''
    Display many informations about the website
    '''
    return render_template('pages/about.html')

def roadmap(request):
    '''
    Display roadmap of the website
    '''
    return render_template('pages/roadmap.html')
