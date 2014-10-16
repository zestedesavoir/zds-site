# coding: utf-8

from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMultiAlternatives
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import redirect, get_object_or_404
from django.template import Context
from django.template.loader import get_template
from django.views.decorators.http import require_POST
from django.forms.util import ErrorList

from zds.utils import render_template, slugify
from zds.utils.mps import send_mp
from zds.utils.paginator import paginator_range
from zds.utils.templatetags.emarkdown import emarkdown

from .forms import PrivateTopicForm, PrivatePostForm
from .models import PrivateTopic, PrivatePost, \
    never_privateread, mark_read, PrivateTopicRead


@login_required
def index(request):
    """Display the all private topics."""

    # delete actions
    if request.method == 'POST':
        if 'delete' in request.POST:
            liste = request.POST.getlist('items')
            topics = PrivateTopic.objects.filter(pk__in=liste)\
                .filter(
                    Q(participants__in=[request.user])
                    | Q(author=request.user))

            for topic in topics:
                if topic.participants.all().count() == 0:
                    topic.delete()
                elif request.user == topic.author:
                    topic.author = topic.participants.all()[0]
                    topic.participants.remove(topic.participants.all()[0])
                    topic.save()
                else:
                    topic.participants.remove(request.user)
                    topic.save()

    privatetopics = PrivateTopic.objects\
        .filter(Q(participants__in=[request.user]) | Q(author=request.user))\
        .select_related("author", "participants")\
        .distinct().order_by('-last_message__pubdate').all()

    # Paginator
    paginator = Paginator(privatetopics, settings.ZDS_APP['forum']['topics_per_page'])
    page = request.GET.get('page')

    try:
        shown_privatetopics = paginator.page(page)
        page = int(page)
    except PageNotAnInteger:
        shown_privatetopics = paginator.page(1)
        page = 1
    except EmptyPage:
        shown_privatetopics = paginator.page(paginator.num_pages)
        page = paginator.num_pages

    return render_template('mp/index.html', {
        'privatetopics': shown_privatetopics,
        'pages': paginator_range(page, paginator.num_pages), 'nb': page
    })


@login_required
def topic(request, topic_pk, topic_slug):
    """Display a thread and its posts using a pager."""

    # TODO: Clean that up
    g_topic = get_object_or_404(PrivateTopic, pk=topic_pk)

    if not g_topic.author == request.user \
            and request.user not in list(g_topic.participants.all()):
        raise PermissionDenied

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
    paginator = Paginator(posts, settings.ZDS_APP['forum']['posts_per_page'])

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

    # Build form to add an answer for the current topid.
    form = PrivatePostForm(g_topic, request.user)

    return render_template('mp/topic/index.html', {
        'topic': g_topic,
        'posts': res,
        'pages': paginator_range(page_nbr, paginator.num_pages),
        'nb': page_nbr,
        'last_post_pk': last_post_pk,
        'form': form
    })


@login_required
def new(request):
    """Creates a new private topic."""

    if request.method == 'POST':
        # If the client is using the "preview" button
        if 'preview' in request.POST:
            form = PrivateTopicForm(request.user.username,
                                    initial={
                                        'participants': request.POST['participants'],
                                        'title': request.POST['title'],
                                        'subtitle': request.POST['subtitle'],
                                        'text': request.POST['text'],
                                    })
            return render_template('mp/topic/new.html', {
                'form': form,
            })

        form = PrivateTopicForm(request.user.username, request.POST)

        if form.is_valid():
            data = form.data

            # Retrieve all participants of the MP.
            ctrl = []
            list_part = data['participants'].split(",")
            for part in list_part:
                part = part.strip()
                if part == '':
                    continue
                p = get_object_or_404(User, username=part)
                # We don't the author of the MP.
                if request.user == p:
                    continue
                ctrl.append(p)

            # user add only himself
            if (len(ctrl) < 1
                    and len(list_part) == 1
                    and list_part[0] == request.user.username):
                errors = form._errors.setdefault("participants", ErrorList())
                errors.append(u'Vous êtes déjà auteur du message')
                return render_template('mp/topic/new.html', {
                    'form': form,
                })

            p_topic = send_mp(request.user,
                              ctrl,
                              data['title'],
                              data['subtitle'],
                              data['text'],
                              True,
                              False)

            return redirect(p_topic.get_absolute_url())

        else:
            return render_template('mp/topic/new.html', {
                'form': form,
            })
    else:
        dest = None
        if 'username' in request.GET:
            dest_list = []
            # check that usernames in url is in the database
            for username in request.GET.getlist('username'):
                try:
                    dest_list.append(User.objects.get(username=username).username)
                except:
                    pass
            if len(dest_list) > 0:
                dest = ', '.join(dest_list)

        form = PrivateTopicForm(username=request.user.username,
                                initial={
                                    'participants': dest,
                                })
        return render_template('mp/topic/new.html', {
            'form': form,
        })


@login_required
@require_POST
def edit(request):
    """Edit the given topic."""

    try:
        topic_pk = request.POST['privatetopic']
    except KeyError:
        raise Http404

    try:
        page = int(request.POST['page'])
    except KeyError:
        page = 1

    g_topic = get_object_or_404(PrivateTopic, pk=topic_pk)

    if request.POST['username']:
        u = get_object_or_404(User, username=request.POST['username'])
        if not request.user == u:
            g_topic.participants.add(u)
            g_topic.save()

    return redirect(u'{}?page={}'.format(g_topic.get_absolute_url(), page))


@login_required
def answer(request):
    """Adds an answer from an user to a topic."""
    try:
        topic_pk = request.GET['sujet']
    except KeyError:
        raise Http404

    # Retrieve current topic.
    g_topic = get_object_or_404(PrivateTopic, pk=topic_pk)

    # check if user has right to answer
    if not g_topic.author == request.user \
            and request.user not in list(g_topic.participants.all()):
        raise PermissionDenied

    last_post_pk = g_topic.last_message.pk
    # Retrieve last posts of the current private topic.
    posts = PrivatePost.objects.filter(privatetopic=g_topic) \
        .prefetch_related() \
        .order_by("-pubdate")[:settings.ZDS_APP['forum']['posts_per_page']]

    # User would like preview his post or post a new post on the topic.
    if request.method == 'POST':
        data = request.POST
        newpost = last_post_pk != int(data['last_post'])

        # Using the « preview button », the « more » button or new post
        if 'preview' in data or newpost:
            form = PrivatePostForm(g_topic, request.user, initial={
                'text': data['text']
            })
            return render_template('mp/post/new.html', {
                'topic': g_topic,
                'last_post_pk': last_post_pk,
                'posts': posts,
                'newpost': newpost,
                'form': form,
            })

        # Saving the message
        else:
            form = PrivatePostForm(g_topic, request.user, request.POST)
            if form.is_valid():
                data = form.data

                post = PrivatePost()
                post.privatetopic = g_topic
                post.author = request.user
                post.text = data['text']
                post.text_html = emarkdown(data['text'])
                post.pubdate = datetime.now()
                post.position_in_topic = g_topic.get_post_count() + 1
                post.save()

                g_topic.last_message = post
                g_topic.save()

                # send email
                subject = "{} - MP : {}".format(settings.ZDS_APP['site']['abbr'], g_topic.title)
                from_email = "{} <{}>".format(settings.ZDS_APP['site']['litteral_name'],
                                              settings.ZDS_APP['site']['email_noreply'])
                parts = list(g_topic.participants.all())
                parts.append(g_topic.author)
                parts.remove(request.user)
                for part in parts:
                    profile = part.profile
                    if profile.email_for_answer:
                        pos = post.position_in_topic - 1
                        last_read = PrivateTopicRead.objects.filter(
                            privatetopic=g_topic,
                            privatepost__position_in_topic=pos,
                            user=part).count()
                        if last_read > 0:
                            message_html = get_template('email/mp/new.html') \
                                .render(
                                    Context({
                                        'username': part.username,
                                        'url': settings.ZDS_APP['site']['url']
                                        + post.get_absolute_url(),
                                        'author': request.user.username
                                    }))
                            message_txt = get_template('email/mp/new.txt').render(
                                Context({
                                    'username': part.username,
                                    'url': settings.ZDS_APP['site']['url']
                                    + post.get_absolute_url(),
                                    'author': request.user.username
                                }))

                            msg = EmailMultiAlternatives(
                                subject, message_txt, from_email, [
                                    part.email])
                            msg.attach_alternative(message_html, "text/html")
                            msg.send()

                return redirect(post.get_absolute_url())
            else:
                return render_template('mp/post/new.html', {
                    'topic': g_topic,
                    'last_post_pk': last_post_pk,
                    'newpost': newpost,
                    'posts': posts,
                    'form': form,
                })

    else:
        text = ''

        # Using the quote button
        if 'cite' in request.GET:
            post_cite_pk = request.GET['cite']
            post_cite = get_object_or_404(PrivatePost, pk=post_cite_pk)

            for line in post_cite.text.splitlines():
                text = text + '> ' + line + '\n'

            text = u'{0}Source:[{1}]({2}{3})'.format(
                text,
                post_cite.author.username,
                settings.ZDS_APP['site']['url'],
                post_cite.get_absolute_url())

        form = PrivatePostForm(g_topic, request.user, initial={
            'text': text
        })
        return render_template('mp/post/new.html', {
            'topic': g_topic,
            'posts': posts,
            'last_post_pk': last_post_pk,
            'form': form
        })


@login_required
def edit_post(request):
    """Edit the given user's post."""
    try:
        post_pk = request.GET['message']
    except KeyError:
        raise Http404

    post = get_object_or_404(PrivatePost, pk=post_pk)

    # Only edit last private post
    tp = get_object_or_404(PrivateTopic, pk=post.privatetopic.pk)
    last = get_object_or_404(PrivatePost, pk=tp.last_message.pk)
    if not last.pk == post.pk:
        raise PermissionDenied

    g_topic = None
    if post.position_in_topic >= 1:
        g_topic = get_object_or_404(PrivateTopic, pk=post.privatetopic.pk)

    # Making sure the user is allowed to do that. Author of the post
    # must to be the user logged.
    if post.author != request.user:
        raise PermissionDenied

    if request.method == 'POST':
        if 'text' not in request.POST:
            # if preview mode return on
            if 'preview' in request.POST:
                return redirect(
                    reverse('zds.mp.views.edit_post') +
                    '?message=' +
                    str(post_pk))
            # disallow send mp
            else:
                raise PermissionDenied

        # Using the preview button
        if 'preview' in request.POST:
            form = PrivatePostForm(g_topic, request.user, initial={
                'text': request.POST['text']
            })
            form.helper.form_action = reverse(
                'zds.mp.views.edit_post') + '?message=' + str(post_pk)

            return render_template('mp/post/edit.html', {
                'post': post,
                'topic': g_topic,
                'form': form,
            })

        # The user just sent data, handle them
        post.text = request.POST['text']
        post.text_html = emarkdown(request.POST['text'])
        post.update = datetime.now()
        post.save()

        return redirect(post.get_absolute_url())

    else:
        form = PrivatePostForm(g_topic, request.user, initial={
            'text': post.text
        })
        form.helper.form_action = reverse(
            'zds.mp.views.edit_post') + '?message=' + str(post_pk)
        return render_template('mp/post/edit.html', {
            'post': post,
            'topic': g_topic,
            'text': post.text,
            'form': form,
        })


@login_required
@require_POST
@transaction.atomic
def leave(request):
    if 'leave' in request.POST:
        ptopic = get_object_or_404(PrivateTopic, pk=request.POST['topic_pk'])
        if ptopic.participants.count() == 0:
            ptopic.delete()
        elif request.user.pk == ptopic.author.pk:
            move = ptopic.participants.first()
            ptopic.author = move
            ptopic.participants.remove(move)
            ptopic.save()
        else:
            ptopic.participants.remove(request.user)
            ptopic.save()

        messages.success(
            request, 'Vous avez quitté la conversation avec succès.')

    return redirect(reverse('zds.mp.views.index'))


@login_required
@require_POST
@transaction.atomic
def add_participant(request):
    ptopic = get_object_or_404(PrivateTopic, pk=request.POST['topic_pk'])

    # check if user is the author of topic
    if not ptopic.author == request.user:
        raise PermissionDenied

    try:
        # user_pk or user_username ?
        part = User.objects.get(username__exact=request.POST['user_pk'])
        if part.pk == ptopic.author.pk or part in ptopic.participants.all():
            messages.warning(
                request,
                'Le membre que vous essayez d\'ajouter '
                u'à la conversation y est déjà')
        else:
            ptopic.participants.add(part)
            ptopic.save()

            messages.success(
                request,
                'Le membre a bien été ajouté à la conversation')
    except:
        messages.warning(
            request, 'Le membre que vous avez essayé d\'ajouter n\'existe pas')

    return redirect(reverse('zds.mp.views.topic', args=[
        ptopic.pk,
        slugify(ptopic.title)]))
