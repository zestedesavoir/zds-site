# coding: utf-8

from datetime import datetime
from operator import attrgetter
from zds.member.models import Profile

try:
    import ujson as json_reader
except ImportError:
    try:
        import simplejson as json_reader
    except ImportError:
        import json as json_reader
import json as json_writter
import os
import shutil
import zipfile
import tempfile

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Q
from django.http import Http404, HttpResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render, render_to_response
from django.utils.encoding import smart_str
from django.views.decorators.http import require_POST
from git import Repo, Actor

from zds.member.decorator import can_write_and_read_now
from zds.member.views import get_client_ip
from zds.utils import slugify
from zds.utils.articles import get_blob
from zds.utils.mps import send_mp
from zds.utils.models import SubCategory, Category, CommentLike, \
    CommentDislike, Alert, Licence
from zds.utils.paginator import paginator_range
from zds.utils.tutorials import get_sep, get_text_is_empty
from zds.utils.templatetags.emarkdown import emarkdown
from django.utils.translation import ugettext_lazy as _

from .forms import ArticleForm, ReactionForm, ActivJsForm
from .models import Article, get_prev_article, get_next_article, Validation, \
    Reaction, never_read, mark_read


def index(request):
    """Display all public articles of the website."""
    # The tag indicate what the category article the user would
    # like to display. We can display all subcategories for articles.
    try:
        tag = get_object_or_404(SubCategory, slug=request.GET['tag'])
    except (KeyError, Http404):
        tag = None

    if tag is None:
        articles = Article.objects\
            .filter(sha_public__isnull=False).exclude(sha_public="")\
            .order_by('-pubdate')\
            .all()
    else:
        # The tag isn't None and exist in the system. We can use it to retrieve
        # all articles in the subcategory specified.
        articles = Article.objects\
            .filter(sha_public__isnull=False, subcategory__in=[tag])\
            .exclude(sha_public="").order_by('-pubdate')\
            .all()

    article_versions = []
    for article in articles:
        article_version = article.load_json_for_public()
        article_version = article.load_dic(article_version)
        article_versions.append(article_version)

    return render(request, 'article/index.html', {
        'articles': article_versions,
        'tag': tag,
    })


@login_required
def view(request, article_pk, article_slug):
    """Show the given offline article if exists."""
    article = get_object_or_404(Article, pk=article_pk)

    # Only authors of the article and staff can view article in offline.
    if request.user not in article.authors.all():
        if not request.user.has_perm('article.change_article'):
            raise PermissionDenied

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
    article_version['txt'] = get_blob(repo.commit(sha).tree, article_version['text'])
    article_version = article.load_dic(article_version)

    validation = Validation.objects.filter(article__pk=article.pk)\
        .order_by("-date_proposition")\
        .first()

    if article.js_support:
        is_js = "js"
    else:
        is_js = ""
    form_js = ActivJsForm(initial={"js_support": article.js_support})

    return render(request, 'article/member/view.html', {
        'article': article_version,
        'authors': article.authors,
        'tags': article.subcategory,
        'version': sha,
        'validation': validation,
        'is_js': is_js,
        'formJs': form_js,
        'on_line': False
    })


def view_online(request, article_pk, article_slug):
    """Show the given article if exists and is visible."""
    article = Article.objects\
        .prefetch_related("authors")\
        .prefetch_related("authors__profile")\
        .prefetch_related("subcategory")\
        .select_related('licence')\
        .select_related('last_reaction')\
        .filter(pk=article_pk)\
        .first()
    if article is None:
        raise Http404("pk {} not found".format(article_pk))
    # article is not online = 404
    if not article.on_line():
        raise Http404("article is offline.")

    # Load the article.
    article_version = article.load_json_for_public()
    txt = open(os.path.join(article.get_path(),
                            article_version['text'] + '.html'),
               "r")
    article_version['txt'] = txt.read()
    txt.close()
    article_version = article.load_dic(article_version)

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
        .select_related('author__profile')\
        .prefetch_related('alerts')\
        .prefetch_related('alerts__author')\
        .prefetch_related('alerts__author__profile')\
        .filter(article__pk=article.pk)\
        .order_by('position')\
        .all()
    reaction_ids = [post.pk for post in reactions]
    user_dislike = CommentDislike.objects\
        .select_related('comment')\
        .filter(user__pk=request.user.pk, comments__pk__in=reaction_ids)\
        .values_list('pk', flat=True)
    user_like = CommentLike.objects\
        .select_related('comment')\
        .filter(user__pk=request.user.pk, comments__pk__in=reaction_ids)\
        .values_list('pk', flat=True)
    # Check if the author is reachable
    authors_reachable_request = Profile.objects.contactable_members().filter(user__in=article.authors.all())
    authors_reachable = []
    for author in authors_reachable_request:
        authors_reachable.append(author.user)

    # Retrieve pk of the last reaction. If there aren't reactions
    # for the article, we initialize this last reaction at 0.
    last_reaction_pk = 0
    if article.last_reaction:
        last_reaction_pk = article.last_reaction.pk

    # Handle pagination.
    paginator = Paginator(reactions, settings.ZDS_APP['forum']['posts_per_page'])

    try:
        page_nbr = int(request.GET['page'])
    except KeyError:
        page_nbr = 1
    except ValueError:
        raise Http404

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

    return render(request, 'article/view.html', {
        'article': article_version,
        'authors': article.authors,
        'tags': article.subcategory,
        'prev': get_prev_article(article),
        'next': get_next_article(article),
        'reactions': res,
        'pages': paginator_range(page_nbr, paginator.num_pages),
        'nb': page_nbr,
        'last_reaction_pk': last_reaction_pk,
        'form': form,
        'on_line': True,
        'authors_reachable': authors_reachable,
        'is_staff': request.user.has_perm('article.change_article'),
        'user_like': user_like,
        'user_dislike': user_dislike
    })


@login_required
@require_POST
def warn_typo(request, article_pk):
    """Warn author(s) about a mistake in its (their) article by sending him/her (them) a private message."""

    # Need profile
    profile = get_object_or_404(Profile, user=request.user)

    # Get article
    try:
        article_pk = int(article_pk)
    except (KeyError, ValueError):
        raise Http404

    article = get_object_or_404(Article, pk=article_pk)

    # Check if the article is published
    if article.sha_public is None:
        raise Http404

    # Check if authors are reachable
    authors_reachable = Profile.objects.contactable_members().filter(user__in=article.authors.all())
    authors = []
    for author in authors_reachable:
        authors.append(author.user)

    if len(authors) == 0:
        if article.authors.count() > 1:
            messages.error(request, _(u"Les auteurs de l'article sont malheureusement injoignables"))
        else:
            messages.error(request, _(u"L'auteur de l'article est malheureusement injoignable"))
    else:
        # Fetch explanation
        if 'explication' not in request.POST or not request.POST['explication'].strip():
            messages.error(request, _(u'Votre proposition de correction est vide'))
        else:
            explanation = request.POST['explication']
            explanation = '\n'.join(['> ' + line for line in explanation.split('\n')])

            # Is the user trying to send PM to himself ?
            if request.user in article.authors.all():
                messages.error(request, _(u'Impossible d\'envoyer la correction car vous êtes l\'auteur '
                                          u'de cet article !'))
            else:
                # Create message :
                msg = _(u'[{}]({}) souhaite vous proposer une correction pour votre article [{}]({}).\n\n').format(
                    request.user.username,
                    settings.ZDS_APP['site']['url'] + profile.get_absolute_url(),
                    article.title,
                    settings.ZDS_APP['site']['url'] + article.get_absolute_url_online()
                )

                msg += _(u'Voici son message :\n\n{}').format(explanation)

                # Send it
                send_mp(request.user,
                        article.authors.all(),
                        _(u"Proposition de correction"),
                        article.title,
                        msg,
                        leave=False)
                messages.success(request, _(u'Votre correction a bien été proposée !'))

    # return to page :
    return redirect(article.get_absolute_url_online())


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
                'subcategory': request.POST.getlist('subcategory'),
                'licence': request.POST['licence'],
                'msg_commit': request.POST['msg_commit']
            })
            return render(request, 'article/member/new.html', {
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

            # add a licence to the article
            if "licence" in data and data["licence"] != "":
                lc = Licence.objects.filter(pk=data["licence"]).all()[0]
                article.licence = lc
            else:
                article.licence = Licence.objects.get(
                    pk=settings.ZDS_APP['tutorial']['default_license_pk']
                )

            article.save()

            maj_repo_article(request,
                             new_slug_path=article.get_path(),
                             article=article,
                             text=data['text'],
                             action='add',
                             msg=request.POST.get('msg_commit', None))
            return redirect(article.get_absolute_url())
    else:
        form = ArticleForm(
            initial={
                'licence': Licence.objects.get(pk=settings.ZDS_APP['tutorial']['default_license_pk'])
            }
        )

    return render(request, 'article/member/new.html', {
        'form': form
    })


@can_write_and_read_now
@login_required
def edit(request):
    """Edit article identified by given GET parameter."""
    try:
        article_pk = int(request.GET['article'])
    except (KeyError, ValueError):
        raise Http404

    article = get_object_or_404(Article, pk=article_pk)

    # Only authors of the article and staff can edit article.
    if request.user not in article.authors.all():
        if not request.user.has_perm('article.change_article'):
            raise PermissionDenied

    json = article.load_json()
    if request.method == 'POST':
        # Using the "preview button"
        if 'preview' in request.POST:
            image = None
            licence = None
            if 'image' in request.FILES:
                image = request.FILES['image']
            if 'licence' in request.POST:
                licence = request.POST['licence']
            form = ArticleForm(initial={
                'title': request.POST['title'],
                'description': request.POST['description'],
                'text': request.POST['text'],
                'image': image,
                'subcategory': request.POST.getlist('subcategory'),
                'licence': licence,
                'msg_commit': request.POST['msg_commit']
            })
            form_js = ActivJsForm(initial={"js_support": article.js_support})
            return render(request, 'article/member/edit.html', {
                'article': article,
                'text': request.POST['text'],
                'form': form,
                'formJs': form_js
            })

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

            if "licence" in data:
                if data["licence"] != "":
                    lc = Licence.objects.filter(pk=data["licence"]).all()[0]
                    article.licence = lc
                else:
                    article.licence = Licence.objects.get(
                        pk=settings.ZDS_APP['tutorial']['default_license_pk']
                    )

            article.save()

            new_slug = os.path.join(
                settings.ZDS_APP['article']['repo_path'],
                article.get_phy_slug())

            maj_repo_article(request,
                             old_slug_path=old_slug,
                             new_slug_path=new_slug,
                             article=article,
                             text=data['text'],
                             action='maj',
                             msg=request.POST.get('msg_commit', None))

            return redirect(article.get_absolute_url())
    else:
        if "licence" in json:
            licence = json['licence']
        else:
            licence = Licence.objects.get(
                pk=settings.ZDS_APP['tutorial']['default_license_pk']
            )
        form = ArticleForm(initial={
            'title': json['title'],
            'description': json['description'],
            'text': article.get_text(),
            'subcategory': article.subcategory.all(),
            'licence': licence
        })

    form_js = ActivJsForm(initial={"js_support": article.js_support})
    return render(request, 'article/member/edit.html', {
        'article': article, 'form': form, 'formJs': form_js, 'authors': article.authors,
    })


def find_article(request, pk_user):
    """Find an article from his author."""
    user = get_object_or_404(User, pk=pk_user)
    articles = Article.objects\
        .filter(authors__in=[user], sha_public__isnull=False).exclude(sha_public="")\
        .order_by('-pubdate')\
        .all()

    article_versions = []
    for article in articles:
        article_version = article.load_json_for_public()
        article_version = article.load_dic(article_version)
        article_versions.append(article_version)

    # Paginator
    return render(request, 'article/find.html', {
        'articles': article_versions, 'usr': user,
    })


def maj_repo_article(
        request,
        old_slug_path=None,
        new_slug_path=None,
        article=None,
        text=None,
        action=None,
        msg=None,):

    article.update = datetime.now()

    if action == 'del':
        shutil.rmtree(old_slug_path)
    else:
        if action == 'maj':
            if old_slug_path != new_slug_path:
                shutil.move(old_slug_path, new_slug_path)
                repo = Repo(new_slug_path)
            msg = u"Modification de l'article «{}» {} {}".format(article.title, get_sep(msg), get_text_is_empty(msg))\
                .strip()
        elif action == 'add':
            os.makedirs(new_slug_path, mode=0o777)
            repo = Repo.init(new_slug_path, bare=False)
            msg = u"Création de l'article «{}» {} {}".format(article.title, get_sep(msg), get_text_is_empty(msg))\
                .strip()

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
            aut_email = "inconnu@{}".format(settings.ZDS_APP['site']['dns'])
        com = index.commit(msg,
                           author=Actor(aut_user, aut_email),
                           committer=Actor(aut_user, aut_email)
                           )
        article.sha_draft = com.hexsha
        article.save()


def insert_into_zip(zip_file, git_tree):
    """recursively add files from a git_tree to a zip archive"""
    for blob in git_tree.blobs:  # first, add files :
        zip_file.writestr(blob.path, blob.data_stream.read())
    if len(git_tree.trees) is not 0:  # then, recursively add dirs :
        for subtree in git_tree.trees:
            insert_into_zip(zip_file, subtree)


def download(request):
    """Download an article."""
    try:
        article_id = int(request.GET["article"])
    except (KeyError, ValueError):
        raise Http404
    article = get_object_or_404(Article, pk=article_id)
    repo_path = os.path.join(settings.ZDS_APP['article']['repo_path'], article.get_phy_slug())
    repo = Repo(repo_path)
    sha = article.sha_draft
    if 'online' in request.GET and article.on_line():
        sha = article.sha_public
    elif request.user not in article.authors.all():
        if not request.user.has_perm('article.change_article'):
            raise PermissionDenied  # Only authors can download draft version
    zip_path = os.path.join(tempfile.gettempdir(), article.slug + '.zip')
    zip_file = zipfile.ZipFile(zip_path, 'w')
    insert_into_zip(zip_file, repo.commit(sha).tree)
    zip_file.close()
    response = HttpResponse(open(zip_path, "rb").read(), content_type="application/zip")
    response["Content-Disposition"] = "attachment; filename={0}.zip".format(article.slug)
    os.remove(zip_path)
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

                comment_reject = '\n'.join(['> ' + line for line in validation.comment_validator.split('\n')])
                # send feedback
                msg = (
                    u'Désolé, le zeste **{0}** '
                    u'n\'a malheureusement pas passé l’étape de validation. '
                    u'Mais ne désespère pas, certaines corrections peuvent '
                    u'sûrement être faites pour l’améliorer et repasser la '
                    u'validation plus tard. Voici le message que [{1}]({2}), '
                    u'ton validateur t\'a laissé:\n\n`{3}`\n\nN\'hésite pas à '
                    u'lui envoyer un petit message pour discuter de la décision '
                    u'ou demander plus de détail si tout cela te semble '
                    u'injuste ou manque de clarté.'.format(
                        article.title,
                        validation.validator.username,
                        settings.ZDS_APP['site']['url'] + validation.validator.profile.get_absolute_url(),
                        comment_reject))
                bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
                send_mp(
                    bot,
                    article.authors.all(),
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
                               u"Vous devez avoir réservé cet article "
                               u"pour pouvoir le refuser.")
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

            validation = Validation.objects\
                .filter(article__pk=article.pk,
                        version=article.sha_validation)\
                .latest('date_proposition')

            if request.user == validation.validator:

                try:
                    mep(article, article.sha_validation)
                except UnicodeErrorInArticle as e:
                    messages.error(request, e)
                    return redirect(article.get_absolute_url() + '?version=' + validation.version)

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
                msg = (
                    u'Félicitations ! Le zeste [{0}]({1}) '
                    u'est maintenant publié ! Les lecteurs du monde entier '
                    u'peuvent venir le lire et réagir à son sujet. Je te conseille '
                    u'de rester à leur écoute afin d\'apporter des '
                    u'corrections/compléments. Un article vivant et à jour '
                    u'est bien plus lu qu\'un sujet abandonné !'.format(
                        article.title,
                        settings.ZDS_APP['site']['url'] + article.get_absolute_url_online()))
                bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
                send_mp(
                    bot,
                    article.authors.all(),
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
                               u"Vous devez avoir réservé cet article "
                               u"pour pouvoir le publier.")
                return redirect(
                    article.get_absolute_url() +
                    '?version=' +
                    validation.version)

    # User actions
    if request.user in article.authors.all() or request.user.has_perm('article.change_article'):
        if 'delete' in data:
            if article.authors.count() == 1:
                article.delete()
            else:
                article.authors.remove(request.user)

            return redirect(reverse('article-index'))

        # User would like to validate his article. So we must save the
        # current sha (version) of the article to his sha_validation.
        elif 'pending' in request.POST:
            old_validation = Validation.objects.filter(article__pk=article_pk,
                                                       status__in=['PENDING_V']).first()
            if old_validation is not None:
                old_validator = old_validation.validator
            else:
                old_validator = None
            # Delete old pending validation
            Validation.objects.filter(article__pk=article_pk,
                                      status__in=['PENDING', 'PENDING_V'])\
                .delete()

            # Create new validation
            validation = Validation()
            validation.status = 'PENDING'
            validation.article = article
            validation.date_proposition = datetime.now()
            validation.comment_authors = request.POST['comment']
            validation.version = request.POST['version']

            if old_validator is not None:
                validation.validator = old_validator
                validation.date_reserve
                bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
                msg = \
                    (u'Bonjour {0},\n\n'
                     u'L\'article *{1}* que tu as réservé a été mis à jour en zone de validation, '
                     u'pour retrouver les modifications qui ont été faites, je t\'invite à '
                     u'consulter l\'historique des versions.'
                     u'\n\nMerci'.format(old_validator.username, article.title))
                send_mp(
                    bot,
                    [old_validator],
                    u"Mise à jour d'article : {0}".format(article.title),
                    "En validation",
                    msg,
                    False,
                )

            validation.save()

            validation.article.sha_validation = request.POST['version']
            validation.article.save()

            return redirect(article.get_absolute_url())
        elif 'add_author' in request.POST:
            redirect_url = reverse('article-view', args=[
                article.pk,
                article.slug
            ])

            author_username = request.POST['author'].strip()
            author = None
            try:
                author = User.objects.get(username=author_username)
                if author.profile.is_private():
                    raise User.DoesNotExist
            except User.DoesNotExist:
                messages.error(request, _(u'Utilisateur inexistant ou introuvable.'))
                return redirect(redirect_url)

            article.authors.add(author)
            article.save()

            messages.success(
                request,
                u'L\'auteur {0} a bien été ajouté à '
                u'la rédaction de l\'article.'.format(
                    author.username))

            # send msg to new author

            msg = (
                u'Bonjour **{0}**,\n\n'
                u'Tu as été ajouté comme auteur de l\'article [{1}]({2}).\n'
                u'Tu peux retrouver cet article en [cliquant ici]({3}), ou *via* le lien "En rédaction" du menu '
                u'"Articles" sur la page de ton profil.\n\n'
                u'Tu peux maintenant commencer à rédiger !'.format(
                    author.username,
                    article.title,
                    settings.ZDS_APP['site']['url'] + article.get_absolute_url(),
                    settings.ZDS_APP['site']['url'] + reverse("member-articles"))
            )
            bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
            send_mp(
                bot,
                [author],
                u"Ajout en tant qu'auteur : {0}".format(article.title),
                "",
                msg,
                True,
                direct=False,
            )

            return redirect(redirect_url)

        elif 'remove_author' in request.POST:
            redirect_url = reverse('article-view', args=[
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
                u'L\'auteur {0} a bien été retiré de la rédaction de l\'article.'.format(
                    author.username))

            # send msg to removed author

            msg = (
                u'Bonjour **{0}**,\n\n'
                u'Tu as été supprimé des auteurs de l\'article [{1}]({2}). Tant qu\'il ne sera pas publié, tu ne '
                u'pourras plus y accéder.\n'.format(
                    author.username,
                    article.title,
                    settings.ZDS_APP['site']['url'] + article.get_absolute_url())
            )
            bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
            send_mp(
                bot,
                [author],
                u"Suppression des auteurs : {0}".format(article.title),
                "",
                msg,
                True,
                direct=False,
            )

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
        subcategory = get_object_or_404(SubCategory, pk=int(request.GET['subcategory']))
    except (KeyError, ValueError, Http404):
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
    return render(request, 'article/validation/index.html', {
        'validations': validations,
    })


@login_required
@permission_required('article.change_article', raise_exception=True)
def history_validation(request, article_pk):
    """History of the validation of an article."""
    article = get_object_or_404(Article, pk=article_pk)

    # Get subcategory to filter validations.
    try:
        subcategory = get_object_or_404(Category, pk=int(request.GET['subcategory']))
    except (KeyError, ValueError, Http404):
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

    return render(request, 'article/validation/history.html', {
        'validations': validations,
        'article': article,
        'authors': article.authors,
        'tags': article.subcategory,
    })


@permission_required('article.change_article', raise_exception=True)
@login_required
@require_POST
def reservation(request, validation_pk):
    """Display articles list in validation."""

    validation = get_object_or_404(Validation, pk=validation_pk)

    if validation.validator:
        validation.validator = None
        validation.date_reserve = None
        validation.status = 'PENDING'
        validation.save()

        return redirect(reverse('article-list-validation'))

    else:
        validation.validator = request.user
        validation.date_reserve = datetime.now()
        validation.status = 'RESERVED'
        validation.save()
        return redirect(
            validation.article.get_absolute_url() +
            '?version=' + validation.version
        )


@login_required
def history(request, article_pk, article_slug):
    """Display an article."""
    article = get_object_or_404(Article, pk=article_pk)

    if not article.on_line() \
       and not request.user.has_perm('article.change_article') \
       and request.user not in article.authors.all():
        raise Http404

    # Make sure the URL is well-formed
    if not article_slug == slugify(article.title):
        return redirect(article.get_absolute_url())

    repo = Repo(article.get_path())

    logs = repo.head.reference.log()
    logs = sorted(logs, key=attrgetter('time'), reverse=True)

    form_js = ActivJsForm(initial={"js_support": article.js_support})

    return render(request, 'article/member/history.html', {
        'article': article, 'logs': logs, 'formJs': form_js
    })


# Reactions at an article.
class UnicodeErrorInArticle(Exception):

    def __init__(self, *args, **kwargs):
        super(UnicodeErrorInArticle, self).__init__(*args, **kwargs)


def mep(article, sha):
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
    if article.js_support:
        is_js = "js"
    else:
        is_js = ""
    try:
        html_file.write(emarkdown(md_file_contenu, is_js))
    except (UnicodeError, UnicodeEncodeError):
        raise UnicodeErrorInArticle(
            u'Une erreur est survenue lors de la génération du HTML, vérifiez que le code markdown ne contient '
            u'pas d\'erreurs')
    html_file.close()


@can_write_and_read_now
@login_required
def answer(request):
    """Adds an answer from a user to an article."""
    try:
        article_pk = int(request.GET['article'])
    except (KeyError, ValueError):
        raise Http404

    # Retrieve current article.
    article = get_object_or_404(Article, pk=article_pk)

    # Making sure reactioning is allowed
    if article.is_locked:
        raise PermissionDenied

    # Check that the user isn't spamming
    if article.antispam(request.user):
        raise PermissionDenied

    # If there is a last reaction for the article, we save his pk.
    # Otherwise, we save 0.
    if article.last_reaction:
        last_reaction_pk = article.last_reaction.pk
    else:
        last_reaction_pk = 0

    # Retrieve lasts reactions of the current topic.
    reactions = Reaction.objects.filter(article=article) \
        .prefetch_related() \
        .order_by("-pubdate")[:settings.ZDS_APP['forum']['posts_per_page']]
    reaction_ids = reactions.values_list('pk', flat=True)
    user_dislike = CommentDislike.objects\
        .select_related('comment')\
        .filter(user__pk=request.user.pk, comments__pk__in=reaction_ids)\
        .values_list('pk', flat=True)
    user_like = CommentLike.objects\
        .select_related('comment')\
        .filter(user__pk=request.user.pk, comments__pk__in=reaction_ids)\
        .values_list('pk', flat=True)
    # User would like preview his post or post a new reaction on the article.
    if request.method == 'POST':
        data = request.POST

        if not request.is_ajax():
            newreaction = last_reaction_pk != int(data['last_reaction'])

        # Using the « preview button », the « more » button or new reaction
        if 'preview' in data or newreaction:
            if request.is_ajax():
                content = render_to_response('misc/previsualization.part.html', {'text': data['text']})
                return StreamingHttpResponse(content)
            else:
                form = ReactionForm(article, request.user, initial={
                    'text': data['text']
                })

                return render(request, 'article/reaction/new.html', {
                    'article': article,
                    'last_reaction_pk': last_reaction_pk,
                    'newreaction': newreaction,
                    'reactions': reactions,
                    'form': form,
                    'is_staff': request.user.has_perm('tutorial.change_article'),
                    'user_like': user_like,
                    'user_dislike': user_dislike
                })

        # Saving the message
        else:
            form = ReactionForm(article, request.user, request.POST)
            if form.is_valid():
                data = form.data

                reaction = Reaction()
                reaction.article = article
                reaction.author = request.user
                reaction.text = data['text']
                reaction.text_html = emarkdown(data['text'])
                reaction.pubdate = datetime.now()
                reaction.position = Reaction.objects.count_reactions(article) + 1
                reaction.ip_address = get_client_ip(request)
                reaction.save()

                article.last_reaction = reaction
                article.save()

                return redirect(reaction.get_absolute_url())
            else:
                return render(request, 'article/reaction/new.html', {
                    'article': article,
                    'last_reaction_pk': last_reaction_pk,
                    'newreaction': newreaction,
                    'reactions': reactions,
                    'form': form,
                    'is_staff': request.user.has_perm('tutorial.change_article'),
                    'user_like': user_like,
                    'user_dislike': user_dislike
                })

    # Actions from the editor render to new.html.
    else:
        text = ''

        # Using the quote button
        if 'cite' in request.GET:
            resp = {}
            try:
                reaction_cite_pk = int(request.GET['cite'])
            except ValueError:
                raise Http404
            reaction_cite = Reaction.objects.get(pk=reaction_cite_pk)
            if not reaction_cite.is_visible:
                raise PermissionDenied

            for line in reaction_cite.text.splitlines():
                text = text + '> ' + line + '\n'

            text = u'{0}Source:[{1}]({2}{3})'.format(
                text,
                reaction_cite.author.username,
                settings.ZDS_APP['site']['url'],
                reaction_cite.get_absolute_url())

            if request.is_ajax():
                resp["text"] = text
                return HttpResponse(json_writter.dumps(resp), content_type='application/json')

        form = ReactionForm(article, request.user, initial={
            'text': text
        })
        return render(request, 'article/reaction/new.html', {
            'article': article,
            'reactions': reactions,
            'last_reaction_pk': last_reaction_pk,
            'form': form,
            'is_staff': request.user.has_perm('tutorial.change_article'),
            'user_like': user_like,
            'user_dislike': user_dislike
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

    if "text" in request.POST and request.POST["text"] != "":
        bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
        msg = (u'Bonjour {0},\n\nVous recevez ce message car vous avez '
               u'signalé le message de *{1}*, dans l\'article [{2}]({3}). '
               u'Votre alerte a été traitée par **{4}** et il vous a laissé '
               u'le message suivant :\n\n> {5}\n\nToute l\'équipe de '
               u'la modération vous remercie !'.format(
                   alert.author.username,
                   reaction.author.username,
                   reaction.article.title,
                   settings.ZDS_APP['site']['url'] +
                   reaction.get_absolute_url(),
                   request.user.username,
                   request.POST['text']))
        send_mp(
            bot,
            [alert.author],
            u"Résolution d'alerte : {0}".format(reaction.article.title),
            "",
            msg,
            False
        )

    alert.delete()
    messages.success(
        request,
        u'L\'alerte a bien été résolue.')

    return redirect(reaction.get_absolute_url())


@login_required
@require_POST
def activ_js(request):

    # only for staff

    if not request.user.has_perm("tutorial.change_tutorial"):
        raise PermissionDenied
    article = get_object_or_404(Article, pk=request.POST["article"])
    article.js_support = "js_support" in request.POST
    article.save()

    return redirect(article.get_absolute_url())


@can_write_and_read_now
@login_required
def edit_reaction(request):
    """Edit the given user's reaction."""

    try:
        reaction_pk = int(request.GET['message'])
    except (KeyError, ValueError):
        raise Http404
    reaction = get_object_or_404(Reaction, pk=reaction_pk)

    g_article = None
    if reaction.position >= 1:
        g_article = get_object_or_404(Article, pk=reaction.article.pk)
    is_staff = request.user.has_perm('article.change_reaction')
    # Making sure the user is allowed to do that. Author of the reaction
    # must to be the user logged.
    if reaction.author != request.user \
            and not is_staff \
            and 'signal_message' not in request.POST:
        raise PermissionDenied

    if reaction.author != request.user \
            and request.method == 'GET' \
            and is_staff:
        messages.add_message(
            request, messages.WARNING,
            u'Vous éditez ce message en tant que modérateur (auteur : {}).'
            u' Soyez encore plus prudent lors de l\'édition de celui-ci !'
            .format(reaction.author.username))
        reaction.alerts.all().delete()

    if request.method == 'POST':

        if 'delete_message' in request.POST:
            if reaction.author == request.user \
                    or is_staff:
                reaction.alerts.all().delete()
                reaction.is_visible = False
                if is_staff:
                    reaction.text_hidden = request.POST['text_hidden']
                reaction.editor = request.user

        if 'show_message' in request.POST:
            if is_staff:
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
            if request.is_ajax():
                content = render_to_response('misc/previsualization.part.html', {'text': request.POST['text']})
                return StreamingHttpResponse(content)
            else:
                return render(request, 'article/reaction/edit.html', {
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
        return render(request, 'article/reaction/edit.html', {
            'reaction': reaction,
            'article': g_article,
            'form': form
        })


@can_write_and_read_now
@login_required
def like_reaction(request):
    """Like a reaction."""

    try:
        reaction_pk = int(request.GET['message'])
    except (KeyError, ValueError):
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
        return HttpResponse(json_writter.dumps(resp))
    else:
        return redirect(reaction.get_absolute_url())


@can_write_and_read_now
@login_required
def dislike_reaction(request):
    """Dislike a reaction."""

    try:
        reaction_pk = int(request.GET['message'])
    except (KeyError, ValueError):
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
        return HttpResponse(json_writter.dumps(resp))
    else:
        return redirect(reaction.get_absolute_url())

# Deprecated URLs


def deprecated_view_redirect(request, article_pk, article_slug):
    article = get_object_or_404(Article, pk=article_pk)
    return redirect(article.get_absolute_url(), permanent=True)
