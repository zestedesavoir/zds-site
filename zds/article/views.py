# coding: utf-8

from datetime import datetime
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.encoding import smart_str, smart_unicode
from django.views.decorators.http import require_POST
import json
from lxml import etree
from operator import itemgetter, attrgetter
import os
import shutil

from git import *
from zds.member.models import Profile
from zds.member.views import get_client_ip
from zds.member.decorator import can_read_now, can_write_and_read_now
from zds.utils import render_template, slugify
from zds.utils.articles import *
from zds.utils.models import SubCategory, Category, CommentLike, CommentDislike, Alert
from zds.utils.paginator import paginator_range
from zds.utils.templatetags.emarkdown import emarkdown

from .forms import ArticleForm, ReactionForm, AlertForm
from .models import Article, get_prev_article, get_next_article, Validation, \
    Reaction, never_read, mark_read, STATUS_CHOICES

@can_read_now
def index(request):
    '''Display all public articles of the website.'''
    # The tag indicate what the category article the user would 
    # like to display. We can display all subcategories for articles.
    try:
        tag = get_object_or_404(SubCategory, title = request.GET['tag'])
    except (KeyError, Http404):
        tag = None
        
    if tag == None:
        article = Article.objects\
            .filter(sha_public__isnull = False)\
            .order_by('-pubdate')\
            .all()
    else:
        # The tag isn't None and exist in the system. We can use it to retrieve 
        # all articles in the subcategory specified.
        article = Article.objects\
            .filter(sha_public__isnull = False, subcategory__in = [tag])\
            .order_by('-pubdate')\
            .all()

    return render_template('article/index.html', {
        'articles': article,
    })

@can_read_now
@permission_required('article.change_article', raise_exception=True)
@login_required
def view(request, article_pk, article_slug):
    '''Show the given offline article if exists'''
    article = get_object_or_404(Article, pk = article_pk)

    # Only authors of the article and staff can view article in offline.
    if not request.user.has_perm('forum.change_article')\
        or request.user not in article.authors.all():
        raise PermissionDenied

    # The slug of the article must to be right.
    if article_slug != slugify(article.title):
        return redirect(article.get_absolute_url())
    
    # Retrieve sha given by the user. This sha must to be exist.
    # If it doesn't exist, we take draft version of the article.
    try:
        sha = request.GET['version']
        if article.sha_public != sha\
            or article.sha_validation != sha\
            or article.sha_draft != sha\
            or article.sha_rereading != sha:
            raise Http404
    except (KeyError, Http404):
        sha = article.sha_draft
    
    # Find the good manifest file
    repo = Repo(article.get_path())

    # Load the article.
    manifest = get_blob(repo.commit(sha).tree, 'manifest.json')
    article_version = json.loads(manifest)
    article_version['txt'] = get_blob(repo.commit(sha).tree, article_version['text'])
    article_version['pk'] = article.pk
    article_version['slug'] = article.slug
    article_version['sha_validation'] = article.sha_validation
    article_version['sha_public'] = article.sha_public
    article_version['sha_rereading'] = article.sha_rereading

    validation = Validation.objects.filter(article__pk = article.pk, version = sha)
    
    return render_template('article/view.html', {
        'article': article_version,
        'authors': article.authors,
        'tags': article.subcategory,
        'version': sha,
        'prev': get_prev_article(article),
        'next': get_next_article(article), 
        'validation': validation
    })

@can_read_now
def view_online(request, article_pk, article_slug):
    '''Show the given article if exists and is visible'''
    article = get_object_or_404(Article, pk=article_pk)
    
    # The slug of the article must to be right.
    if article_slug != slugify(article.title):
        return redirect(article.get_absolute_url_online())
    
    # Load the article.
    article_version = article.load_json()
    txt = open(os.path.join(article.get_path(), article_version['text']+'.html'), "r")
    article_version['txt'] = txt.read()
    txt.close()
    article_version['pk'] = article.pk
    article_version['slug'] = article.slug
    article_version['is_locked'] = article.is_locked

    # If the user is authenticated
    if request.user.is_authenticated():
        # We check if he can post an article or not with 
        # antispam filter.
        article_version['antispam'] = article.antispam()
        # If the user is never read, we mark this article read.
        if never_read(article):
            mark_read(article)
       
    # Find all reactions of the article.
    reactions = Reaction.objects\
                .filter(article__pk = article.pk)\
                .order_by('position')\
                .all()
    
    # Retrieve pk of the last reaction. If there aren't reactions
    # for the article, we initialize this last reaction at 0.
    last_reaction_pk = 0
    if article.last_reaction:
        last_reaction_pk = article.last_reaction.pk
    
    # Handle pagination.
    paginator = Paginator(reactions, settings.POSTS_PER_PAGE)

    try:
        page_nbr = int(request.GET['page'])
    except KeyError:
        page_nbr = 1

    try:
        reactions = paginator.page(page_nbr)
    except PageNotAnInteger:
        reactions = paginator.page(1)
    except EmptyPage:
        raise Http404

    res = []
    if page_nbr != 1:
        # Show the last reaction of the previous page
        last_page = paginator.page(page_nbr - 1).object_list
        last_reaction = (last_page)[len(last_page) - 1]
        res.append(last_reaction)

    for reaction in reactions:
        res.append(reaction)
    
    return render_template('article/view_online.html', {
        'article': article_version,
        'authors': article.authors,
        'tags': article.subcategory,
        'prev': get_prev_article(article),
        'next': get_next_article(article),
        'reactions': res,
        'pages': paginator_range(page_nbr, paginator.num_pages),
        'nb': page_nbr,
        'last_reaction_pk': last_reaction_pk 
    })

@can_write_and_read_now
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

            # Add subcategories on article
            for subcat in form.cleaned_data['subcategory']:
                article.subcategory.add(subcat)

            article.save()
            
            maj_repo_article(request,
                          new_slug_path=article.get_path(), 
                          article = article,
                          text = data['text'],
                          action = 'add')
            return redirect(article.get_absolute_url())
    else:
        form = ArticleForm()

    return render_template('article/new.html', {
        'form': form
    })

@can_write_and_read_now
@login_required
def edit(request):
    '''Edit article identified by given GET parameter'''
    try:
        article_pk = request.GET['article']
    except KeyError:
        raise Http404

    article = get_object_or_404(Article, pk=article_pk)

    # Only authors of the article and staff can edit article.
    if not request.user.has_perm('forum.change_article')\
        or request.user not in article.authors.all():
        raise PermissionDenied

    json = article.load_json()
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            # Update article with data.
            data = form.data
            old_slug = article.get_path()
            article.title = data['title']
            article.description = data['description']
            if 'image' in request.FILES:
                article.image = request.FILES['image']

            article.subcategory.clear()
            for subcat in form.cleaned_data['subcategory']:
                article.subcategory.add(subcat)

            article.save()

            new_slug = os.path.join(settings.REPO_ARTICLE_PATH, slugify(data['title']))
            
            maj_repo_article(request,
                          old_slug_path=old_slug, 
                          new_slug_path=new_slug, 
                          article=article, 
                          text=data['text'],
                          action = 'maj')
            
            return redirect(article.get_absolute_url())
    else:
        form = ArticleForm({
            'title': json['title'],
            'description': json['description'],
            'text': article.get_text(),
            'subcategory': article.subcategory.all(),
        })

    return render_template('article/edit.html', {
        'article': article, 'form': form
    })

@can_write_and_read_now
@require_POST
@login_required
def modify(request):
    '''Modify status of the article'''
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
            article.sha_rereading = ''
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
            article.sha_public = None
            article.sha_rereading = ''
            article.pubdate = None
            article.save()
            
            return redirect(article.get_absolute_url()+'?version='+validation.version)
        
        elif 'invalid-article' in request.POST:
            validation = Validation.objects.filter(article__pk=article.pk, version = article.sha_public).all()[0]
            validation.status = 'PENDING'
            validation.date_validation = None
            validation.save()
            
            article.sha_validation = validation.version
            article.sha_public = None
            article.sha_rereading = ''
            article.pubdate = None
            article.save()
            
            return redirect(article.get_absolute_url()+'?version='+validation.version)

        elif 'invalid-rereading' in request.POST:
            validation = Validation.objects.filter(article__pk=article.pk, version = article.sha_rereading).all()[0]
            validation.status = 'REJECT'
            validation.date_validation = None
            validation.save()
            
            article.sha_validation = ''
            article.sha_public = None
            article.sha_rereading = ''
            article.pubdate = None
            article.save()
            
            return redirect(article.get_absolute_url())
    
    # User actions
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
        elif 'rereading' in request.POST:
            validation = Validation()
            validation.status = 'REREADING'
            validation.article = article
            validation.date_proposition = datetime.now()
            validation.version = request.POST['version']

            validation.save()

            validation.article.sha_rereading = request.POST['version']
            validation.article.save()

    return redirect(article.get_absolute_url())

@can_read_now
def find_article(request, name):
    u = get_object_or_404(User, username=name)
    articles=Article.objects.all().filter(author=u)\
                          .order_by('-pubdate')
    # Paginator
    
    return render_template('article/find_article.html', {
        'articles': articles, 'usr':u,
    })

def maj_repo_article(request, old_slug_path=None, new_slug_path=None, article=None, text=None, action=None):
    
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
        
        aut_user = str(request.user.pk)
        aut_email = str(request.user.email)
        if aut_email is None or aut_email.strip() == "":
            aut_email ="inconnu@zestedesavoir.com"
        com = index.commit(msg.encode('utf-8'),
                           author=Actor(aut_user, aut_email),
                           committer=Actor(aut_user, aut_email)
                           )
        article.sha_draft=com.hexsha
        article.save()

@can_read_now
def download(request):
    '''Download an article'''

    article = get_object_or_404(Article, pk=request.GET['article'])

    ph=os.path.join(settings.REPO_ARTICLE_PATH, article.slug)
    repo = Repo(ph)
    repo.archive(open(ph+".tar",'w'))
    
    response = HttpResponse(open(ph+".tar", 'rb').read(), mimetype='application/tar')
    response['Content-Disposition'] = 'attachment; filename={0}.tar'.format(article.slug)

    return response

# Validation

@can_read_now
@permission_required('article.change_article', raise_exception=True)
@login_required
def list_validation(request):
    '''Display articles list in validation'''
    try:
        type = request.GET['type']
    except KeyError:
        type=None
    
    try:
        subcategory = get_object_or_404(Category, pk=request.GET['subcategory'])
    except KeyError:
        subcategory=None

    if type == 'orphan':
        if subcategory == None:
            validations = Validation.objects \
                            .filter(validator__isnull=True) \
                            .order_by("date_proposition") \
                            .all()
        else :
            validations = Validation.objects \
                            .filter(validator__isnull=True, article__subcategory__in=[subcategory]) \
                            .order_by("date_proposition") \
                            .all()
    elif type == 'reserved':
        if subcategory == None:
            validations = Validation.objects \
                            .filter(validator__isnull=False) \
                            .order_by("date_proposition") \
                            .all()
        else :
            validations = Validation.objects \
                            .filter(validator__isnull=False, article__subcategory__in=[subcategory]) \
                            .order_by("date_proposition") \
                            .all()        
    else:
        if subcategory == None:
            validations = Validation.objects \
                            .order_by("date_proposition") \
                            .all()
        else :
            validations = Validation.objects \
                            .filter(article__subcategory__in=[subcategory]) \
                            .order_by("date_proposition") \
                            .all()
    
    return render_template('article/validation.html', {
        'validations': validations,
    })

@can_read_now
@permission_required('article.change_article', raise_exception=True)
@login_required
def reservation(request, validation_pk):
    '''Display articles list in validation'''
    
    validation = get_object_or_404(Validation, pk=validation_pk)
    
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

@can_read_now
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

# Reactions at an article.

def MEP(article, sha):
    #convert markdown file to html file
    repo = Repo(article.get_path())
    manifest = get_blob(repo.commit(sha).tree, 'manifest.json')
    
    article_version = json.loads(manifest)
    md_file_contenu = get_blob(repo.commit(sha).tree, article_version['text'])
    
    html_file = open(os.path.join(article.get_path(), article_version['text']+'.html'), "w")
    html_file.write(emarkdown(md_file_contenu))
    html_file.close()

@can_write_and_read_now
@login_required
def answer(request):
    '''
    Adds an answer from a user to an article
    '''
    try:
        article_pk = request.GET['article']
    except KeyError:
        raise Http404
    
    g_article = get_object_or_404(Article, pk=article_pk)
    
    reactions = Reaction.objects.filter(article=g_article).order_by('-pubdate')[:3]
    
    if g_article.last_reaction:
        last_reaction_pk = g_article.last_reaction.pk
    else:
        last_reaction_pk=0

    # Making sure reactioning is allowed
    if g_article.is_locked:
        raise Http404

    # Check that the user isn't spamming
    if g_article.antispam(request.user):
        raise Http404

    # If we just sent data
    if request.method == 'POST':
        data = request.POST
        newreaction = last_reaction_pk != int(data['last_reaction'])

        # Using the « preview button », the « more » button or new reaction
        if 'preview' in data or 'more' in data or newreaction:
            return render_template('article/answer.html', {
                'text': data['text'], 'article': g_article, 'reactions': reactions,
                'last_reaction_pk': last_reaction_pk, 'newreaction': newreaction
            })

        # Saving the message
        else:
            form = ReactionForm(request.POST)
            if form.is_valid() and data['text'].strip() !='':
                data = form.data

                reaction = Reaction()
                reaction.article = g_article
                reaction.author = request.user
                reaction.text = data['text']
                reaction.text_html = emarkdown(data['text'])
                reaction.pubdate = datetime.now()
                reaction.position = g_article.get_reaction_count() + 1
                reaction.ip_address = get_client_ip(request)
                reaction.save()

                g_article.last_reaction = reaction
                g_article.save()

                return redirect(reaction.get_absolute_url())
            else:
                raise Http404

    else:
        text = ''

        # Using the quote button
        if 'cite' in request.GET:
            reaction_cite_pk = request.GET['cite']
            reaction_cite = Reaction.objects.get(pk=reaction_cite_pk)

            for line in reaction_cite.text.splitlines():
                text = text + '> ' + line + '\n'

            text = u'**{0} a écrit :**\n{1}\n'.format(
                reaction_cite.author.username, text)

        return render_template('article/answer.html', {
            'article': g_article, 'text': text, 'reactions': reactions,
            'last_reaction_pk': last_reaction_pk
        })

@can_write_and_read_now
@login_required
def edit_reaction(request):
    '''
    Edit the given user's reaction
    '''
    
    try:
        reaction_pk = request.GET['message']
    except KeyError:
        raise Http404

    reaction = get_object_or_404(Reaction, pk=reaction_pk)

    g_article = None
    if reaction.position >= 1:
        g_article = get_object_or_404(Article, pk=reaction.article.pk)

    # Making sure the user is allowed to do that
    if reaction.author != request.user:
        if request.method == 'GET' and request.user.has_perm('article.change_reaction'):
            messages.add_message(
                request, messages.WARNING,
                u'Vous éditez ce message en tant que modérateur (auteur : {}).'
                u' Soyez encore plus prudent lors de l\'édition de celui-ci !'
                .format(reaction.author.username))
            reaction.alerts.all().delete()

    if request.method == 'POST':
        
        if 'delete-reaction' in request.POST:
            if reaction.author == request.user or request.user.has_perm('article.change_reaction'):
                reaction.alerts.all().delete()
                reaction.is_visible=False
                if request.user.has_perm('article.change_reaction'):
                    reaction.text_hidden=request.POST['text_hidden']
                reaction.editor = request.user
            
        if 'show-reaction' in request.POST:
            if request.user.has_perm('article.change_reaction'):
                reaction.is_visible=True
                reaction.text_hidden=''
                    
        if 'signal-reaction' in request.POST:
            if reaction.author != request.user :
                alert = Alert()
                alert.author = request.user
                alert.text=request.POST['signal-text']
                alert.pubdate = datetime.now()
                alert.save()
                reaction.alerts.add(alert)
        # Using the preview button
        if 'preview' in request.POST:
            return render_template('article/edit_reaction.html', {
                'reaction': reaction, 'article': g_article, 'text': request.POST['text'],
            })
        
        if not 'delete-reaction' in request.POST and not 'signal-reaction' in request.POST and not 'show-reaction' in request.POST:
            # The user just sent data, handle them
            if request.POST['text'].strip() !='':
                reaction.text = request.POST['text']
                reaction.text_html = emarkdown(request.POST['text'])
                reaction.update = datetime.now()
                reaction.editor = request.user
        
        reaction.save()
        
        return redirect(reaction.get_absolute_url())

    else:
        return render_template('article/edit_reaction.html', {
            'reaction': reaction, 'article': g_article, 'text': reaction.text
        })


@can_write_and_read_now
@login_required
def like_reaction(request):
    '''Like a reaction'''
    
    try:
        reaction_pk = request.GET['message']
    except KeyError:
        raise Http404

    resp = {}
    reaction = get_object_or_404(Reaction, pk=reaction_pk)
    user = request.user
    
    if reaction.author.pk != request.user.pk:
        # Making sure the user is allowed to do that
        if CommentLike.objects.filter(user__pk=user.pk, comments__pk=reaction_pk).count()==0:
            like=CommentLike()
            like.user=user
            like.comments=reaction
            reaction.like=reaction.like+1
            reaction.save()
            like.save()
            if CommentDislike.objects.filter(user__pk=user.pk, comments__pk=reaction_pk).count()>0:
                CommentDislike.objects.filter(user__pk=user.pk, comments__pk=reaction_pk).all().delete()
                reaction.dislike=reaction.dislike-1
                reaction.save()
        else:
            CommentLike.objects.filter(user__pk=user.pk, comments__pk=reaction_pk).all().delete()
            reaction.like=reaction.like-1
            reaction.save()
            
    resp['upvotes'] = reaction.like
    resp['downvotes'] = reaction.dislike
    
    if request.is_ajax():
        return HttpResponse(json.dumps(resp))
    else:
        return redirect(reaction.get_absolute_url())

@can_write_and_read_now
@login_required
def dislike_reaction(request):
    '''Dislike a reaction'''
    
    try:
        reaction_pk = request.GET['message']
    except KeyError:
        raise Http404

    reaction = get_object_or_404(Reaction, pk=reaction_pk)
    user = request.user

    if reaction.author.pk != request.user.pk:
        # Making sure the user is allowed to do that
        if CommentDislike.objects.filter(user__pk=user.pk, comments__pk=reaction_pk).count()==0:
            dislike=CommentDislike()
            dislike.user=user
            dislike.comments=reaction
            reaction.dislike=reaction.dislike+1
            reaction.save()
            dislike.save()
            if CommentLike.objects.filter(user__pk=user.pk, comments__pk=reaction_pk).count()>0:
                CommentLike.objects.filter(user__pk=user.pk, comments__pk=reaction_pk).all().delete()
                reaction.like=reaction.like-1
                reaction.save()
        else :
            CommentDislike.objects.filter(user__pk=user.pk, comments__pk=reaction_pk).all().delete()
            reaction.dislike=reaction.dislike-1
            reaction.save()

    return redirect(reaction.get_absolute_url())
    
# Deprecated URLs

def deprecated_view_redirect(request, article_pk, article_slug):
    article = get_object_or_404(Article, pk=article_pk)
    return redirect(article.get_absolute_url(), permanent=True)
