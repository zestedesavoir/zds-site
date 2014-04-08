# coding: utf-8

from django.core.urlresolvers import reverse

from zds.article.models import get_last_articles
from zds.forum.models import get_last_topics
from zds.member.decorator import can_read_now
from zds.tutorial.models import get_last_tutorials
from zds.utils import render_template
from zds.utils import slugify


@can_read_now
def home(request):
    '''
    Display the home page with last topics added
    '''
    
    tutos = []
    for tuto in get_last_tutorials():
        data = tuto.load_json_for_public()
        data['pk']=tuto.pk
        data['image']=tuto.image
        data['gallery']=tuto.gallery
        data['pubdate']=tuto.pubdate
        data['update']=tuto.update
        data['subcategory']=tuto.subcategory
        data['get_absolute_url_online']=reverse('zds.tutorial.views.view_tutorial_online', 
                                                   args=[tuto.pk, 
                                                         slugify(data['title'])])
        
        
        tutos.append(data)
    
    return render_template('home.html', {
        'last_topics': get_last_topics(request.user),
        'last_tutorials': tutos,
        'last_articles': get_last_articles(),
    })

@can_read_now
def index(request):
    return render_template('pages/index.html')

@can_read_now
def help_markdown(request):
    '''
    Display a page with a markdown helper
    '''
    return render_template('pages/help_markdown.html')

@can_read_now
def about(request):
    '''
    Display many informations about the website
    '''
    return render_template('pages/about.html')

@can_read_now
def roadmap(request):
    '''
    Display roadmap of the website
    '''
    return render_template('pages/roadmap.html')
