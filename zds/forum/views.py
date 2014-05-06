# coding: utf-8

from datetime import datetime
from django.conf import settings
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import transaction
from django.http import Http404, HttpResponse
from django.views.decorators.http import require_POST
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, get_object_or_404

from .forms import TopicForm, PostForm, MoveTopicForm
from .models import Category, Forum, Topic, Post, follow, never_read, mark_read, TopicFollowed, TopicRead
from zds.member.decorator import can_read_now, can_write_and_read_now
from zds.member.views import get_client_ip
from zds.utils import render_template, slugify
from zds.utils.models import Alert, CommentLike, CommentDislike
from zds.utils.mps import send_mp
from zds.utils.paginator import paginator_range
from zds.utils.templatetags.emarkdown import emarkdown

from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.views.decorators.cache import cache_page


@cache_page(60 * 2)
@can_read_now
def index(request):
    """Display the category list with all their forums."""
    categories = Category.objects.order_by('position').all()

    return render_template('forum/index.html', {
        'categories': categories,
        'user': request.user
    })


@can_read_now
def details(request, cat_slug, forum_slug):
    """Display the given forum and all its topics."""
    forum = get_object_or_404(Forum, slug=forum_slug)

    if not forum.can_read(request.user):
        raise PermissionDenied

    sticky_topics = Topic.objects\
        .filter(forum__pk=forum.pk, is_sticky=True)\
        .order_by('-last_message__pubdate')\
        .all()
    if 'filter' in request.GET:
        if request.GET['filter'] == 'solve':
            topics = Topic.objects\
                .filter(forum__pk=forum.pk, is_sticky=False, is_solved=True)\
                .order_by('-last_message__pubdate')\
                .all()
        else :
            topics = Topic.objects\
                .filter(forum__pk=forum.pk, is_sticky=False, is_solved=False)\
                .order_by('-last_message__pubdate')\
                .all()
    else:
        topics = Topic.objects\
            .filter(forum__pk=forum.pk, is_sticky=False)\
            .order_by('-last_message__pubdate')\
            .all()

    # Paginator
    paginator = Paginator(topics, settings.TOPICS_PER_PAGE)
    page = request.GET.get('page')

    try:
        shown_topics = paginator.page(page)
        page = int(page)
    except PageNotAnInteger:
        shown_topics = paginator.page(1)
        page = 1
    except EmptyPage:
        shown_topics = paginator.page(paginator.num_pages)
        page = paginator.num_pages

    return render_template('forum/details.html', {
        'forum': forum, 'sticky_topics': sticky_topics, 'topics': shown_topics,
        'pages': paginator_range(page, paginator.num_pages), 'nb': page
    })


@cache_page(60 * 2)
@can_read_now
def cat_details(request, cat_slug):
    """Display the forums belonging to the given category."""
    category = get_object_or_404(Category, slug=cat_slug)
    forums = Forum.objects.filter(category__pk=category.pk).all()

    return render_template('forum/cat_details.html', {
        'category': category, 'forums': forums
    })


@can_read_now
def topic(request, topic_pk, topic_slug):
    """Display a thread and its posts using a pager."""
    # TODO: Clean that up
    topic = get_object_or_404(Topic, pk=topic_pk)
    
    if not topic.forum.can_read(request.user):
        raise PermissionDenied

    # Check link
    if not topic_slug == slugify(topic.title):
        return redirect(topic.get_absolute_url())

    # If the user is authenticated and has never read topic, we mark it as
    # read.
    if request.user.is_authenticated():
        if never_read(topic):
            mark_read(topic)
        elif TopicFollowed.objects.filter(topic=topic, user=request.user).count()>0 :
            if TopicRead.objects.filter(topic=topic, user=request.user).last().post.pk != topic.last_message.pk:
                cache.delete(make_template_fragment_key('notification', str(request.user.pk)))
                cache.delete(make_template_fragment_key('follows', str(request.user.pk)))

    # Retrieves all posts of the topic and use paginator with them.
    posts = Post.objects\
                .filter(topic__pk=topic.pk)\
                .order_by('position')\
                .all()

    last_post_pk = topic.last_message.pk

    # Handle pagination
    paginator = Paginator(posts, settings.POSTS_PER_PAGE)

    # The category list is needed to move threads
    categories = Category.objects.all()

    try:
        page_nbr = int(request.GET['page'])
    except KeyError:
        page_nbr = 1

    try:
        posts = paginator.page(page_nbr)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        raise Http404

    res = []
    if page_nbr != 1:
        # Show the last post of the previous page
        last_page = paginator.page(page_nbr - 1).object_list
        last_post = (last_page)[len(last_page) - 1]
        res.append(last_post)

    for post in posts:
        res.append(post)

    # Build form to send a post for the current topic.
    form = PostForm(topic, request.user)
    form.helper.form_action = reverse(
        'zds.forum.views.answer') + '?sujet=' + str(topic.pk)

    form_move = MoveTopicForm(topic=topic)
    
    return render_template('forum/topic.html', {
        'topic': topic,
        'posts': res,
        'categories': categories,
        'pages': paginator_range(page_nbr, paginator.num_pages),
        'nb': page_nbr,
        'last_post_pk': last_post_pk,
        'form': form,
        'form_move': form_move
    })


@can_write_and_read_now
@login_required
@transaction.atomic
def new(request):
    """Creates a new topic in a forum."""
    try:
        forum_pk = request.GET['forum']
    except KeyError:
        raise Http404

    forum = get_object_or_404(Forum, pk=forum_pk)
    
    if not forum.can_read(request.user):
        raise PermissionDenied

    if request.method == 'POST':

        # If the client is using the "preview" button
        if 'preview' in request.POST:
            form = TopicForm(initial={
                'title': request.POST['title'],
                'subtitle': request.POST['subtitle'],
                'text': request.POST['text']
            })
            return render_template('forum/new.html', {
                'forum': forum,
                'form': form,
                'text': request.POST['text'],
            })

        form = TopicForm(request.POST)
        data = form.data
        if form.is_valid():
            # Creating the thread
            n_topic = Topic()
            n_topic.forum = forum
            n_topic.title = data['title']
            n_topic.subtitle = data['subtitle']
            n_topic.pubdate = datetime.now()
            n_topic.author = request.user
            n_topic.save()

            # Adding the first message
            post = Post()
            post.topic = n_topic
            post.author = request.user
            post.text = data['text']
            post.text_html = emarkdown(request.POST['text'])
            post.pubdate = datetime.now()
            post.position = 1
            post.ip_address = get_client_ip(request)
            post.save()

            n_topic.last_message = post
            n_topic.save()

            # Follow the topic
            follow(n_topic)

            return redirect(n_topic.get_absolute_url())

    else:
        form = TopicForm()

    return render_template('forum/new.html', {
        'forum': forum,
        'form': form,
    })


@can_write_and_read_now
@login_required
@require_POST
@transaction.atomic
def solve_alert(request):
    # only staff can move topic
    if not request.user.has_perm('forum.change_post'):
        raise PermissionDenied

    alert = get_object_or_404(Alert, pk=request.POST['alert_pk'])
    post = Post.objects.get(alerts__in=[alert])
    bot = get_object_or_404(User, username=settings.BOT_ACCOUNT)
    msg = u"Bonjour {0},\n\nVous recevez ce message car vous avez signalé le message de *{1}*, dans le sujet [{2}]({3}). Votre alerte a été traitée par **{4}** et il vous a laissé le message suivant :\n\n`{5}`\n\n\nToute l'équipe de la modération vous remercie".format(alert.author.username, post.author.username, post.topic.title, settings.SITE_URL + post.get_absolute_url(), request.user.username, request.POST['text'])
    send_mp(bot, [alert.author], u"Résolution d'alerte : {0}".format(post.topic.title), "", msg, False)
    alert.delete()

    messages.success(
        request,
        u'L\'alerte a bien été résolue')

    return redirect(post.get_absolute_url())

@can_write_and_read_now
@login_required
@require_POST
def move_topic(request):
    # only staff can move topic
    if not request.user.has_perm('forum.change_topic'):
        raise PermissionDenied

    try:
        topic_pk = request.GET['sujet']
    except KeyError:
        raise Http404

    forum = get_object_or_404(Forum, pk=request.POST['forum'])
    
    if not forum.can_read(request.user):
        raise PermissionDenied
    
    topic = get_object_or_404(Topic, pk=topic_pk)
    topic.forum = forum
    topic.save()

    messages.success(
        request,
        u'Le sujet {0} a bien été déplacé dans {1}.'.format(
            topic.title,
            forum.title))

    return redirect(topic.get_absolute_url())


@can_write_and_read_now
@login_required
def edit(request):
    """Edit the given topic."""
    try:
        topic_pk = request.GET['topic']
    except KeyError:
        raise Http404

    try:
        page = int(request.GET['page'])
    except KeyError:
        page = 1

    data = request.GET
    resp = {}

    g_topic = get_object_or_404(Topic, pk=topic_pk)

    if 'follow' in data:
        resp['follow'] = follow(g_topic)

    if request.user == g_topic.author or request.user.has_perm('forum.change_topic'):
        if 'solved' in data:
            g_topic.is_solved = not g_topic.is_solved
            resp['solved'] = g_topic.is_solved
    if request.user.has_perm('forum.change_topic'):
        # Staff actions using AJAX
        # TODO: Do not redirect on AJAX requests
        if 'lock' in data:
            g_topic.is_locked = data['lock'] == 'true'
            messages.success(
                request,
                u'Le sujet {0} est désormais vérouillé.'.format(
                    g_topic.title))
        if 'sticky' in data:
            g_topic.is_sticky = data['sticky'] == 'true'
            messages.success(
                request,
                u'Le sujet {0} est désormais épinglé.'.format(
                    g_topic.title))
        if 'move' in data:
            try:
                forum_pk = int(request.POST['move_target'])
            except KeyError:
                raise Http404

            forum = get_object_or_404(Forum, pk=forum_pk)
            g_topic.forum = forum

    g_topic.save()

    if request.is_ajax():
        return HttpResponse(json.dumps(resp))
    else:
        if not g_topic.forum.can_read(request.user):
            return redirect(reverse('zds.forum.views.index'))
        else:
            return redirect(u'{}?page={}'.format(g_topic.get_absolute_url(), page))


@can_write_and_read_now
@login_required
@transaction.atomic
def answer(request):
    """Adds an answer from a user to a topic."""
    try:
        topic_pk = request.GET['sujet']
    except KeyError:
        raise Http404

    # Retrieve current topic.
    g_topic = get_object_or_404(Topic, pk=topic_pk)
    
    if not g_topic.forum.can_read(request.user):
        raise PermissionDenied

    # Making sure posting is allowed
    if g_topic.is_locked:
        raise PermissionDenied

    # Check that the user isn't spamming
    if g_topic.antispam(request.user):
        raise PermissionDenied

    last_post_pk = g_topic.last_message.pk

    # Retrieve 10 last posts of the currenta topic.
    posts = Post.objects\
        .filter(topic=g_topic)\
        .order_by('-pubdate')[:10]

    # User would like preview his post or post a new post on the topic.
    if request.method == 'POST':
        data = request.POST
        newpost = last_post_pk != int(data['last_post'])

        # Using the « preview button », the « more » button or new post
        if 'preview' in data or newpost:
            form = PostForm(g_topic, request.user, initial={
                'text': data['text']
            })
            form.helper.form_action = reverse(
                'zds.forum.views.answer') + '?sujet=' + str(g_topic.pk)
            return render_template('forum/answer.html', {
                'text': data['text'],
                'topic': g_topic,
                'posts': posts,
                'last_post_pk': last_post_pk,
                'newpost': newpost,
                'form': form
            })

        # Saving the message
        else:
            form = PostForm(g_topic, request.user, request.POST)
            if form.is_valid():
                data = form.data

                post = Post()
                post.topic = g_topic
                post.author = request.user
                post.text = data['text']
                post.text_html = emarkdown(data['text'])
                post.pubdate = datetime.now()
                post.position = g_topic.get_post_count() + 1
                post.ip_address = get_client_ip(request)
                post.save()

                g_topic.last_message = post
                g_topic.save()

                # Follow topic on answering
                if not g_topic.is_followed():
                    follow(g_topic)

                return redirect(post.get_absolute_url())
            else:
                return render_template('forum/answer.html', {
                    'text': data['text'],
                    'topic': g_topic,
                    'posts': posts,
                    'last_post_pk': last_post_pk,
                    'newpost': newpost,
                    'form': form
                })

    # Actions from the editor render to answer.html.
    else:
        text = ''

        # Using the quote button
        if 'cite' in request.GET:
            post_cite_pk = request.GET['cite']
            post_cite = Post.objects.get(pk=post_cite_pk)
            if not post_cite.is_visible:
                raise PermissionDenied

            for line in post_cite.text.splitlines():
                text = text + '> ' + line + '\n'

            text = u'{0}\nSource:[{1}]({2}{3})'.format(
                text,
                post_cite.author.username,
                settings.SITE_URL,
                post_cite.get_absolute_url())

        form = PostForm(g_topic, request.user, initial={
            'text': text
        })
        form.helper.form_action = reverse(
            'zds.forum.views.answer') + '?sujet=' + str(g_topic.pk)


        return render_template('forum/answer.html', {
            'topic': g_topic,
            'posts': posts,
            'last_post_pk': last_post_pk,
            'form': form
        })


@can_write_and_read_now
@login_required
@transaction.atomic
def edit_post(request):
    """Edit the given user's post."""
    try:
        post_pk = request.GET['message']
    except KeyError:
        raise Http404

    post = get_object_or_404(Post, pk=post_pk)
    
    if not post.topic.forum.can_read(request.user):
        raise PermissionDenied

    g_topic = None
    if post.position <= 1:
        g_topic = get_object_or_404(Topic, pk=post.topic.pk)

    # Making sure the user is allowed to do that. Author of the post
    # must to be the user logged.
    if post.author != request.user and not request.user.has_perm('forum.change_post') and 'signal-post' not in request.POST:
        raise PermissionDenied

    if post.author != request.user and request.method == 'GET' and request.user.has_perm('forum.change_post'):
        messages.warning(
            request,
            u'Vous éditez ce message en tant que modérateur (auteur : {}).'
            u' Soyez encore plus prudent lors de l\'édition de celui-ci !'
            .format(post.author.username))

    if request.method == 'POST':

        if 'delete-post' in request.POST:
            if post.author == request.user or request.user.has_perm('forum.change_post'):
                post.alerts.all().delete()
                post.is_visible = False
                if request.user.has_perm('forum.change_post'):
                    post.text_hidden = request.POST['text_hidden']
                post.editor = request.user
                messages.success(request, u'Le message est désormais masqué')

        if 'show-post' in request.POST:
            if request.user.has_perm('forum.change_post'):
                post.is_visible = True
                post.text_hidden = ''

        if 'signal-post' in request.POST:
            alert = Alert()
            alert.author = request.user
            alert.text = request.POST['signal-text']
            alert.pubdate = datetime.now()
            alert.save()
            post.alerts.add(alert)

            messages.success(
                request,
                u'Une alerte a été envoyée à l\'équipe concernant ce message')

        # Using the preview button
        if 'preview' in request.POST:
            if g_topic:
                form = TopicForm(initial={
                    'title': request.POST['title'],
                    'subtitle': request.POST['subtitle'],
                    'text': request.POST['text']
                })
            else:
                form = PostForm(post.topic, request.user, initial={
                    'text': request.POST['text']
                })
            
            form.helper.form_action = reverse(
                'zds.forum.views.edit_post') + '?message=' + str(post_pk)
            return render_template('forum/edit_post.html', {
                'post': post,
                'topic': post.topic,
                'text': request.POST['text'],
                'form': form,
            })

        if not 'delete-post' in request.POST and not 'signal-post' in request.POST and not 'show-post' in request.POST:
            # The user just sent data, handle them
            if request.POST['text'].strip() != '':
                post.text = request.POST['text']
                post.text_html = emarkdown(request.POST['text'])
                post.update = datetime.now()
                post.editor = request.user

            # Modifying the thread info
            if g_topic:
                g_topic.title = request.POST['title']
                g_topic.subtitle = request.POST['subtitle']
                g_topic.save()

        post.save()

        return redirect(post.get_absolute_url())

    else:
        if g_topic:
            form = TopicForm(initial={
                'title': g_topic.title,
                'subtitle': g_topic.subtitle,
                'text': post.text
            })
        else:
            form = PostForm(post.topic, request.user, initial={
                'text': post.text
            })

        form.helper.form_action = reverse(
            'zds.forum.views.edit_post') + '?message=' + str(post_pk)
        return render_template('forum/edit_post.html', {
            'post': post,
            'topic': post.topic,
            'text': post.text,
            'form': form
        })


@can_write_and_read_now
@login_required
def useful_post(request):
    """Marks a message as useful (for the OP)"""
    try:
        post_pk = request.GET['message']
    except KeyError:
        raise Http404

    post = get_object_or_404(Post, pk=post_pk)
    
    if not post.topic.forum.can_read(request.user):
        raise PermissionDenied

    # Making sure the user is allowed to do that
    if post.author == request.user or request.user != post.topic.author:
        raise Http404

    post.is_useful = not post.is_useful

    post.save()

    return redirect(post.get_absolute_url())


@can_write_and_read_now
@login_required
def like_post(request):
    """Like a post."""
    try:
        post_pk = request.GET['message']
    except KeyError:
        raise Http404

    resp = {}
    post = get_object_or_404(Post, pk=post_pk)
    user = request.user
    
    if not post.topic.forum.can_read(request.user):
        raise PermissionDenied

    if post.author.pk != request.user.pk:
        # Making sure the user is allowed to do that
        if CommentLike.objects.filter(user__pk=user.pk, comments__pk=post_pk).count() == 0:
            like = CommentLike()
            like.user = user
            like.comments = post
            post.like = post.like + 1
            post.save()
            like.save()
            if CommentDislike.objects.filter(user__pk=user.pk, comments__pk=post_pk).count() > 0:
                CommentDislike.objects.filter(
                    user__pk=user.pk,
                    comments__pk=post_pk).all().delete()
                post.dislike = post.dislike - 1
                post.save()
        else:
            CommentLike.objects.filter(
                user__pk=user.pk,
                comments__pk=post_pk).all().delete()
            post.like = post.like - 1
            post.save()

    resp['upvotes'] = post.like
    resp['downvotes'] = post.dislike

    if request.is_ajax():
        return HttpResponse(json.dumps(resp))
    else:
        return redirect(post.get_absolute_url())


@can_write_and_read_now
@login_required
def dislike_post(request):
    """Dislike a post."""
    try:
        post_pk = request.GET['message']
    except KeyError:
        raise Http404

    resp = {}
    post = get_object_or_404(Post, pk=post_pk)
    user = request.user

    if not post.topic.forum.can_read(request.user):
        raise PermissionDenied

    if post.author.pk != request.user.pk:
        # Making sure the user is allowed to do that
        if CommentDislike.objects.filter(user__pk=user.pk, comments__pk=post_pk).count() == 0:
            dislike = CommentDislike()
            dislike.user = user
            dislike.comments = post
            post.dislike = post.dislike + 1
            post.save()
            dislike.save()
            if CommentLike.objects.filter(user__pk=user.pk, comments__pk=post_pk).count() > 0:
                CommentLike.objects.filter(
                    user__pk=user.pk,
                    comments__pk=post_pk).all().delete()
                post.like = post.like - 1
                post.save()
        else:
            CommentDislike.objects.filter(
                user__pk=user.pk,
                comments__pk=post_pk).all().delete()
            post.dislike = post.dislike - 1
            post.save()

    resp['upvotes'] = post.like
    resp['downvotes'] = post.dislike

    if request.is_ajax():
        return HttpResponse(json.dumps(resp))
    else:
        return redirect(post.get_absolute_url())


@can_read_now
def find_topic(request, user_pk):
    """Finds all topics of a user."""
    u = get_object_or_404(User, pk=user_pk)
    topics = Topic.objects\
        .filter(author=u)\
        .order_by('-pubdate')\
        .all()
    
    tops = []
    for top in topics :
        if not top.forum.can_read(request.user):
            continue
        else:
            tops.append(top)

    # Paginator
    paginator = Paginator(tops, settings.TOPICS_PER_PAGE)
    page = request.GET.get('page')

    try:
        shown_topics = paginator.page(page)
        page = int(page)
    except PageNotAnInteger:
        shown_topics = paginator.page(1)
        page = 1
    except EmptyPage:
        shown_topics = paginator.page(paginator.num_pages)
        page = paginator.num_pages

    return render_template('forum/find_topic.html', {
        'topics': shown_topics, 'usr': u,
        'pages': paginator_range(page, paginator.num_pages), 'nb': page
    })


@can_read_now
def find_post(request, user_pk):
    """Finds all posts of a user."""
    u = get_object_or_404(User, pk=user_pk)
    posts = Post.objects\
                .filter(author=u)\
                .order_by('-pubdate')\
                .all()
    pts = []
    for post in posts :
        if not post.topic.forum.can_read(request.user):
            continue
        else:
            pts.append(post)
            
    # Paginator
    paginator = Paginator(pts, settings.POSTS_PER_PAGE)
    page = request.GET.get('page')

    try:
        shown_posts = paginator.page(page)
        page = int(page)
    except PageNotAnInteger:
        shown_posts = paginator.page(1)
        page = 1
    except EmptyPage:
        shown_posts = paginator.page(paginator.num_pages)
        page = paginator.num_pages

    return render_template('forum/find_post.html', {
        'posts': shown_posts, 'usr': u,
        'pages': paginator_range(page, paginator.num_pages), 'nb': page
    })


@login_required
@can_read_now
def followed_topics(request):
    followed_topics = request.user.get_profile().get_followed_topics()

    # Paginator
    paginator = Paginator(followed_topics, settings.FOLLOWED_TOPICS_PER_PAGE)
    page = request.GET.get('page')

    try:
        shown_topics = paginator.page(page)
        page = int(page)
    except PageNotAnInteger:
        shown_topics = paginator.page(1)
        page = 1
    except EmptyPage:
        shown_topics = paginator.page(paginator.num_pages)
        page = paginator.num_pages
    
    cache.delete(make_template_fragment_key('notification', str(request.user.pk)))
    cache.delete(make_template_fragment_key('follows', str(request.user.pk)))
    
    return render_template('forum/followed_topics.html', {
        'followed_topics': shown_topics,
        'pages': paginator_range(page, paginator.num_pages),
        'nb': page
    })
