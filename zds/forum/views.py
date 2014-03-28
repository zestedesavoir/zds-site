# coding: utf-8

from datetime import datetime
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.http import require_POST
import json

from forms import TopicForm, PostForm, MoveTopicForm
from models import Category, Forum, Topic, Post, follow, never_read, mark_read
from zds.member.models import Profile
from zds.member.views import get_client_ip
from zds.utils import render_template, slugify
from zds.utils.models import Alert, CommentLike, CommentDislike
from zds.utils.paginator import paginator_range
from zds.member.models import Profile
from zds.member.decorator import can_read_now, can_write_and_read_now
from zds.utils.templatetags.emarkdown import emarkdown

@can_read_now
def index(request):
    '''
    Display the category list with all their forums
    '''
    categories = Category.objects.order_by('position').all()

    return render_template('forum/index.html', {
        'categories': categories,
        'user': request.user
    })

@can_read_now
def details(request, cat_slug, forum_slug):
    '''
    Display the given forum and all its topics
    '''
    forum = get_object_or_404(Forum, slug=forum_slug)
    
    if not forum.can_read(request.user):
        raise Http404
    
    sticky_topics = Topic.objects\
        .filter(forum__pk=forum.pk, is_sticky=True)\
        .order_by('-last_message__pubdate')\
        .all()
    topics = Topic.objects\
        .filter(forum__pk=forum.pk, is_sticky=False)\
        .order_by('-last_message__pubdate')\
        .all()

    # Paginator
    paginator = Paginator(topics, settings.TOPICS_PER_PAGE)
    page = request.GET.get('page')

    try:
        shown_topics = paginator.page(page)
        page=int(page)
    except PageNotAnInteger:
        shown_topics = paginator.page(1)
        page = 1
    except EmptyPage:
        shown_topics = paginator.page(paginator.num_pages)
        page=paginator.num_pages

    return render_template('forum/details.html', {
        'forum': forum, 'sticky_topics': sticky_topics, 'topics': shown_topics,
        'pages': paginator_range(page, paginator.num_pages), 'nb': page
    })

@can_read_now
def cat_details(request, cat_slug):
    '''
    Display the forums belonging to the given category
    '''
    category = get_object_or_404(Category, slug=cat_slug)
    forums = Forum.objects.filter(category__pk=category.pk).all()

    return render_template('forum/cat_details.html', {
        'category': category, 'forums': forums
    })

@can_read_now
def topic(request, topic_pk, topic_slug):
    '''Display a thread and its posts using a pager'''
    # TODO: Clean that up
    topic = get_object_or_404(Topic, pk=topic_pk)
    
    # Check link
    if not topic_slug == slugify(topic.title):
        return redirect(topic.get_absolute_url())

    # If the user is authenticated and has never read topic, we mark it as read.
    if request.user.is_authenticated():
        if never_read(topic):
            mark_read(topic)

    # Retrieves all posts of the topoc and use paginator with them.
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
    form.helper.form_action = reverse('zds.forum.views.answer') + '?sujet=' + str(topic.pk)
    
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
def new(request):
    '''
    Creates a new topic in a forum
    '''
    try:
        forum_pk = request.GET['forum']
    except KeyError:
        raise Http404

    forum = get_object_or_404(Forum, pk=forum_pk)

    if request.method == 'POST':
        # If the client is using the "preview" button
        if 'preview' in request.POST:
            form = TopicForm(initial = {
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
        if form.is_valid() and request.POST['text'].strip() !='':
            data = form.data
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
            # TODO: add errors to the form and return it
            raise Http404

    else:

        form = TopicForm()
        return render_template('forum/new.html', {
            'forum': forum,
            'form': form,
        })

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
    topic = get_object_or_404(Topic, pk=topic_pk)
    topic.forum = forum
    topic.save()
    
    return redirect(topic.get_absolute_url())
    
@can_write_and_read_now
@login_required
def edit(request):
    '''
    Edit the given topic
    '''
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
        if 'sticky' in data:
            g_topic.is_sticky = data['sticky'] == 'true'
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
        return redirect(u'{}?page={}'.format(g_topic.get_absolute_url(), page))

@can_write_and_read_now
@login_required
def answer(request):
    '''Adds an answer from a user to a topic'''
    try:
        topic_pk = request.GET['sujet']
    except KeyError:
        raise Http404
    
    # Retrieve current topic.
    g_topic = get_object_or_404(Topic, pk=topic_pk)

    # Making sure posting is allowed
    if g_topic.is_locked:
        raise Http404

    # Check that the user isn't spamming
    if g_topic.antispam(request.user):
        raise Http404
    
    # Retrieve 3 last posts of the currenta topic.
    posts = Post.objects\
                .filter(topic = g_topic)\
                .order_by('-pubdate')[:3]
    last_post_pk = g_topic.last_message.pk

    # User would like preview his post or post a new post on the topic.
    if request.method == 'POST':
        data = request.POST
        newpost = last_post_pk != int(data['last_post'])
        
        # Using the « preview button », the « more » button or new post
        if 'preview' in data or newpost:
            form = PostForm(g_topic, request.user, initial = {
                'text': data['text']
            })
            form.helper.form_action = reverse('zds.forum.views.answer') + '?sujet=' + str(g_topic.pk)
            return render_template('forum/answer.html', {
                'text': data['text'], 
                'topic': g_topic, 
                'last_post_pk': last_post_pk, 
                'newpost': newpost,
                'form': form
            })

        # Saving the message
        else:
            form = PostForm(g_topic, request.user, request.POST)
            if form.is_valid() and data['text'].strip() !='':
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
                raise Http404

    # Actions from the editor render to answer.html.
    else:
        text = ''

        # Using the quote button
        if 'cite' in request.GET:
            post_cite_pk = request.GET['cite']
            post_cite = Post.objects.get(pk=post_cite_pk)

            for line in post_cite.text.splitlines():
                text = text + '> ' + line + '\n'

            text = u'{0}\nSource:[{1}]({2})'.format(text,
                post_cite.author.username, post_cite.get_absolute_url())

        form = PostForm(g_topic, request.user, initial = {
            'text': text
        })
        form.helper.form_action = reverse('zds.forum.views.answer') + '?sujet=' + str(g_topic.pk)
        return render_template('forum/answer.html', {
            'topic': g_topic, 
            'posts': posts,
            'last_post_pk': last_post_pk,
            'form': form
        })

@can_write_and_read_now
@login_required
def edit_post(request):
    '''
    Edit the given user's post
    '''
    try:
        post_pk = request.GET['message']
    except KeyError:
        raise Http404

    post = get_object_or_404(Post, pk=post_pk)

    g_topic = None
    if post.position <= 1:
        g_topic = get_object_or_404(Topic, pk=post.topic.pk)

    # Making sure the user is allowed to do that. Author of the post
    # must to be the user logged.
    if post.author != request.user and not request.user.has_perm('forum.change_post') :
        raise PermissionDenied
        
    if post.author != request.user and request.method == 'GET' and request.user.has_perm('forum.change_post'):
        messages.add_message(
            request, messages.WARNING,
            u'Vous éditez ce message en tant que modérateur (auteur : {}).'
            u' Soyez encore plus prudent lors de l\'édition de celui-ci !'
            .format(post.author.username))
        post.alerts.all().delete()

    if request.method == 'POST':
        
        if 'delete-post' in request.POST:
            if post.author == request.user or request.user.has_perm('forum.change_post'):
                post.alerts.all().delete()
                post.is_visible=False
                if request.user.has_perm('forum.change_post'):
                    post.text_hidden=request.POST['text_hidden']
                post.editor = request.user
            
        if 'show-post' in request.POST:
            if request.user.has_perm('forum.change_post'):
                post.is_visible=True
                post.text_hidden=''
                    
        if 'signal-post' in request.POST:
            if post.author != request.user :
                alert = Alert()
                alert.author = request.user
                alert.text=request.POST['signal-text']
                alert.pubdate = datetime.now()
                alert.save()
                post.alerts.add(alert)
        
        # Using the preview button
        if 'preview' in request.POST:
            form = PostForm(g_topic, request.user, initial = {
                'text': request.POST['text']
            })
            form.helper.form_action = reverse('zds.forum.views.edit_post') + '?message=' + str(post_pk)
            return render_template('forum/edit_post.html', {
                'post': post, 
                'topic': g_topic, 
                'text': request.POST['text'],
                'form': form,
            })
        
        if not 'delete-post' in request.POST and not 'signal-post' in request.POST and not 'show-post' in request.POST:
            # The user just sent data, handle them
            if request.POST['text'].strip() !='':
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
            form = TopicForm(g_topic, request.user, initial = {
                'title ': g_topic.title,
                'subtitle': g_topic.subtitle,
                'text': post.text
            })
        else:
            form = PostForm(g_topic, request.user, initial = {
                'text': post.text
            })
        
        form.helper.form_action = reverse('zds.forum.views.edit_post') + '?message=' + str(post_pk)
        return render_template('forum/edit_post.html', {
            'post': post, 
            'topic': g_topic, 
            'text': post.text,
            'form': form
        })


@can_write_and_read_now
@login_required
def useful_post(request):
    '''Marks a message as useful (for the OP)'''
    try:
        post_pk = request.GET['message']
    except KeyError:
        raise Http404

    post = get_object_or_404(Post, pk=post_pk)
    
    # Making sure the user is allowed to do that
    if post.author == request.user or request.user != post.topic.author:
        raise Http404
    
    
    post.is_useful = not post.is_useful
    
    post.save()

    return redirect(post.get_absolute_url())

@can_write_and_read_now
@login_required
def like_post(request):
    '''Like a post'''
    try:
        post_pk = request.GET['message']
    except KeyError:
        raise Http404
    
    resp = {}
    post = get_object_or_404(Post, pk=post_pk)
    user = request.user
    
    if post.author.pk != request.user.pk:
        # Making sure the user is allowed to do that
        if CommentLike.objects.filter(user__pk=user.pk, comments__pk=post_pk).count()==0:
            like=CommentLike()
            like.user=user
            like.comments=post
            post.like=post.like+1
            post.save()
            like.save()
            if CommentDislike.objects.filter(user__pk=user.pk, comments__pk=post_pk).count()>0:
                CommentDislike.objects.filter(user__pk=user.pk, comments__pk=post_pk).all().delete()
                post.dislike=post.dislike-1
                post.save()
        else:
            CommentLike.objects.filter(user__pk=user.pk, comments__pk=post_pk).all().delete()
            post.like=post.like-1
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
    '''Dislike a post'''
    try:
        post_pk = request.GET['message']
    except KeyError:
        raise Http404
    
    resp = {}
    post = get_object_or_404(Post, pk=post_pk)
    user = request.user

    if post.author.pk != request.user.pk:
        # Making sure the user is allowed to do that
        if CommentDislike.objects.filter(user__pk=user.pk, comments__pk=post_pk).count()==0:
            dislike=CommentDislike()
            dislike.user=user
            dislike.comments=post
            post.dislike=post.dislike+1
            post.save()
            dislike.save()
            if CommentLike.objects.filter(user__pk=user.pk, comments__pk=post_pk).count()>0:
                CommentLike.objects.filter(user__pk=user.pk, comments__pk=post_pk).all().delete()
                post.like=post.like-1
                post.save()
        else :
            CommentDislike.objects.filter(user__pk=user.pk, comments__pk=post_pk).all().delete()
            post.dislike=post.dislike-1
            post.save()
    
    resp['upvotes'] = post.like
    resp['downvotes'] = post.dislike
    
    if request.is_ajax():
        return HttpResponse(json.dumps(resp))
    else:
        return redirect(post.get_absolute_url())

@can_read_now
def find_topic(request, user_pk):
    '''Finds all topics of a user'''
    u = get_object_or_404(User, pk=user_pk)
    topics = Topic.objects\
                .filter(author=u)\
                .order_by('-pubdate')\
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
    
    return render_template('forum/find_topic.html', {
        'topics': shown_topics, 'usr':u,
        'pages': paginator_range(page, paginator.num_pages), 'nb': page
    })

@can_read_now
def find_post(request, user_pk):
    '''Finds all posts of a user'''
    u = get_object_or_404(User, pk=user_pk)
    posts = Post.objects\
                .filter(author=u)\
                .order_by('-pubdate')\
                .all()

    # Paginator
    paginator = Paginator(posts, settings.POSTS_PER_PAGE)
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
        'posts': shown_posts, 'usr':u,
        'pages': paginator_range(page, paginator.num_pages), 'nb': page
    })

# Deprecated URLs

def deprecated_topic_redirect(request, topic_pk, topic_slug):
    topic = get_object_or_404(Topic, pk=topic_pk)
    return redirect(topic.get_absolute_url(), permanent=True)


def deprecated_cat_details_redirect(request, cat_pk, cat_slug):
    category = get_object_or_404(Category, pk=cat_pk)
    return redirect(category.get_absolute_url(), permanent=True)


def deprecated_details_redirect(request, cat_slug, forum_pk, forum_slug):
    forum = get_object_or_404(Forum, pk=forum_pk)
    return redirect(forum.get_absolute_url(), permanent=True)


def deprecated_feed_messages_rss(request):
    return redirect('/forums/flux/messages/rss/', permanent=True)


def deprecated_feed_messages_atom(request):
    return redirect('/forums/flux/messages/atom/', permanent=True)
