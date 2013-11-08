# coding: utf-8

from lbp.utils import render_template

from lbp.forum.models import get_last_topics
from lbp.news.models import get_last_news
from lbp.project.models import get_last_projects


def home(request):
    '''
    Display the home page with last topics added
    '''
    return render_template('home.html', {
        'last_topics': get_last_topics(),
        'last_news': get_last_news(),
        'last_projects': get_last_projects(),
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
