# -*- coding: utf-8 -*-

from datetime import datetime

from django.shortcuts import get_object_or_404, redirect
from django.http import Http404

from django.contrib.auth.decorators import login_required

from lbp.utils import render_template, slugify
from lbp.utils.models import DateManager

from .models import News, get_prev_news, get_next_news
from .forms import NewsForm



def index(request):
    '''Affiche la liste des actualités'''
    news = News.objects.all()\
        .filter(statut='PUBLIQUE')\
        .order_by('date__pubdate')
        
    if len(news)>0 :
        une=news[0]
        if len(news)>1 :
            other=news[1:5]
        else :
            other=None
    else:
        une=News()
        other=None
     

    if request.user.is_authenticated():
        user_news = News.objects.filter(authors__in = [request.user])
    else:
        user_news = None

    return render_template('news/index.html', {
        'une': une,
        'news': other,
        'user_news': user_news
    })


def view(request, news_pk, news_slug):
    '''Montrer une actualité donnée si elle existe et si elle est publique'''
    news = get_object_or_404(News, pk=news_pk)

    if news.statut != 'PUBLIQUE' and not request.user in actualite.auteurs.all() :
        raise Http404

    if news_slug != slugify(news.titre):
        return redirect(news.get_absolute_url())

    return render_template('news/view.html', {
        'news': news,
        'prev': get_prev_news(news),
        'next': get_next_news(news)
    })


@login_required
def new(request):
    '''Create a new actualite'''
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.data

            news = News()
            news.titre = data['title']
            news.description = data['description']
            news.text = data['text']
            

            # Since the news is not published yet, this value isn't
            # important (will be changed on publish)
            dt = DateManager()
            dt.create_at = datetime.now()
            dt.update = datetime.now()
            dt.save()
            news.date = dt

            # on enregistre d'abord les champs de base
            news.save()
            
            #on rajoute ensuite l'auteur de l'actualité
            news.authors.add(request.user)
            news.save()

            list_tags = data['tags'].split(',')
            for tag in list_tags:
                news.tags.add(tag)
            news.save()
            return redirect(news.get_absolute_url())
    else:
        form = NewsForm()

    return render_template('news/new.html', {
        'form': form
    })


@login_required
def edit(request):
    '''Edit news identified by given GET paramter'''
    try:
        news_pk = request.GET['news']
    except KeyError:
        raise Http404

    news = get_object_or_404(News, pk=news_pk)

    # Make sure the user is allowed to do it
    if not request.user in actualite.auteurs.all():
        raise Http404

    if request.method == 'POST':
        form = NewsForm(request.POST)
        if form.is_valid():
            data = form.data

            news.titre = data['title']
            news.description = data['description']
            news.text = data['text']

            news.tags.clear()
            list_tags = data['tags'].split(',')
            for tag in list_tags:
                news.tags.add(tag)

            news.save()
            return redirect(actualite.get_absolute_url())
    else:
        # initial value for tags input
        list_tags = ''
        for tag in news.tags.all():
            list_tags += ',' + tag.__str__()

        form = NewsForm({
            'title': news.title,
            'description': news.description,
            'text': news.text,
            'tags': list_tags,
        })

    return render_template('news/edit.html', {
        'news': actualite, 'form': form
    })


@login_required
def modify(request):
    if not request.method == 'POST':
        raise Http404

    data = request.POST

    news_pk = data['news']
    news = get_object_or_404(News, pk=news_pk)

    if request.user in news.authors:
        if 'delete' in data:
            news.delete()
            return redirect('/news/')

    return redirect(news.get_absolute_url())
