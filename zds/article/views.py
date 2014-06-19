# coding: utf-8

from datetime import datetime
from operator import attrgetter
try:
    import ujson as json_reader
except:
    try:
        import simplejson as json_reader
    except:
        import json as json_reader

import json as json_writer
import os
import shutil

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.encoding import smart_str
from django.views.decorators.http import require_POST
from git import *

from zds.member.decorator import can_write_and_read_now
from zds.member.views import get_client_ip
from zds.utils import render_template
from zds.utils import slugify
from zds.utils.articles import *
from zds.utils.mps import send_mp
from zds.utils.models import SubCategory, Category, CommentLike, \
    CommentDislike, Alert
from zds.utils.paginator import paginator_range
from zds.utils.templatetags.emarkdown import emarkdown

from .forms import ArticleForm, ReactionForm
from .models import Article, get_prev_article, get_next_article, Validation, \
    Reaction, never_read, mark_read



def index(request):
    """Display all public articles of the website."""
    # The tag indicate what the category article the user would
    # like to display. We can display all subcategories for articles.
    try:
        tag = get_object_or_404(SubCategory, title=request.GET['tag'])
    except (KeyError, Http404):
        tag = None

    if tag is None:
        article = Article.objects\
            .filter(sha_public__isnull=False).exclude(sha_public="")\
            .order_by('-pubdate')\
            .all()
    else:
        # The tag isn't None and exist in the system. We can use it to retrieve
        # all articles in the subcategory specified.
        article = Article.objects\
            .filter(sha_public__isnull=False, subcategory__in=[tag])\
            .exclude(sha_public="").order_by('-pubdate')\
            .all()

    return render_template('article/index.html', {
        'articles': article,
    })



@login_required
def view(request, article_pk, article_slug):
    """Show the given offline article if exists."""
    article = get_object_or_404(Article, pk=article_pk)

    # Only authors of the article and staff can view article in offline.
    if request.user not in article.authors.all():
        if not request.user.has_perm('article.change_article'):
            raise PermissionDenied

    # The slug of the article must to be right.
    if article_slug != slugify(article.title):
        return redirect(article.get_absolute_url())

    # Retrieve sha given by the user. This sha must to be exist.
    # If it doesn't exist, we take draft version of the article.
    try:
        sha = request.GET['version']
    except KeyError:
        sha = article.sha_draft

    # Find the good manifest file
    repo = Repo(article.get_path())

    # Load the article.
    try:
        manifest = get_blob(repo.commit(sha).tree, 'manifest.json')
    except:
        sha = article.sha_draft
        manifest = get_blob(repo.commit(sha).tree, 'manifest.json')

    article_version = json_reader.loads(manifest)
    article_version['txt'] = get_blob(
        repo.commit(sha).tree,
        article_version['text'])
    article_version['pk'] = article.pk
    article_version['slug'] = article.slug
    article_version['image'] = article.image
    article_version['sha_draft'] = article.sha_draft
    article_version['sha_validation'] = article.sha_validation
    article_version['sha_public'] = article.sha_public
    article_version['get_absolute_url_online'] = article.get_absolute_url_online()

    validation = Validation.objects.filter(article__pk=article.pk,
                                            version=sha)\
                                    .order_by("-date_proposition")\
                                    .first()

    return render_template('article/member/view.html', {
        'article': article_version,
        'authors': article.authors,
        'tags': article.subcategory,
        'version': sha,
        'validation': validation
    })



def view_online(request, article_pk, article_slug):
    """Show the given article if exists and is visible."""
    article = get_object_or_404(Article, pk=article_pk)

    # The slug of the article must to be right.
    if article_slug != slugify(article.title):
        return redirect(article.get_absolute_url_online())

    # Load the article.
    article_version = article.load_json()
    txt = open(
        os.path.join(
            article.get_path(),
            article_version['text'] +
            '.html'),
        "r")
    article_version['txt'] = txt.read()
    txt.close()
    article_version['pk'] = article.pk
    article_version['slug'] = article.slug
    article_version['image'] = article.image
    article_version['thumbnail'] = article.thumbnail
    article_version['is_locked'] = article.is_locked
    article_version['get_absolute_url'] = article.get_absolute_url()
    article_version['get_absolute_url_online'] = article.get_absolute_url_online()

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
        .filter(article__pk=article.pk)\
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

    # Build form to send a reaction for the current article.
    form = ReactionForm(article, request.user)

    return render_template('article/view.html', {
        'article': article_version,
        'authors': article.authors,
        'tags': article.subcategory,
        'prev': get_prev_article(article),
        'next': get_next_article(article),
        'reactions': res,
        'pages': paginator_range(page_nbr, paginator.num_pages),
        'nb': page_nbr,
        'last_reaction_pk': last_reaction_pk,
        'form': form
    })


@can_write_and_read_now
@login_required
def new(request):
    """Create a new article."""
    if request.method == 'POST':
        # Using the "preview button"
        if 'preview' in request.POST:
            image = None
            if 'image' in request.FILES:
                image = request.FILES['image']
            form = ArticleForm(initial={
                'title': request.POST['title'],
                'description': request.POST['description'],
                'text': request.POST['text'],
                'image': image,
                'subcategory': request.POST.getlist('subcategory')
            })
            return render_template('article/new.html', {
                'text': request.POST['text'],
                'form': form
            })

        # Otherwise, the user would like submit his article.
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.data

            article = Article()
            article.title = data['title']
            article.description = data['description']
            article.text = "text.md"
            if 'image' in request.FILES:
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
                             article=article,
                             text=data['text'],
                             action='add')
            return redirect(article.get_absolute_url())
    else:
        form = ArticleForm()

    return render_template('article/member/new.html', {
        'form': form
    })


@can_write_and_read_now
@login_required
def edit(request):
    """Edit article identified by given GET parameter."""
    try:
        article_pk = request.GET['article']
    except KeyError:
        raise Http404

    article = get_object_or_404(Article, pk=article_pk)

    # Only authors of the article and staff can edit article.
    if request.user not in article.authors.all():
        if not request.user.has_perm('article.change_article'):
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

            new_slug = os.path.join(
                settings.REPO_ARTICLE_PATH,
                slugify(
                    data['title']))

            maj_repo_article(request,
                             old_slug_path=old_slug,
                             new_slug_path=new_slug,
                             article=article,
                             text=data['text'],
                             action='maj')

            return redirect(article.get_absolute_url())
    else:
        form = ArticleForm({
            'title': json['title'],
            'description': json['description'],
            'text': article.get_text(),
            'subcategory': article.subcategory.all(),
        })

    return render_template('article/member/edit.html', {
        'article': article, 'form': form
    })



def find_article(request, name):
    """Find an article from his author."""
    user = get_object_or_404(User, pk=name)
    articles = Article.objects\
        .filter(authors__in=[user], sha_public__isnull=False).exclude(sha_public="")\
        .order_by('-pubdate')\
        .all()
    # Paginator
    return render_template('article/find.html', {
        'articles': articles, 'usr': user,
    })


def maj_repo_article(
        request,
        old_slug_path=None,
        new_slug_path=None,
        article=None,
        text=None,
        action=None):

    if action == 'del':
        shutil.rmtree(old_slug_path)
    else:
        if action == 'maj':
            shutil.move(old_slug_path, new_slug_path)
            repo = Repo(new_slug_path)
            msg = 'Modification de l\'article'
        elif action == 'add':
            os.makedirs(new_slug_path, mode=0o777)
            repo = Repo.init(new_slug_path, bare=False)
            msg = 'Creation de l\'article'

        repo = Repo(new_slug_path)
        index = repo.index

        man_path = os.path.join(new_slug_path, 'manifest.json')
        article.dump_json(path=man_path)
        index.add(['manifest.json'])

        txt = open(os.path.join(new_slug_path, 'text.md'), "w")
        txt.write(smart_str(text).strip())
        txt.close()
        index.add(['text.md'])

        aut_user = str(request.user.pk)
        aut_email = str(request.user.email)
        if aut_email is None or aut_email.strip() == "":
            aut_email = "inconnu@zestedesavoir.com"
        com = index.commit(msg.encode('utf-8'),
                           author=Actor(aut_user, aut_email),
                           committer=Actor(aut_user, aut_email)
                           )
        article.sha_draft = com.hexsha
        article.save()



def download(request):
    """Download an article."""

    article = get_object_or_404(Article, pk=request.GET['article'])

    ph = os.path.join(settings.REPO_ARTICLE_PATH, article.slug)
    repo = Repo(ph)
    repo.archive(open(ph + ".tar", 'w'))

    response = HttpResponse(
        open(
            ph +
            ".tar",
            'rb').read(),
        mimetype='application/tar')
    response[
        'Content-Disposition'] = 'attachment; filename={0}.tar' \
        .format(article.slug)

    return response

# Validation


@can_write_and_read_now
@require_POST
@login_required
def modify(request):
    """Modify status of the article."""
    data = request.POST
    article_pk = data['article']
    article = get_object_or_404(Article, pk=article_pk)

    # Validator actions
    if request.user.has_perm('article.change_article'):

        # A validator would like to invalid an article in validation.
        # We must mark article rejected with the current sha of
        # validation.
        if 'reject-article' in request.POST:
            validation = Validation.objects\
                .filter(article__pk=article.pk,
                        version=article.sha_validation)\
                .latest('date_proposition')

            if request.user == validation.validator:
                validation.comment_validator = request.POST['comment-r']
                validation.status = 'REJECTED'
                validation.date_validation = datetime.now()
                validation.save()

                # Remove sha_validation because we rejected this version
                # of the article.
                article.sha_validation = None
                article.pubdate = None
                article.save()

                # send feedback
                for author in article.authors.all():
                    msg = u'Désolé **{0}**, ton zeste **{1}** '
                    u'n\'a malheureusement pas passé l’étape de validation. '
                    u'Mais ne désespère pas, certaines corrections peuvent '
                    u'surement être faite pour l’améliorer et repasser la '
                    u'validation plus tard. Voici le message que [{2}]({3}), '
                    u'ton validateur t\'a laissé\n\n`{4}`\n\nN\'hésite pas a '
                    u'lui envoyer un petit message pour discuter de la décision '
                    u'ou demander plus de détail si tout cela te semble '
                    u'injuste ou manque de clarté.'.format(
                        author.username,
                        article.title,
                        validation.validator.username,
                        validation.validator.profile.get_absolute_url(),
                        validation.comment_validator)
                    bot = get_object_or_404(User, username=settings.BOT_ACCOUNT)
                    send_mp(
                        bot,
                        [author],
                        u"Refus de Validation : {0}".format(
                            article.title),
                        "",
                        msg,
                        True,
                        direct=False)

                return redirect(
                    article.get_absolute_url() +
                    '?version=' +
                    validation.version)
            else:
                messages.error(request,
                    "Vous devez avoir réservé cet article "
                    "pour pouvoir le refuser.")
                return redirect(
                    article.get_absolute_url() +
                    '?version=' +
                    validation.version)

        # A validator would like to invalid an article published. We must
        # come back to sha_validation with the current sha of validation.
        elif 'invalid-article' in request.POST:
            validation = Validation.objects\
                .filter(article__pk=article.pk, version=article.sha_public)\
                .latest('date_proposition')
            validation.status = 'PENDING'
            validation.date_validation = None
            validation.save()

            # Only update sha_validation because contributors can
            # contribute on rereading version.
            article.sha_public = None
            article.sha_validation = validation.version
            article.pubdate = None
            article.save()

            return redirect(
                article.get_absolute_url() +
                '?version=' +
                validation.version)

        # A validatir would like to valid an article in validation. We
        # must update sha_public with the current sha of the validation.
        elif 'valid-article' in request.POST:
            MEP(article, article.sha_validation)
            validation = Validation.objects\
                .filter(article__pk=article.pk,
                        version=article.sha_validation)\
                .latest('date_proposition')

            if request.user == validation.validator:
                validation.comment_validator = request.POST['comment-v']
                validation.status = 'PUBLISHED'
                validation.date_validation = datetime.now()
                validation.save()

                # Update sha_public with the sha of validation.
                # We don't update sha_draft.
                # So, the user can continue to edit his article in offline.
                if request.POST.get('is_major', False) or article.sha_public is None:
                    article.pubdate = datetime.now()
                article.sha_public = validation.version
                article.sha_validation = None
                article.save()

                # send feedback
                for author in article.authors.all():
                    msg = u'Félicitations **{0}** ! Ton zeste [{1}]({2}) '
                    u'est maintenant publié ! Les lecteurs du monde entier '
                    u'peuvent venir le lire et réagir a son sujet. Je te conseille '
                    u'de rester a leur écoute afin d\'apporter des '
                    u'corrections/compléments. Un Article vivant et a jour '
                    u'est bien plus lu qu\'un sujet abandonné !'.format(
                        author.username,
                        article.title,
                        article.get_absolute_url_online())
                    bot = get_object_or_404(User, username=settings.BOT_ACCOUNT)
                    send_mp(
                        bot,
                        [author],
                        u"Publication : {0}".format(
                            article.title),
                        "",
                        msg,
                        True,
                        direct=False)

                return redirect(
                    article.get_absolute_url() +
                    '?version=' +
                    validation.version)
            else:
                messages.error(request,
                    "Vous devez avoir réservé cet article "
                    "pour pouvoir le publier.")
                return redirect(
                    article.get_absolute_url() +
                    '?version=' +
                    validation.version)

    # User actions
    if request.user in article.authors.all():
        if 'delete' in data:
            if article.authors.count() == 1:
                article.delete()
            else:
                article.authors.remove(request.user)

            return redirect(reverse('zds.article.views.index'))

        # User would like to validate his article. So we must save the
        # current sha (version) of the article to his sha_validation.
        elif 'pending' in request.POST and article.sha_validation is None:
            validation = Validation()
            validation.status = 'PENDING'
            validation.article = article
            validation.date_proposition = datetime.now()
            validation.comment_authors = request.POST['comment']
            validation.version = request.POST['version']

            validation.save()

            validation.article.sha_validation = request.POST['version']
            validation.article.save()

            return redirect(article.get_absolute_url())
        elif 'add_author' in request.POST:
            redirect_url = reverse('zds.article.views.view', args=[
                article.pk,
                article.slug
            ])

            author_username = request.POST['author']
            author = None
            try:
                author = User.objects.get(username=author_username)
            except User.DoesNotExist:
                return redirect(redirect_url)

            article.authors.add(author)
            article.save()

            messages.success(
                request,
                u'L\'auteur {0} a bien été ajouté à '
                u'la rédaction de l\'article.'.format(
                    author.username))

            return redirect(redirect_url)

        elif 'remove_author' in request.POST:
            redirect_url = reverse('zds.article.views.view', args=[
                article.pk,
                article.slug
            ])

            # Avoid orphan articles
            if article.authors.all().count() <= 1:
                raise Http404

            author_pk = request.POST['author']
            author = get_object_or_404(User, pk=author_pk)

            article.authors.remove(author)
            article.save()

            messages.success(
                request,
                u'L\'auteur {0} a bien été retiré de l\'article.'.format(
                    author.username))

            return redirect(redirect_url)

    return redirect(article.get_absolute_url())



@permission_required('article.change_article', raise_exception=True)
@login_required
def list_validation(request):
    """Display articles list in validation."""
    # Retrieve type of the validation. Default value is all validations.
    try:
        type = request.GET['type']
    except KeyError:
        type = None

    # Get subcategory to filter validations.
    try:
        subcategory = get_object_or_404(
            Category,
            pk=request.GET['subcategory'])
    except (KeyError, Http404):
        subcategory = None

    # Orphan validation. There aren't validator attached to the validations.
    if type == 'orphan':
        if subcategory is None:
            validations = Validation.objects \
                .filter(validator__isnull=True, status='PENDING') \
                .order_by("date_proposition") \
                .all()
        else:
            validations = Validation.objects \
                .filter(validator__isnull=True, status='PENDING',
                        article__subcategory__in=[subcategory]) \
                .order_by("date_proposition") \
                .all()

    # Reserved validation. There are a validator attached to the validations.
    elif type == 'reserved':
        if subcategory is None:
            validations = Validation.objects \
                .filter(validator__isnull=False, status='RESERVED') \
                .order_by("date_proposition") \
                .all()
        else:
            validations = Validation.objects \
                .filter(validator__isnull=False, status='PENDING',
                        article__subcategory__in=[subcategory]) \
                .order_by("date_proposition") \
                .all()

    # Default, we display all validations.
    else:
        if subcategory is None:
            validations = Validation.objects \
                .filter(Q(status='PENDING') | Q(status='RESERVED'))\
                .order_by("date_proposition") \
                .all()
        else:
            validations = Validation.objects \
                .filter(status='PENDING',
                        article__subcategory__in=[subcategory]) \
                .order_by("date_proposition") \
                .all()
    return render_template('article/validation/index.html', {
        'validations': validations,
    })



@login_required
@permission_required('article.change_article', raise_exception=True)
def history_validation(request, article_pk):
    """History of the validation of an article."""
    article = get_object_or_404(Article, pk=article_pk)

    # Get subcategory to filter validations.
    try:
        subcategory = get_object_or_404(
            Category,
            pk=request.GET['subcategory'])
    except (KeyError, Http404):
        subcategory = None

    if subcategory is None:
        validations = Validation.objects \
            .filter(article__pk=article_pk) \
            .order_by("date_proposition") \
            .all()
    else:
        validations = Validation.objects \
            .filter(article__pk=article_pk,
                    article__subcategory__in=[subcategory]) \
            .order_by("date_proposition") \
            .all()

    return render_template('article/validation/history.html', {
        'validations': validations,
        'article': article,
    })



@permission_required('article.change_article', raise_exception=True)
@login_required
def reservation(request, validation_pk):
    """Display articles list in validation."""

    validation = get_object_or_404(Validation, pk=validation_pk)

    if validation.validator:
        validation.validator = None
        validation.date_reserve = None
        validation.status = 'PENDING'
        validation.save()

        return redirect(reverse('zds.article.views.list_validation'))

    else:
        validation.validator = request.user
        validation.date_reserve = datetime.now()
        validation.status = 'RESERVED'
        validation.save()
        return redirect(validation.article.get_absolute_url())



@login_required
def history(request, article_pk, article_slug):
    """Display an article."""
    article = get_object_or_404(Article, pk=article_pk)

    if not article.on_line \
       and not request.user.has_perm('article.change_article') \
       and request.user not in article.authors.all():
        raise Http404

    # Make sure the URL is well-formed
    if not article_slug == slugify(article.title):
        return redirect(article.get_absolute_url())

    repo = Repo(article.get_path())

    logs = repo.head.reference.log()
    logs = sorted(logs, key=attrgetter('time'), reverse=True)

    return render_template('article/member/history.html', {
        'article': article, 'logs': logs
    })

# Reactions at an article.


def MEP(article, sha):
    # convert markdown file to html file
    repo = Repo(article.get_path())
    manifest = get_blob(repo.commit(sha).tree, 'manifest.json')

    article_version = json_reader.loads(manifest)
    md_file_contenu = get_blob(repo.commit(sha).tree, article_version['text'])

    html_file = open(
        os.path.join(
            article.get_path(),
            article_version['text'] +
            '.html'),
        "w")
    html_file.write(emarkdown(md_file_contenu))
    html_file.close()


@can_write_and_read_now
@login_required
def answer(request):
    """Adds an answer from a user to an article."""
    try:
        article_pk = request.GET['article']
    except KeyError:
        raise Http404

    # Retrieve current article.
    article = get_object_or_404(Article, pk=article_pk)

    # Making sure reactioning is allowed
    if article.is_locked:
        raise PermissionDenied

    # Check that the user isn't spamming
    if article.antispam(request.user):
        raise PermissionDenied

    # Retrieve 3 last reactions of the currenta article.
    reactions = Reaction.objects\
        .filter(article=article)\
        .order_by('-pubdate')[:3]

    # If there is a last reaction for the article, we save his pk.
    # Otherwise, we save 0.
    if article.last_reaction:
        last_reaction_pk = article.last_reaction.pk
    else:
        last_reaction_pk = 0

    # User would like preview his post or post a new reaction on the article.
    if request.method == 'POST':
        data = request.POST
        newreaction = last_reaction_pk != int(data['last_reaction'])

        # Using the « preview button », the « more » button or new reaction
        if 'preview' in data or newreaction:
            form = ReactionForm(article, request.user, initial={
                'text': data['text']
            })
            return render_template('article/reaction/new.html', {
                'article': article,
                'last_reaction_pk': last_reaction_pk,
                'newreaction': newreaction,
                'form': form
            })

        # Saving the message
        else:
            form = ReactionForm(article, request.user, request.POST)
            if form.is_valid() and data['text'].strip() != '':
                data = form.data

                reaction = Reaction()
                reaction.article = article
                reaction.author = request.user
                reaction.text = data['text']
                reaction.text_html = emarkdown(data['text'])
                reaction.pubdate = datetime.now()
                reaction.position = article.get_reaction_count() + 1
                reaction.ip_address = get_client_ip(request)
                reaction.save()

                article.last_reaction = reaction
                article.save()

                return redirect(reaction.get_absolute_url())
            else:
                raise Http404

    # Actions from the editor render to new.html.
    else:
        text = ''

        # Using the quote button
        if 'cite' in request.GET:
            reaction_cite_pk = request.GET['cite']
            reaction_cite = Reaction.objects.get(pk=reaction_cite_pk)
            if not reaction_cite.is_visible:
                raise PermissionDenied

            for line in reaction_cite.text.splitlines():
                text = text + '> ' + line + '\n'

            text = u'{0}Source:[{1}]({2})'.format(
                text,
                reaction_cite.author.username,
                reaction_cite.get_absolute_url())

        form = ReactionForm(article, request.user, initial={
            'text': text
        })
        return render_template('article/reaction/new.html', {
            'article': article,
            'reactions': reactions,
            'last_reaction_pk': last_reaction_pk,
            'form': form
        })


@can_write_and_read_now
@login_required
@require_POST
@transaction.atomic
def solve_alert(request):
    # only staff can move topic
    if not request.user.has_perm('article.change_reaction'):
        raise PermissionDenied

    alert = get_object_or_404(Alert, pk=request.POST['alert_pk'])
    reaction = Reaction.objects.get(pk=alert.comment.id)
    bot = get_object_or_404(User, username=settings.BOT_ACCOUNT)
    msg = u'Bonjour {0},\n\nVous recevez ce message car vous avez '
    u'signalé le message de *{1}*, dans l\'article [{2}]({3}). '
    u'Votre alerte a été traitée par **{4}** et il vous a laissé '
    u'le message suivant :\n\n`{5}`\n\n\nToute l\'équipe de '
    u'la modération vous remercie'.format(
        alert.author.username,
        reaction.author.username,
        reaction.article.title,
        settings.SITE_URL +
        reaction.get_absolute_url(),
        request.user.username,
        request.POST['text'])
    send_mp(
        bot, [
            alert.author], u"Résolution d'alerte : {0}".format(
            reaction.article.title), "", msg, False)
    alert.delete()

    messages.success(
        request,
        u'L\'alerte a bien été résolue')

    return redirect(reaction.get_absolute_url())


@can_write_and_read_now
@login_required
def edit_reaction(request):
    """Edit the given user's reaction."""

    try:
        reaction_pk = request.GET['message']
    except KeyError:
        raise Http404
    reaction = get_object_or_404(Reaction, pk=reaction_pk)

    g_article = None
    if reaction.position >= 1:
        g_article = get_object_or_404(Article, pk=reaction.article.pk)

    # Making sure the user is allowed to do that. Author of the reaction
    # must to be the user logged.
    if reaction.author != request.user \
            and not request.user.has_perm('article.change_reaction') \
            and 'signal_message' not in request.POST:
        raise PermissionDenied

    if reaction.author != request.user \
            and request.method == 'GET' \
            and request.user.has_perm('article.change_reaction'):
        messages.add_message(
            request, messages.WARNING,
            u'Vous éditez ce message en tant que modérateur (auteur : {}).'
            u' Soyez encore plus prudent lors de l\'édition de celui-ci !'
            .format(reaction.author.username))
        reaction.alerts.all().delete()

    if request.method == 'POST':

        if 'delete_message' in request.POST:
            if reaction.author == request.user \
                    or request.user.has_perm('article.change_reaction'):
                reaction.alerts.all().delete()
                reaction.is_visible = False
                if request.user.has_perm('article.change_reaction'):
                    reaction.text_hidden = request.POST['text_hidden']
                reaction.editor = request.user

        if 'show_message' in request.POST:
            if request.user.has_perm('article.change_reaction'):
                reaction.is_visible = True
                reaction.text_hidden = ''

        if 'signal_message' in request.POST:
            alert = Alert()
            alert.author = request.user
            alert.comment = reaction
            alert.scope = Alert.ARTICLE
            alert.text = request.POST['signal_text']
            alert.pubdate = datetime.now()
            alert.save()

        # Using the preview button
        if 'preview' in request.POST:
            form = ReactionForm(g_article, request.user, initial={
                'text': request.POST['text']
            })
            form.helper.form_action = reverse(
                'zds.article.views.edit_reaction') + \
                '?message=' + \
                str(reaction_pk)
            return render_template('article/reaction/edit.html', {
                'reaction': reaction,
                'article': g_article,
                'form': form
            })

        if 'delete_message' not in request.POST \
                and 'signal_message' not in request.POST \
                and 'show_message' not in request.POST:
            # The user just sent data, handle them
            if request.POST['text'].strip() != '':
                reaction.text = request.POST['text']
                reaction.text_html = emarkdown(request.POST['text'])
                reaction.update = datetime.now()
                reaction.editor = request.user

        reaction.save()

        return redirect(reaction.get_absolute_url())

    else:
        form = ReactionForm(g_article, request.user, initial={
            'text': reaction.text
        })
        form.helper.form_action = reverse(
            'zds.article.views.edit_reaction') + '?message=' + str(reaction_pk)
        return render_template('article/reaction/edit.html', {
            'reaction': reaction,
            'article': g_article,
            'form': form
        })


@can_write_and_read_now
@login_required
def like_reaction(request):
    """Like a reaction."""

    try:
        reaction_pk = request.GET['message']
    except KeyError:
        raise Http404

    resp = {}
    reaction = get_object_or_404(Reaction, pk=reaction_pk)
    user = request.user

    if reaction.author.pk != request.user.pk:
        # Making sure the user is allowed to do that
        if CommentLike.objects.filter(user__pk=user.pk,
                                      comments__pk=reaction_pk).count() == 0:
            like = CommentLike()
            like.user = user
            like.comments = reaction
            reaction.like = reaction.like + 1
            reaction.save()
            like.save()
            if CommentDislike.objects.filter(user__pk=user.pk,
                                             comments__pk=reaction_pk) \
                    .count() > 0:
                CommentDislike.objects.filter(
                    user__pk=user.pk,
                    comments__pk=reaction_pk).all().delete()
                reaction.dislike = reaction.dislike - 1
                reaction.save()
        else:
            CommentLike.objects.filter(
                user__pk=user.pk,
                comments__pk=reaction_pk).all().delete()
            reaction.like = reaction.like - 1
            reaction.save()

    resp['upvotes'] = reaction.like
    resp['downvotes'] = reaction.dislike

    if request.is_ajax():
        return HttpResponse(json_writer.dumps(resp))
    else:
        return redirect(reaction.get_absolute_url())


@can_write_and_read_now
@login_required
def dislike_reaction(request):
    """Dislike a reaction."""

    try:
        reaction_pk = request.GET['message']
    except KeyError:
        raise Http404
    resp = {}
    reaction = get_object_or_404(Reaction, pk=reaction_pk)
    user = request.user

    if reaction.author.pk != request.user.pk:
        # Making sure the user is allowed to do that
        if CommentDislike.objects.filter(user__pk=user.pk,
                                         comments__pk=reaction_pk) \
                .count() == 0:
            dislike = CommentDislike()
            dislike.user = user
            dislike.comments = reaction
            reaction.dislike = reaction.dislike + 1
            reaction.save()
            dislike.save()
            if CommentLike.objects.filter(user__pk=user.pk,
                                          comments__pk=reaction_pk) \
                    .count() > 0:
                CommentLike.objects.filter(
                    user__pk=user.pk,
                    comments__pk=reaction_pk).all().delete()
                reaction.like = reaction.like - 1
                reaction.save()
        else:
            CommentDislike.objects.filter(
                user__pk=user.pk,
                comments__pk=reaction_pk).all().delete()
            reaction.dislike = reaction.dislike - 1
            reaction.save()

    resp['upvotes'] = reaction.like
    resp['downvotes'] = reaction.dislike

    if request.is_ajax():
        return HttpResponse(json_writer.dumps(resp))
    else:
        return redirect(reaction.get_absolute_url())

# Deprecated URLs


def deprecated_view_redirect(request, article_pk, article_slug):
    article = get_object_or_404(Article, pk=article_pk)
    return redirect(article.get_absolute_url(), permanent=True)
