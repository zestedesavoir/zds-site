# coding: utf-8

from datetime import datetime
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.encoding import smart_str, smart_unicode
from lxml import etree
from operator import itemgetter, attrgetter
from zds.utils.templatetags.emarkdown import emarkdown
import json
import os
import shutil

from git import *
from zds.utils import render_template, slugify
from zds.utils.articles import *
from zds.utils.models import Category

from .forms import ArticleForm
from .models import Article, get_prev_article, get_next_article, Validation


def index(request):
    '''Displayy articles list'''
    article = Article.objects.all()\
        .filter(is_visible=True)\
        .order_by('-pubdate')

    return render_template('article/index.html', {
        'articles': article,
    })


def list(request):
    '''Display articles list'''
    try:
        articles = Article.objects.all() \
            .filter(sha_draft__isnull=False) \
            .order_by("-update")
    except:
        articles = None
        
    return render_template('article/index.html', {
        'articles': articles,
    })
    
@login_required
def list_validation(request):
    '''Display articles list in validation'''
    
    if not request.user.has_perm('article.change_article'):
        raise Http404
    try:
        type = request.GET['type']
    except KeyError:
        type=None
    
    try:
        category = get_object_or_404(Category, pk=request.GET['category'])
    except KeyError:
        category=None
    
    if type == 'orphan':
        if category ==None:
            validations = Validation.objects.all() \
                .filter(validator__isnull=True) \
                .order_by("date_proposition")
        else :
            validations = Validation.objects.all() \
                .filter(validator__isnull=True, article__category__in=[category]) \
                .order_by("date_proposition")
    elif type == 'reserved':
        if category ==None:
            validations = Validation.objects.all() \
                .filter(validator__isnull=False) \
                .order_by("date_proposition")
        else:
            validations = Validation.objects.all() \
                .filter(validator__isnull=False, article__category__in=[category]) \
                .order_by("date_proposition")
    else:
        if category ==None:
            validations = Validation.objects.all() \
                .order_by("date_proposition")
        else:
            validations = Validation.objects.all() \
            .filter(article__category__in=[category]) \
                .order_by("date_proposition")
    
    print(validations)
    return render_template('article/validation.html', {
        'validations': validations,
    })


@login_required
def reservation(request, validation_pk):
    '''Display articles list in validation'''
    
    validation = get_object_or_404(Validation, pk=validation_pk)
    
    if not request.user.has_perm('article.change_article'):
        raise Http404
    
    if validation.validator :
        validation.validator = None
        validation.date_reserve = None
        validation.status = 'PENDING'
        validation.save()
        
        return redirect(reverse('zds.article.views.list_validation'))
    
    else:
        validation.validator = request.user
        validation.date_reserve = datetime.now()
        validation.status = 'PENDING_V'
        validation.save()
        return redirect(validation.article.get_absolute_url())

@login_required
def history(request, article_pk, article_slug):
    '''Display an article'''
    article = get_object_or_404(Article, pk=article_pk)

    if not article.on_line \
       and not request.user.has_perm('article.change_article') \
       and request.user not in article.authors.all():
        raise Http404

    # Make sure the URL is well-formed
    if not article_slug == slugify(article.title):
        return redirect(article.get_absolute_url())


    repo = Repo(article.get_path())
    tree = repo.heads.master.commit.tree
    
    logs = repo.head.reference.log()
    logs = sorted(logs, key=attrgetter('time'), reverse=True)
    
    return render_template('article/history.html', {
        'article': article, 'logs':logs
    })

def view(request, article_pk, article_slug):
    '''Show the given article if exists and is visible'''
    article = get_object_or_404(Article, pk=article_pk)

    if request.user.has_perm('article.change_article') and (article.authors.filter(pk = request.user.pk).count()==0):
        raise Http404
    
    try:
        sha = request.GET['version']
    except KeyError:
        sha = article.sha_draft

    if article_slug != slugify(article.title):
        return redirect(article.get_absolute_url())
    
    #find the good manifest file
    repo = Repo(article.get_path())

    manifest = get_blob(repo.commit(sha).tree, 'manifest.json')
    article_version = json.loads(manifest)
    article_version['txt'] = get_blob(repo.commit(sha).tree, article_version['text'])
    article_version['pk'] = article.pk
    article_version['slug'] = article.slug
    article_version['sha_validation'] = article.sha_validation
    article_version['sha_public'] = article.sha_public

    validation = Validation.objects.filter(article__pk=article.pk, version = sha)
    
    return render_template('article/view.html', {
        'article': article_version,
        'authors': article.authors,
        'tags': article.tags,
        'version': sha,
        'prev': get_prev_article(article),
        'next': get_next_article(article), 
        'validation': validation
    })

def view_online(request, article_pk, article_slug):
    '''Show the given article if exists and is visible'''
    article = get_object_or_404(Article, pk=article_pk)

    if (not article.is_visible) and (article.authors.filter(pk = request.user.pk).count()==0):
        raise Http404
    
    try:
        sha = request.GET['version']
    except KeyError:
        sha = article.sha_draft

    if article_slug != slugify(article.title):
        return redirect(article.get_absolute_url())
    
    #find the good manifest file
    article_version = article.load_json()
    txt = open(os.path.join(article.get_path(), article_version['text']+'.html'), "r")
    article_version['txt'] = txt.read()
    txt.close()
    article_version['pk'] = article.pk
    article_version['slug'] = article.slug
    
    return render_template('article/view_online.html', {
        'article': article_version,
        'authors': article.authors,
        'tags': article.tags,
        'version': sha,
        'prev': get_prev_article(article),
        'next': get_next_article(article), 
    })

@login_required
def new(request):
    '''Create a new article'''
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.data

            article = Article()
            article.title = data['title']
            article.description = data['description']
            article.text = "text.md"
            if 'image' in request.FILES :
                article.image = request.FILES['image']

            # Since the article is not published yet, this value isn't
            # important (will be changed on publish)
            article.create_at = datetime.now()
            article.pubdate = datetime.now()

            # First save before tags because they need to know the id of the
            # article
            article.save()
            
            article.authors.add(request.user)

            list_tags = data['tags'].split(',')
            for tag in list_tags:
                article.tags.add(tag)
            article.save()
            
            maj_repo_article(new_slug_path=article.get_path(), 
                          article = article,
                          text = data['text'],
                          action = 'add')
            return redirect(article.get_absolute_url())
    else:
        form = ArticleForm()

    return render_template('article/new.html', {
        'form': form
    })


@login_required
def edit(request):
    '''Edit article identified by given GET paramter'''
    try:
        article_pk = request.GET['article']
    except KeyError:
        raise Http404

    article = get_object_or_404(Article, pk=article_pk)
    json = article.load_json()

    # Make sure the user is allowed to do it
    if not request.user in article.authors.all():
        raise Http404

    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.data
            old_slug = article.get_path()
            article.title = data['title']
            article.description = data['description']
            if 'image' in request.FILES:
                article.image = request.FILES['image']

            article.tags.clear()
            list_tags = data['tags'].split(',')
            for tag in list_tags:
                article.tags.add(tag)

            article.save()
            
            
            
            new_slug = os.path.join(settings.REPO_ARTICLE_PATH, slugify(data['title']))
            
            maj_repo_article(old_slug_path=old_slug, 
                          new_slug_path=new_slug, 
                          article=article, 
                          text=data['text'],
                          action = 'maj')
            
            return redirect(article.get_absolute_url())
    else:
        # initial value for tags input
        list_tags = ''
        for tag in article.tags.all():
            list_tags += ',' + tag.__str__()

        form = ArticleForm({
            'title': json['title'],
            'description': json['description'],
            'text': article.get_text(),
            'tags': list_tags,
        })

    return render_template('article/edit.html', {
        'article': article, 'form': form
    })


@login_required
def modify(request):
    if not request.method == 'POST':
        raise Http404

    data = request.POST

    article_pk = data['article']
    article = get_object_or_404(Article, pk=article_pk)
    
    # Validator actions
    if request.user.has_perm('article.change_article'):
        if 'valid-article' in request.POST:
            MEP(article, article.sha_validation)
            validation = Validation.objects.filter(article__pk=article.pk, version = article.sha_validation).all()[0]
            validation.comment_validator = request.POST['comment-v']
            validation.status = 'ACCEPT'
            validation.date_validation = datetime.now()
            validation.save()
            
            article.sha_public = validation.version
            article.sha_validation = ''
            article.pubdate = datetime.now()
            article.save()
            
            return redirect(article.get_absolute_url()+'?version='+validation.version)
        
        elif 'reject-article' in request.POST:
            validation = Validation.objects.filter(article__pk=article.pk, version = article.sha_validation).all()[0]
            validation.comment_validator = request.POST['comment-r']
            validation.status = 'REJECT'
            validation.date_validation = datetime.now()
            validation.save()
            
            article.sha_validation = ''
            article.pubdate = None
            article.save()
            
            return redirect(article.get_absolute_url()+'?version='+validation.version)
        
        elif 'invalid-article' in request.POST:
            validation = Validation.objects.filter(article__pk=article.pk, version = article.sha_public).all()[0]
            validation.status = 'PENDING'
            validation.date_validation = None
            validation.save()
            
            article.sha_validation = validation.version
            article.sha_public = ''
            article.pubdate = None
            article.save()
            
            return redirect(article.get_absolute_url()+'?version='+validation.version)
    
    #User actions
    if request.user in article.authors.all():
        if 'delete' in data:
            article.delete()
            return redirect('/articles/')
        elif 'pending' in request.POST:
            validation = Validation()
            validation.article = article
            validation.date_proposition = datetime.now()
            validation.comment_authors = request.POST['comment']
            validation.version = request.POST['version']
            
            validation.save()
            
            validation.article.sha_validation = request.POST['version']
            validation.article.save()
            
            return redirect(article.get_absolute_url())

    return redirect(article.get_absolute_url())

def find_article(request, name):
    u = get_object_or_404(User, username=name)
    articles=Article.objects.all().filter(author=u)\
                          .order_by('-pubdate')
    # Paginator
    
    return render_template('article/find_article.html', {
        'articles': articles, 'usr':u,
    })

def maj_repo_article(old_slug_path=None, new_slug_path=None, article=None, text=None, action=None):
    
    if action == 'del' :
        shutil.rmtree(old_slug_path)
    else:
        if action == 'maj':    
            shutil.move(old_slug_path, new_slug_path)
            repo = Repo(new_slug_path)
            msg='Modification de l\'article'
        elif action == 'add' :
            os.makedirs(new_slug_path, mode=0777)
            repo = Repo.init(new_slug_path, bare=False)
            msg='Creation de l\'article'
        
        repo = Repo(new_slug_path)
        index = repo.index
        
        man_path=os.path.join(new_slug_path,'manifest.json')
        article.dump_json(path=man_path)
        index.add(['manifest.json'])
        
        
        txt = open(os.path.join(new_slug_path, 'text.md'), "w")
        txt.write(smart_str(text).strip())
        txt.close()
        index.add(['text.md'])
            
        com = index.commit(msg.encode('utf-8'))
        article.sha_draft=com.hexsha
        article.save()

def download(request):
    '''Download an article'''

    article = get_object_or_404(Article, pk=request.GET['article'])

    ph=os.path.join(settings.REPO_ARTICLE_PATH, article.slug)
    repo = Repo(ph)
    repo.archive(open(ph+".tar",'w'))
    
    response = HttpResponse(open(ph+".tar", 'rb').read(), mimetype='application/tar')
    response['Content-Disposition'] = 'attachment; filename={0}.tar'.format(article.slug)

    return response

# Deprecated URLs

def deprecated_view_redirect(request, article_pk, article_slug):
    article = get_object_or_404(Article, pk=article_pk)
    return redirect(article.get_absolute_url(), permanent=True)

def MEP(article, sha):
    #convert markdown file to html file
    repo = Repo(article.get_path())
    manifest = get_blob(repo.commit(sha).tree, 'manifest.json')
    
    article_version = json.loads(manifest)
    md_file_contenu = get_blob(repo.commit(sha).tree, article_version['text'])
    
    html_file = open(os.path.join(article.get_path(), article_version['text']+'.html'), "w")
    html_file.write(emarkdown(md_file_contenu))
    html_file.close()
    
    

