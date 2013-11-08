# -*- coding: utf-8 -*-

from datetime import datetime
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.http import Http404

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from lbp.utils import render_template, slugify
from lbp.utils.models import DateManagerse
from lbp.utils.paginator import paginator_range

from lbp.project.models import Category
from lbp.gallery.models import Image, Gallery, UserGallery

from .models import News, get_prev_news, get_next_news, Comment
from .forms import NewsForm, CommentForm

from models import POSTS_PER_PAGE, TOPICS_PER_PAGE


def index(request):
    '''Affiche la liste des actualités'''
    newss = News.objects.all()\
        .filter(statut='PUBLIQUE')\
        .order_by('-date__pubdate')

    if request.user.is_authenticated():
        user_news = News.objects.filter(authors__in = [request.user])
    else:
        user_news = None

    return render_template('news/index.html', {
        'newss': newss,
        'user_news': user_news
    })
    
def list(request, cat_pk, cat_slug):
    '''Affiche la liste des actualités par catégorie'''
    
    category = get_object_or_404(Category, pk=cat_pk)
    
    newss = News.objects.all()\
        .filter(statut='PUBLIQUE', category__in=[category])\
        .order_by('-date__pubdate')
        
    if request.user.is_authenticated():
        user_news = News.objects.filter(authors__in = [request.user])
    else:
        user_news = None

    return render_template('news/index.html', {
        'newss': newss,
        'user_news': user_news
    })
    
def list_admin(request):
    '''Affiche la liste des actualités par catégorie'''
    
    if not request.user.has_perm('news.valider_news'):
        raise Http404
    
    newss = News.objects.all()\
        .filter(statut='VALIDATION')\
        .order_by('-date__pubdate')
        
    if request.user.is_authenticated():
        user_news = News.objects.filter(authors__in = [request.user])
    else:
        user_news = None

    return render_template('news/admin.html', {
        'newss': newss,
        'user_news': user_news
    })


def view(request, news_pk, news_slug):
    '''Montrer une actualité donnée si elle existe et si elle est publique'''
    news = get_object_or_404(News, pk=news_pk)
    
    if news.statut != 'PUBLIQUE' and not (request.user in news.authors.all() or request.user.has_perm('news.valider_news') ):
        raise Http404

    if news_slug != slugify(news.title):
        return redirect(news.get_absolute_url())
    
    # Handle pagination
    paginator = Paginator(news.get_comments(), POSTS_PER_PAGE)
    
    try:
        page_nbr = int(request.GET['page'])
    except KeyError:
        page_nbr = 1

    try:
        comments = paginator.page(page_nbr)
    except PageNotAnInteger:
        comments = paginator.page(1)
    except EmptyPage:
        raise Http404

    res = []
    if page_nbr != 1:
        # Show the last comment of the previous page
        last_page = paginator.page(page_nbr - 1).object_list
        last_comment = (last_page)[len(last_page) - 1]
        res.append(last_comment)
    
    return render_template('news/view.html', {
        'news': news,
        'prev': get_prev_news(news),
        'next': get_next_news(news),
        'pages': paginator_range(page_nbr, paginator.num_pages),
        'nb': page_nbr,
    })


@login_required
def new(request):
    '''Create a new actualite'''
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES)
        
        if 'image' in request.FILES: 
            if request.FILES['image'].size > settings.IMAGE_MAX_SIZE:
                raise Http404
        
        if form.is_valid():
            data = form.data

            news = News()
            news.title = data['title']
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
            
            #create authors
            news.authors.add(request.user)
            news.save()
            
            # Creating the gallery
            gal = Gallery()
            gal.title = data['title']
            gal.slug = slugify(data['title'])
            gal.pubdate = datetime.now()
            gal.save()

            # Attach user to gallery
            userg = UserGallery()
            userg.gallery = gal
            userg.mode = 'W' #write mode
            userg.user = request.user
            userg.save()
            
            news.gallery=gal
            news.save()
            
            # Create image
            if 'image' in request.FILES:
                img = Image()
                img.physical = request.FILES['image']
                img.gallery = gal
                img.title = request.FILES['image']
                img.slug = slugify(request.FILES['image'])
                img.pubdate = datetime.now()
                img.save()
                
                news.image=img
                news.save()

            for cat in data['category']:
                news.category.add(cat)
            
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
    if ((not request.user in news.authors.all()) or (not news.en_ligne)) and  not request.user.has_perm('news.valider_news'):
        raise Http404

    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES)
        
        if 'image' in request.FILES: 
            if request.FILES['image'].size > settings.IMAGE_MAX_SIZE:
                raise Http404
            
        if form.is_valid():
            data = form.data

            news.titre = data['title']
            news.description = data['description']
            news.text = data['text']
            news.date.update = datetime.now()
            news.category= data['category']
            
            # Update image
            if 'image' in request.FILES:
                img = Image()
                img.physical = request.FILES['image']
                img.gallery = news.gallery
                img.title = request.FILES['image']
                img.slug = slugify(request.FILES['image'])
                img.update = datetime.now()
                img.save()
                
                news.image=img
                news.save()
                
            news.tags.clear()
            list_tags = data['tags'].split(',')
            for tag in list_tags:
                news.tags.add(tag)

            news.save()
            return redirect(news.get_absolute_url())
    else:
        # initial value for tags input
        list_tags = ''
        for tag in news.tags.all():
            list_tags += ',' + tag.__str__()

        form = NewsForm({
            'title': news.title,
            'description': news.description,
            'category': news.category.all(),
            'text': news.text,
            'tags': list_tags,
        })

    return render_template('news/edit.html', {
        'news': news, 'form': form
    })


@login_required
def modify(request):
    if not request.method == 'POST':
        raise Http404

    data = request.POST

    news_pk = data['news']
    news = get_object_or_404(News, pk=news_pk)

    if request.user in news.authors.all() or request.user.has_perm('news.valider_news'):
        if 'delete' in data:
            news.delete()
            return redirect('/news/')
    if request.user in news.authors.all() :
        if 'ask-valide' in data:
            news.statut = 'VALIDATION'
            news.save()
    if request.user.has_perm('news.valider_news') :
        if 'valide' in data:
            news.statut = 'PUBLIQUE'
            dt=news.date
            dt.pubdate = datetime.now()
            dt.save()
            
            news.date = dt
            news.save()
        if 'rejet' in data:
            news.statut = 'REDACTION'
            news.save()
        if 'invalide' in data:
            news.statut = 'VALIDATION'
            dt=news.date
            dt.pubdate = None
            dt.save()
            news.date=dt
            news.save()

    return redirect(news.get_absolute_url())

def find_news(request, pk):
    u = get_object_or_404(User, pk=pk)
    newss=News.objects.all().filter(authors__in=[u])\
                          .order_by('-date__pubdate')
    # Paginator
    
    return render_template('news/find.html', {
        'newss': newss, 'usr':u,
    })
    

@login_required
def answer(request):
    '''
    Adds an answer from an user to a news
    '''
    try:
        news_pk = request.GET['news']
    except KeyError:
        raise Http404

    g_news = get_object_or_404(News, pk=news_pk)
    comments = Comment.objects.filter(news=g_news).order_by('-pubdate')[:3]
    last_comment = g_news.get_last_answer()
    if last_comment==None:
        last_comment_pk = None
    else:
        last_comment_pk = last_comment.pk

    # Check that the user isn't spamming
    if g_news.antispam(request.user):
        raise Http404

    # If we just sent data
    if request.method == 'POST':
        data = request.POST
        if data['last_comment']=='':
            newcomment = False
        else:
            newcomment = last_comment_pk != int(data['last_comment'])

        # Using the « preview button », the « more » button or new comment
        if 'preview' in data or 'more' in data or newcomment:
            return render_template('news/answer.html', {
                'text': data['text'], 'news': g_news, 'comments': comments,
                'last_comment_pk': last_comment_pk, 'newcomment': newcomment
            })

        # Saving the message
        else:
            form = CommentForm(request.POST)
            if form.is_valid():
                data = form.data

                comment = Comment()
                comment.news = g_news
                comment.author = request.user
                comment.text = data['text']
                comment.pubdate = datetime.now()
                comment.position = g_news.get_comment_count() + 1
                comment.save()


                return redirect(comment.get_absolute_url())
            else:
                raise Http404

    else:
        text = ''

        # Using the quote button
        if 'cite' in request.GET:
            comment_cite_pk = request.GET['cite']
            comment_cite = Comment.objects.get(pk=comment_cite_pk)

            for line in comment_cite.text.splitlines():
                text = text + '> ' + line + '\n'

            text = u'**{0} a écrit :**\n{1}\n'.format(
                comment_cite.author.username, text)

        return render_template('forum/answer.html', {
            'news': g_news, 'text': text, 'comments': comments,
            'last_comment_pk': last_comment_pk
        })

@login_required
def edit_comment(request):
    '''
    Edit the given user's comment
    '''
    try:
        comment_pk = request.GET['message']
    except KeyError:
        raise Http404

    comment = get_object_or_404(Comment, pk=comment_pk)

    g_news = None
    if comment.position == 1:
        g_news = get_object_or_404(News, pk=comment.news.pk)

    # Making sure the user is allowed to do that
    if comment.author != request.user:
        if not request.user.has_perm('forum.change_comment'):
            raise Http404
        elif request.method == 'GET':
            messages.add_message(
                request, messages.WARNING,
                u'Vous éditez ce message en tant que modérateur (auteur : {}).'
                u' Soyez encore plus prudent lors de l\'édition de celui-ci !'
                .format(comment.author.username))

    if request.method == 'POST':
         # Using the preview button
        if 'preview' in request.POST:
            return render_template('forum/edit_post.html', {
                'comment': comment, 'news': g_news, 'text': request.POST['text'],
            })
        # The user just sent data, handle them
        comment.text = request.POST['text']
        comment.update = datetime.now()
        comment.save()

        return redirect(comment.get_absolute_url())

    else:
        return render_template('news/edit_comment.html', {
            'comment': comment, 'news': g_news, 'text': comment.text
        })

