# coding: utf-8

from datetime import datetime
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, get_object_or_404

from forms import PrivateTopicForm, PrivatePostForm
from models import PrivateTopic, PrivatePost, \
    never_privateread, mark_read
from zds.utils import render_template, slugify
from zds.utils.paginator import paginator_range


def index(request):
    '''
    Display the all private topics
    '''
    
    #delete actions
    if request.method == 'POST':
        if 'delete' in request.POST:
            liste = request.POST.getlist('items')
            topics=PrivateTopic.objects.filter(pk__in=liste).all()
            for topic in topics:
                if request.user == topic.author:
                    topic.author=topic.participants.all()[0]
                    topic.participants.remove(topic.participants.all()[0])
                else :
                    topic.participants.remove(request.user)
                topic.save()

    privatetopics = PrivateTopic.objects\
        .filter(Q(participants__in=[request.user])|Q(author=request.user))\
        .distinct().order_by('-last_message__pubdate').all()

    # Paginator
    paginator = Paginator(privatetopics, settings.TOPICS_PER_PAGE)
    page = request.GET.get('page')

    try:
        shown_privatetopics = paginator.page(page)
        page=int(page)
    except PageNotAnInteger:
        shown_privatetopics = paginator.page(1)
        page = 1
    except EmptyPage:
        shown_privatetopics = paginator.page(paginator.num_pages)
        page=paginator.num_pages

    return render_template('mp/index.html', {
        'privatetopics': shown_privatetopics,
        'pages': paginator_range(page, paginator.num_pages), 'nb': page
    })


def topic(request, topic_pk, topic_slug):
    '''
    Display a thread and its posts using a pager
    '''

    # TODO: Clean that up
    g_topic = get_object_or_404(PrivateTopic, pk=topic_pk)
    
    if not g_topic.author == request.user and not request.user in list(g_topic.participants.all()):
         raise Http404
    
    # Check link
    if not topic_slug == slugify(g_topic.title):
        return redirect(g_topic.get_absolute_url())

    if request.user.is_authenticated():
        if never_privateread(g_topic):
            mark_read(g_topic)

    posts = PrivatePost.objects.filter(privatetopic__pk=g_topic.pk)\
                              .order_by('position_in_topic')\
                              .all()

    last_post_pk = g_topic.last_message.pk

    # Handle pagination
    paginator = Paginator(posts, settings.POSTS_PER_PAGE)

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

    return render_template('mp/topic.html', {
        'topic': g_topic, 'posts': res,
        'pages': paginator_range(page_nbr, paginator.num_pages),
        'nb': page_nbr,
        'last_post_pk': last_post_pk
    })


@login_required
def new(request):
    '''
    Creates a new private topic 
    '''
    
    if request.method == 'POST':
        # If the client is using the "preview" button
        if 'preview' in request.POST:
            return render_template('mp/new.html', {
                'participants': request.POST['participants'],
                'title': request.POST['title'],
                'subtitle': request.POST['subtitle'],
                'text': request.POST['text'],
            })
                
        form = PrivateTopicForm(request.POST)
        if form.is_valid():
            data = form.data
            #control participant
            ctrl=[]
            list_part = data['participants'].replace(',',' ').split()
            for part in list_part:
                p=get_object_or_404(User, username=part)
                ctrl.append(p)
            
            # Creating the thread
            n_topic = PrivateTopic()
            n_topic.title = data['title']
            n_topic.subtitle = data['subtitle']
            n_topic.pubdate = datetime.now()
            n_topic.author = request.user
            n_topic.save()
            
            for part in ctrl:
                n_topic.participants.add(part)

            # Adding the first message
            post = PrivatePost()
            post.privatetopic = n_topic
            post.author = request.user
            post.text = data['text']
            post.pubdate = datetime.now()
            post.position_in_topic = 1
            post.save()

            n_topic.last_message = post
            n_topic.save()

            return redirect(n_topic.get_absolute_url())

        else:
            # TODO: add errors to the form and return it
            raise Http404
    else:
        form = PrivateTopicForm()
        if 'username' in request.GET:
            user = request.GET['username']
            u=get_object_or_404(User, username=user)
        else :
            u=''
        return render_template('mp/new.html', {
            'participants': u,
        })
        
@login_required
def edit(request):
    '''
    Edit the given topic
    '''
    authenticated_user = request.user

    if not request.method == 'POST':
        raise Http404

    try:
        topic_pk = request.POST['privatetopic']
    except KeyError:
        raise Http404

    try:
        page = int(request.POST['page'])
    except KeyError:
        page = 1

    data = request.POST

    g_topic = get_object_or_404(PrivateTopic, pk=topic_pk)

    if request.POST['username'] :
        u = get_object_or_404(User, username=request.POST['username'])
        if not authenticated_user == u:
            g_topic.participants.add(u)
            g_topic.save()

    return redirect(u'{}?page={}'.format(g_topic.get_absolute_url(), page))


@login_required
def answer(request):
    '''
    Adds an answer from an user to a topic
    '''
    try:
        topic_pk = request.GET['sujet']
    except KeyError:
        raise Http404

    g_topic = get_object_or_404(PrivateTopic, pk=topic_pk)
    posts = PrivatePost.objects.filter(privatetopic=g_topic).order_by('-pubdate')[:3]
    last_post_pk = g_topic.last_message.pk

    # Check that the user isn't spamming
    if g_topic.antispam(request.user):
        raise Http404
    
    # If we just sent data
    if request.method == 'POST':
        data = request.POST
        newpost = last_post_pk != int(data['last_post'])

        # Using the « preview button », the « more » button or new post
        if 'preview' in data or 'more' in data or newpost:
            return render_template('mp/answer.html', {
                'text': data['text'], 'topic': g_topic, 'posts': posts,
                'last_post_pk': last_post_pk, 'newpost': newpost
            })

        # Saving the message
        else:
            form = PrivatePostForm(request.POST)
            if form.is_valid():
                data = form.data

                post = PrivatePost()
                post.privatetopic = g_topic
                post.author = request.user
                post.text = data['text']
                post.pubdate = datetime.now()
                post.position_in_topic = g_topic.get_post_count() + 1
                post.save()

                g_topic.last_message = post
                g_topic.save()

                return redirect(post.get_absolute_url())
            else:
                raise Http404

    else:
        text = ''

        # Using the quote button
        if 'cite' in request.GET:
            post_cite_pk = request.GET['cite']
            post_cite = PrivatePost.objects.get(pk=post_cite_pk)

            for line in post_cite.text.splitlines():
                text = text + '> ' + line + '\n'

            text = u'**{0} a écrit :**\n{1}\n'.format(
                post_cite.author.username, text)

        return render_template('mp/answer.html', {
            'topic': g_topic, 'text': text, 'posts': posts,
            'last_post_pk': last_post_pk
        })


@login_required
def edit_post(request):
    '''
    Edit the given user's post
    '''
    try:
        post_pk = request.GET['message']
    except KeyError:
        raise Http404

    post = get_object_or_404(PrivatePost, pk=post_pk)
    
    #Only edit last private post
    tp = get_object_or_404(PrivateTopic, pk=post.privatetopic.pk)
    last = get_object_or_404(PrivatePost, pk=tp.last_message.pk)
    if not  last.pk == post.pk :
        raise Http404
    
    g_topic = None
    if post.position_in_topic == 1:
        g_topic = get_object_or_404(PrivateTopic, pk=post.privatetopic.pk)

    
    
    # Making sure the user is allowed to do that
    if post.author != request.user:
        if not request.user.has_perm('mp.change_post'):
            raise Http404
        elif request.method == 'GET':
            messages.add_message(
                request, messages.WARNING,
                u'Vous éditez ce message en tant que modérateur (auteur : {}).'
                u' Soyez encore plus prudent lors de l\'édition de celui-ci !'
                .format(post.author.username))

    if request.method == 'POST':

        # Using the preview button
        if 'preview' in request.POST:
            if g_topic:
                g_topic = Topic(title=request.POST['title'],
                                subtitle=request.POST['subtitle'])
            return render_template('mp/edit_post.html', {
                'post': post, 'topic': g_topic, 'text': request.POST['text'],
            })

        # The user just sent data, handle them
        post.text = request.POST['text']
        post.update = datetime.now()
        post.save()

        # Modifying the thread info
        if g_topic:
            g_topic.title = request.POST['title']
            g_topic.subtitle = request.POST['subtitle']
            g_topic.save()

        return redirect(post.get_absolute_url())

    else:
        return render_template('mp/edit_post.html', {
            'post': post, 'topic': g_topic, 'text': post.text
        })
