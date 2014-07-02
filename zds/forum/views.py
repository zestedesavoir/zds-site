#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import datetime
import json
import re

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMultiAlternatives
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.template import Context
from django.template.loader import get_template
from django.views.decorators.http import require_POST
from django.utils.encoding import smart_text

from haystack.inputs import AutoQuery
from haystack.query import SearchQuerySet

from forms import TopicForm, PostForm, MoveTopicForm
from models import Category, Forum, Topic, Post, follow, follow_by_email, never_read, \
    mark_read, TopicFollowed, sub_tag
from zds.forum.models import TopicRead
from zds.member.decorator import can_write_and_read_now
from zds.member.views import get_client_ip
from zds.utils import render_template, slugify
from zds.utils.models import Alert, CommentLike, CommentDislike, Tag
from zds.utils.mps import send_mp
from zds.utils.paginator import paginator_range
from zds.utils.templatetags.emarkdown import emarkdown
from zds.utils.templatetags.topbar import top_categories


def index(request):
    """Display the category list with all their forums."""

    categories = top_categories(request.user)

    return render_template("forum/index.html", {"categories": categories,
                                                "user": request.user})



def details(request, cat_slug, forum_slug):
    """Display the given forum and all its topics."""

    forum = get_object_or_404(Forum, slug=forum_slug)
    if not forum.can_read(request.user):
        raise PermissionDenied
    sticky_topics = Topic.objects.filter(forum__pk=forum.pk, is_sticky=True).order_by(
        "-last_message__pubdate").prefetch_related("author", "last_message", "tags").all()
    if "filter" in request.GET:
        filter = request.GET["filter"]
        if request.GET["filter"] == "solve":
            topics = Topic.objects.filter(
                forum__pk=forum.pk,
                is_sticky=False,
                is_solved=True).order_by("-last_message__pubdate").prefetch_related(
                "author",
                "last_message",
                "tags").all()
        else:
            topics = Topic.objects.filter(
                forum__pk=forum.pk,
                is_sticky=False,
                is_solved=False).order_by("-last_message__pubdate").prefetch_related(
                "author",
                "last_message",
                "tags").all()
    else:
        filter = None
        topics = Topic.objects.filter(forum__pk=forum.pk, is_sticky=False) .order_by(
            "-last_message__pubdate").prefetch_related("author", "last_message", "tags").all()

    # Paginator

    paginator = Paginator(topics, settings.TOPICS_PER_PAGE)
    page = request.GET.get("page")
    try:
        shown_topics = paginator.page(page)
        page = int(page)
    except PageNotAnInteger:
        shown_topics = paginator.page(1)
        page = 1
    except EmptyPage:
        shown_topics = paginator.page(paginator.num_pages)
        page = paginator.num_pages

    return render_template("forum/category/forum.html", {
        "forum": forum,
        "sticky_topics": sticky_topics,
        "topics": shown_topics,
        "pages": paginator_range(page, paginator.num_pages),
        "nb": page,
        "filter": filter,
    })



def cat_details(request, cat_slug):
    """Display the forums belonging to the given category."""
    
    category = get_object_or_404(Category, slug=cat_slug)
    
    forums_pub = Forum.objects.filter(group__isnull=True).select_related("category").all()
    if request.user.is_authenticated():
        forums_prv = Forum.objects.filter(group__isnull=False).select_related("category").all()
        out = []
        for forum in forums_prv:
            if forum.can_read(request.user):
                out.append(forum.pk)
        forums = forums_pub|forums_prv.exclude(pk__in=out)
    else :
        forums = forums_pub

    return render_template("forum/category/index.html", {"category": category,
                                                         "forums": forums})



def topic(request, topic_pk, topic_slug):
    """Display a thread and its posts using a pager."""

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

    # Retrieves all posts of the topic and use paginator with them.

    posts = \
        Post.objects.filter(topic__pk=topic.pk) \
        .select_related() \
        .order_by("position"
                  ).all()
    last_post_pk = topic.last_message.pk

    # Handle pagination

    paginator = Paginator(posts, settings.POSTS_PER_PAGE)

    # The category list is needed to move threads

    categories = Category.objects.all()
    try:
        page_nbr = int(request.GET["page"])
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
        last_post = last_page[len(last_page) - 1]
        res.append(last_post)
    for post in posts:
        res.append(post)

    # Build form to send a post for the current topic.

    form = PostForm(topic, request.user)
    form.helper.form_action = reverse("zds.forum.views.answer") + "?sujet=" \
        + str(topic.pk)
    form_move = MoveTopicForm(topic=topic)

    return render_template("forum/topic/index.html", {
        "topic": topic,
        "posts": res,
        "categories": categories,
        "pages": paginator_range(page_nbr, paginator.num_pages),
        "nb": page_nbr,
        "last_post_pk": last_post_pk,
        "form": form,
        "form_move": form_move,
    })


def get_tag_by_title(title):
    nb_bracket = 0
    current_tag = u""
    current_title = u""
    tags = []
    continue_parsing_tags = True
    original_title = title
    for char in title:
		
        if char == u"[" and nb_bracket == 0 and continue_parsing_tags:
            nb_bracket += 1
        elif nb_bracket > 0 and char != u"]" and continue_parsing_tags:
            current_tag = current_tag + char
            if char == u"[" :
                nb_bracket += 1
        elif char == u"]" and nb_bracket > 0 and continue_parsing_tags:
            nb_bracket -= 1
            if nb_bracket == 0 and current_tag.strip() != u"":
                tags.append(current_tag.strip())
                current_tag = u""
            elif current_tag.strip() != u"" and nb_bracket > 0:
                current_tag = current_tag + char
                
        elif ((char != u"[" and char.strip()!="") or not continue_parsing_tags):
            continue_parsing_tags = False
            current_title = current_title + char
    title = current_title
    #if we did not succed in parsing the tags
    if nb_bracket != 0 :
        return ([],original_title)

    return (tags, title.strip())


@can_write_and_read_now
@login_required
@transaction.atomic
def new(request):
    """Creates a new topic in a forum."""

    try:
        forum_pk = request.GET["forum"]
    except KeyError:
        raise Http404
    forum = get_object_or_404(Forum, pk=forum_pk)
    if not forum.can_read(request.user):
        raise PermissionDenied
    if request.method == "POST":

        # If the client is using the "preview" button

        if "preview" in request.POST:
            form = TopicForm(initial={"title": request.POST["title"],
                                      "subtitle": request.POST["subtitle"],
                                      "text": request.POST["text"]})
            return render_template("forum/topic/new.html",
                                   {"forum": forum,
                                    "form": form,
                                    "text": request.POST["text"]})
        form = TopicForm(request.POST)
        data = form.data
        if form.is_valid():

            # Treat title

            (tags, title) = get_tag_by_title(data["title"])

            # Creating the thread
            n_topic = Topic()
            n_topic.forum = forum
            n_topic.title = title
            n_topic.subtitle = data["subtitle"]
            n_topic.pubdate = datetime.now()
            n_topic.author = request.user
            n_topic.save()
            # add tags

            n_topic.add_tags(tags)
            n_topic.save()
            # Adding the first message

            post = Post()
            post.topic = n_topic
            post.author = request.user
            post.text = data["text"]
            post.text_html = emarkdown(request.POST["text"])
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

    return render_template("forum/topic/new.html", {"forum": forum, "form": form})


@can_write_and_read_now
@login_required
@require_POST
@transaction.atomic
def solve_alert(request):

    # only staff can move topic

    if not request.user.has_perm("forum.change_post"):
        raise PermissionDenied
    alert = get_object_or_404(Alert, pk=request.POST["alert_pk"])
    post = Post.objects.get(pk=alert.comment.id)
    bot = get_object_or_404(User, username=settings.BOT_ACCOUNT)
    msg = \
        (u'Bonjour {0},'
        u'Vous recevez ce message car vous avez signalé le message de *{1}*, '
        u'dans le sujet [{2}]({3}). Votre alerte a été traitée par **{4}** '
        u'et il vous a laissé le message suivant :'
        u'\n\n`{5}`\n\nToute l\'équipe de la modération vous remercie'.format(
            alert.author.username,
            post.author.username,
            post.topic.title,
            settings.SITE_URL + post.get_absolute_url(),
            request.user.username,
            request.POST["text"],))
    send_mp(
        bot,
        [alert.author],
        u"Résolution d'alerte : {0}".format(post.topic.title),
        "",
        msg,
        False,
    )
    alert.delete()
    messages.success(request, u"L'alerte a bien été résolue")
    return redirect(post.get_absolute_url())


@can_write_and_read_now
@login_required
@require_POST
@transaction.atomic
def move_topic(request):

    # only staff can move topic

    if not request.user.has_perm("forum.change_topic"):
        raise PermissionDenied
    try:
        topic_pk = request.GET["sujet"]
    except KeyError:
        raise Http404
    forum = get_object_or_404(Forum, pk=request.POST["forum"])
    if not forum.can_read(request.user):
        raise PermissionDenied
    topic = get_object_or_404(Topic, pk=topic_pk)
    topic.forum = forum
    topic.save()

    # unfollow user auth

    followers = TopicFollowed.objects.filter(topic=topic)
    for follower in followers:
        if not forum.can_read(follower.user):
            follower.delete()
    messages.success(request,
                     u"Le sujet {0} a bien été déplacé dans {1}."
                     .format(topic.title,
                             forum.title))
    return redirect(topic.get_absolute_url())


@can_write_and_read_now
@login_required
@require_POST
def edit(request):
    """Edit the given topic."""

    try:
        topic_pk = request.POST["topic"]
    except KeyError:
        raise Http404
    try:
        page = int(request.POST["page"])
    except KeyError:
        page = 1
    data = request.POST
    resp = {}
    g_topic = get_object_or_404(Topic, pk=topic_pk)
    if "follow" in data:
        resp["follow"] = follow(g_topic)
    if "email" in data:
        resp["email"] = follow_by_email(g_topic)
    if request.user == g_topic.author \
            or request.user.has_perm("forum.change_topic"):
        if "solved" in data:
            g_topic.is_solved = not g_topic.is_solved
            resp["solved"] = g_topic.is_solved
    if request.user.has_perm("forum.change_topic"):

        # Staff actions using AJAX TODO: Do not redirect on AJAX requests

        if "lock" in data:
            g_topic.is_locked = data["lock"] == "true"
            messages.success(request,
                             u"Le sujet {0} est désormais vérouillé."
                             .format(g_topic.title))
        if "sticky" in data:
            g_topic.is_sticky = data["sticky"] == "true"
            messages.success(request,
                             u"Le sujet {0} est désormais épinglé."
                             .format(g_topic.title))
        if "move" in data:
            try:
                forum_pk = int(request.POST["move_target"])
            except KeyError:
                raise Http404
            forum = get_object_or_404(Forum, pk=forum_pk)
            g_topic.forum = forum
    g_topic.save()
    if request.is_ajax():
        return HttpResponse(json.dumps(resp))
    else:
        if not g_topic.forum.can_read(request.user):
            return redirect(reverse("zds.forum.views.index"))
        else:
            return redirect(u"{}?page={}".format(g_topic.get_absolute_url(),
                                                 page))


@can_write_and_read_now
@login_required
@transaction.atomic
def answer(request):
    """Adds an answer from a user to a topic."""

    try:
        topic_pk = request.GET["sujet"]
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

    # Retrieve 10 last posts of the current topic.

    posts = \
        Post.objects.filter(topic=g_topic) \
        .prefetch_related() \
        .order_by("-pubdate"
                  )[:10]

    # User would like preview his post or post a new post on the topic.

    if request.method == "POST":
        data = request.POST
        newpost = last_post_pk != int(data["last_post"])

        # Using the « preview button », the « more » button or new post

        if "preview" in data or newpost:
            form = PostForm(g_topic, request.user, initial={"text": data["text"
                                                                         ]})
            form.helper.form_action = reverse("zds.forum.views.answer") \
                + "?sujet=" + str(g_topic.pk)
            return render_template("forum/post/new.html", {
                "text": data["text"],
                "topic": g_topic,
                "posts": posts,
                "last_post_pk": last_post_pk,
                "newpost": newpost,
                "form": form,
            })
        else:

            # Saving the message

            form = PostForm(g_topic, request.user, request.POST)
            if form.is_valid():
                data = form.data
                post = Post()
                post.topic = g_topic
                post.author = request.user
                post.text = data["text"]
                post.text_html = emarkdown(data["text"])
                post.pubdate = datetime.now()
                post.position = g_topic.get_post_count() + 1
                post.ip_address = get_client_ip(request)
                post.save()
                g_topic.last_message = post
                g_topic.save()
                #Send mail
                subject = "ZDS - Notification : " + g_topic.title
                from_email = "Zeste de Savoir <{0}>".format(settings.MAIL_NOREPLY)
                followers = g_topic.get_followers_by_email()
                for follower in followers:
                    receiver = follower.user
                    if receiver == request.user:
                        continue
                    pos = post.position - 1
                    last_read = TopicRead.objects.filter(
                        topic=g_topic,
                        post__position=pos,
                        user=receiver).count()
                    if last_read > 0:
                        message_html = get_template('email/notification/new.html') \
                            .render(
                                Context({
                                    'username': receiver.username,
                                    'title':g_topic.title,
                                    'url': settings.SITE_URL + post.get_absolute_url(),
                                    'author': request.user.username
                                })
                        )
                        message_txt = get_template('email/notification/new.txt').render(
                            Context({
                                'username': receiver.username,
                                'title':g_topic.title,
                                'url': settings.SITE_URL + post.get_absolute_url(),
                                'author': request.user.username
                            })
                        )
                        msg = EmailMultiAlternatives(
                            subject, message_txt, from_email, [
                                receiver.email])
                        msg.attach_alternative(message_html, "text/html")
                        msg.send()

                # Follow topic on answering
                if not g_topic.is_followed(user=request.user):
                    follow(g_topic)
                return redirect(post.get_absolute_url())
            else:
                return render_template("forum/post/new.html", {
                    "text": data["text"],
                    "topic": g_topic,
                    "posts": posts,
                    "last_post_pk": last_post_pk,
                    "newpost": newpost,
                    "form": form,
                })
    else:

        # Actions from the editor render to new.html.

        text = ""

        # Using the quote button

        if "cite" in request.GET:
            post_cite_pk = request.GET["cite"]
            post_cite = Post.objects.get(pk=post_cite_pk)
            if not post_cite.is_visible:
                raise PermissionDenied
            for line in post_cite.text.splitlines():
                text = text + "> " + line + "\n"
            text = u"{0}Source:[{1}]({2}{3})".format(
                text,
                post_cite.author.username,
                settings.SITE_URL,
                post_cite.get_absolute_url())

        form = PostForm(g_topic, request.user, initial={"text": text})
        form.helper.form_action = reverse("zds.forum.views.answer") \
            + "?sujet=" + str(g_topic.pk)
        return render_template("forum/post/new.html", {
            "topic": g_topic,
            "posts": posts,
            "last_post_pk": last_post_pk,
            "form": form,
        })


@can_write_and_read_now
@login_required
@transaction.atomic
def edit_post(request):
    """Edit the given user's post."""

    try:
        post_pk = request.GET["message"]
    except KeyError:
        raise Http404
    post = get_object_or_404(Post, pk=post_pk)
    if not post.topic.forum.can_read(request.user):
        raise PermissionDenied
    g_topic = None
    if post.position <= 1:
        g_topic = get_object_or_404(Topic, pk=post.topic.pk)

    # Making sure the user is allowed to do that. Author of the post must to be
    # the user logged.

    if post.author != request.user \
            and not request.user.has_perm("forum.change_post") and "signal_message" \
            not in request.POST:
        raise PermissionDenied
    if post.author != request.user and request.method == "GET" \
            and request.user.has_perm("forum.change_post"):
        messages.warning(request,
                         u'Vous \xe9ditez ce message en tant que '
                         u'mod\xe9rateur (auteur : {}). Soyez encore plus '
                         u'prudent lors de l\'\xe9dition de celui-ci !'
                         .format(post.author.username))
    if request.method == "POST":
        if "delete_message" in request.POST:
            if post.author == request.user \
                    or request.user.has_perm("forum.change_post"):
                post.alerts.all().delete()
                post.is_visible = False
                if request.user.has_perm("forum.change_post"):
                    post.text_hidden = request.POST["text_hidden"]
                post.editor = request.user
                messages.success(request, u"Le message est désormais masqué")
        if "show_message" in request.POST:
            if request.user.has_perm("forum.change_post"):
                post.is_visible = True
                post.text_hidden = ""
        if "signal_message" in request.POST:
            alert = Alert()
            alert.author = request.user
            alert.comment = post
            alert.scope = Alert.FORUM
            alert.text = request.POST['signal_text']
            alert.pubdate = datetime.now()
            alert.save()
            messages.success(request,
                             u'Une alerte a été envoyée '
                             u'à l\'équipe concernant '
                             u'ce message')

        # Using the preview button

        if "preview" in request.POST:
            if g_topic:
                form = TopicForm(initial={"title": request.POST["title"],
                                          "subtitle": request.POST["subtitle"],
                                          "text": request.POST["text"]})
            else:
                form = PostForm(post.topic, request.user,
                                initial={"text": request.POST["text"]})
            form.helper.form_action = reverse("zds.forum.views.edit_post") \
                + "?message=" + str(post_pk)
            return render_template("forum/post/edit.html", {
                "post": post,
                "topic": post.topic,
                "text": request.POST["text"],
                "form": form,
            })

        if "delete_message" not in request.POST and "signal_message" \
                not in request.POST and "show_message" not in request.POST:
            # The user just sent data, handle them

            if request.POST["text"].strip() != "":
                post.text = request.POST["text"]
                post.text_html = emarkdown(request.POST["text"])
                post.update = datetime.now()
                post.editor = request.user

            # Modifying the thread info

            if g_topic:
                (tags, title) = get_tag_by_title(request.POST["title"])
                g_topic.title = title
                g_topic.subtitle = request.POST["subtitle"]
                g_topic.save()
                g_topic.tags.clear()

                # add tags

                g_topic.add_tags(tags)
        post.save()
        return redirect(post.get_absolute_url())
    else:
        if g_topic:
            prefix = u""
            for tag in g_topic.tags.all():
                prefix += u"[{0}]".format(tag.title)
            form = TopicForm(
                initial={
                    "title": u"{0} {1}".format(
                        prefix,
                        g_topic.title).strip(),
                    "subtitle": g_topic.subtitle,
                    "text": post.text})
        else:
            form = PostForm(post.topic, request.user,
                            initial={"text": post.text})
        form.helper.form_action = reverse("zds.forum.views.edit_post") \
            + "?message=" + str(post_pk)
        return render_template("forum/post/edit.html", {
            "post": post,
            "topic": post.topic,
            "text": post.text,
            "form": form,
        })


@can_write_and_read_now
@login_required
@require_POST
def useful_post(request):
    """Marks a message as useful (for the OP)"""

    try:
        post_pk = request.GET["message"]
    except KeyError:
        raise Http404
    post = get_object_or_404(Post, pk=post_pk)

    # check that author can access the forum

    if not post.topic.forum.can_read(request.user):
        raise PermissionDenied

    # Making sure the user is allowed to do that

    if post.author == request.user or request.user != post.topic.author:
        if not request.user.has_perm("forum.change_post"):
            raise PermissionDenied
    post.is_useful = not post.is_useful
    post.save()
    return redirect(post.get_absolute_url())


@can_write_and_read_now
@login_required
def unread_post(request):
    """Marks a message as unread """

    try:
        post_pk = request.GET["message"]
    except KeyError:
        raise Http404
    post = get_object_or_404(Post, pk=post_pk)

    # check that author can access the forum

    if not post.topic.forum.can_read(request.user):
        raise PermissionDenied

    t = TopicRead.objects.filter(topic=post.topic, user=request.user).first()
    if t is None:
        if post.position > 1:
            unread = Post.objects.filter(topic=post.topic, position=(post.position - 1)).first()
            t = TopicRead(post=unread, topic=unread.topic, user=request.user)
            t.save()
    else:
        if post.position > 1:
            unread = Post.objects.filter(topic=post.topic, position=(post.position - 1)).first()
            t.post = unread
            t.save()
        else:
            t.delete()

    return redirect(reverse("zds.forum.views.details", args=[post.topic.forum.category.slug, post.topic.forum.slug]))


@can_write_and_read_now
@login_required
@require_POST
def like_post(request):
    """Like a post."""

    try:
        post_pk = request.GET["message"]
    except KeyError:
        raise Http404
    resp = {}
    post = get_object_or_404(Post, pk=post_pk)
    user = request.user
    if not post.topic.forum.can_read(request.user):
        raise PermissionDenied
    if post.author.pk != request.user.pk:

        # Making sure the user is allowed to do that

        if CommentLike.objects.filter(user__pk=user.pk,
                                      comments__pk=post_pk).count() == 0:
            like = CommentLike()
            like.user = user
            like.comments = post
            post.like = post.like + 1
            post.save()
            like.save()
            if CommentDislike.objects.filter(user__pk=user.pk,
                                             comments__pk=post_pk).count() > 0:
                CommentDislike.objects.filter(
                    user__pk=user.pk,
                    comments__pk=post_pk).all().delete()
                post.dislike = post.dislike - 1
                post.save()
        else:
            CommentLike.objects.filter(user__pk=user.pk,
                                       comments__pk=post_pk).all().delete()
            post.like = post.like - 1
            post.save()
    resp["upvotes"] = post.like
    resp["downvotes"] = post.dislike
    if request.is_ajax():
        return HttpResponse(json.dumps(resp), content_type='application/json')
    else:
        return redirect(post.get_absolute_url())


@can_write_and_read_now
@login_required
@require_POST
def dislike_post(request):
    """Dislike a post."""

    try:
        post_pk = request.GET["message"]
    except KeyError:
        raise Http404
    resp = {}
    post = get_object_or_404(Post, pk=post_pk)
    user = request.user
    if not post.topic.forum.can_read(request.user):
        raise PermissionDenied
    if post.author.pk != request.user.pk:

        # Making sure the user is allowed to do that

        if CommentDislike.objects.filter(user__pk=user.pk,
                                         comments__pk=post_pk).count() == 0:
            dislike = CommentDislike()
            dislike.user = user
            dislike.comments = post
            post.dislike = post.dislike + 1
            post.save()
            dislike.save()
            if CommentLike.objects.filter(user__pk=user.pk,
                                          comments__pk=post_pk).count() > 0:
                CommentLike.objects.filter(user__pk=user.pk,
                                           comments__pk=post_pk).all().delete()
                post.like = post.like - 1
                post.save()
        else:
            CommentDislike.objects.filter(user__pk=user.pk,
                                          comments__pk=post_pk).all().delete()
            post.dislike = post.dislike - 1
            post.save()
    resp["upvotes"] = post.like
    resp["downvotes"] = post.dislike
    if request.is_ajax():
        return HttpResponse(json.dumps(resp))
    else:
        return redirect(post.get_absolute_url())



def find_topic_by_tag(request, tag_pk, tag_slug):
    """Finds all topics byg tag."""

    tag = Tag.objects.filter(pk=tag_pk, slug=tag_slug).first()
    if tag is None:
        return redirect(reverse("zds.forum.views.index"))
    if "filter" in request.GET:
        filter = request.GET["filter"]
        if request.GET["filter"] == "solve":
            topics = Topic.objects.filter(
                tags__in=[tag],
                is_sticky=False,
                is_solved=True).order_by("-last_message__pubdate").prefetch_related(
                "author",
                "last_message",
                "tags").all()
        else:
            topics = Topic.objects.filter(
                tags__in=[tag],
                is_sticky=False,
                is_solved=False).order_by("-last_message__pubdate").prefetch_related(
                "author",
                "last_message",
                "tags").all()
    else:
        filter = None
        topics = Topic.objects.filter(tags__in=[tag], is_sticky=False) .order_by(
            "-last_message__pubdate").prefetch_related("author", "last_message", "tags").all()
    tops = []
    for top in topics:
        if not top.forum.can_read(request.user):
            continue
        else:
            tops.append(top)

    # Paginator

    paginator = Paginator(tops, settings.TOPICS_PER_PAGE)
    page = request.GET.get("page")
    try:
        shown_topics = paginator.page(page)
        page = int(page)
    except PageNotAnInteger:
        shown_topics = paginator.page(1)
        page = 1
    except EmptyPage:
        shown_topics = paginator.page(paginator.num_pages)
        page = paginator.num_pages
    return render_template("forum/find/topic_by_tag.html", {
        "topics": shown_topics,
        "tag": tag,
        "pages": paginator_range(page, paginator.num_pages),
        "nb": page,
        "filter": filter,
    })



def find_topic(request, user_pk):
    """Finds all topics of a user."""

    u = get_object_or_404(User, pk=user_pk)
    topics = \
        Topic.objects.filter(author=u).prefetch_related().order_by("-pubdate"
                                                                   ).all()
    tops = []
    for top in topics:
        if not top.forum.can_read(request.user):
            continue
        else:
            tops.append(top)

    # Paginator

    paginator = Paginator(tops, settings.TOPICS_PER_PAGE)
    page = request.GET.get("page")
    try:
        shown_topics = paginator.page(page)
        page = int(page)
    except PageNotAnInteger:
        shown_topics = paginator.page(1)
        page = 1
    except EmptyPage:
        shown_topics = paginator.page(paginator.num_pages)
        page = paginator.num_pages

    return render_template("forum/find/topic.html", {
        "topics": shown_topics,
        "usr": u,
        "pages": paginator_range(page, paginator.num_pages),
        "nb": page,
    })



def find_post(request, user_pk):
    """Finds all posts of a user."""

    u = get_object_or_404(User, pk=user_pk)
    posts = \
        Post.objects.filter(author=u).prefetch_related().order_by("-pubdate"
                                                                  ).all()
    pts = []

    for post in posts:
        if not post.topic.forum.can_read(request.user):
            continue
        else:
            pts.append(post)

    # Paginator

    paginator = Paginator(pts, settings.POSTS_PER_PAGE)
    page = request.GET.get("page")
    try:
        shown_posts = paginator.page(page)
        page = int(page)
    except PageNotAnInteger:
        shown_posts = paginator.page(1)
        page = 1
    except EmptyPage:
        shown_posts = paginator.page(paginator.num_pages)
        page = paginator.num_pages

    return render_template("forum/find/post.html", {
        "posts": shown_posts,
        "usr": u,
        "pages": paginator_range(page, paginator.num_pages),
        "nb": page,
    })


@login_required

def followed_topics(request):
    followed_topics = request.user.get_profile().get_followed_topics()

    # Paginator

    paginator = Paginator(followed_topics, settings.FOLLOWED_TOPICS_PER_PAGE)
    page = request.GET.get("page")
    try:
        shown_topics = paginator.page(page)
        page = int(page)
    except PageNotAnInteger:
        shown_topics = paginator.page(1)
        page = 1
    except EmptyPage:
        shown_topics = paginator.page(paginator.num_pages)
        page = paginator.num_pages
    return render_template("forum/topic/followed.html",
                           {"followed_topics": shown_topics,
                            "pages": paginator_range(page,
                                                     paginator.num_pages),
                            "nb": page})


def complete_topic(request):
    sqs = SearchQuerySet().filter(content=AutoQuery(request.GET.get('q'))).order_by('-pubdate').all()

    suggestions = {}

    cpt = 0
    for result in sqs:
        if cpt > 5:
            break
        if 'Topic' in str(result.model) and result.object.is_solved:
            suggestions[str(result.object.pk)] = (result.title, result.author, result.object.get_absolute_url())
            cpt += 1

    the_data = json.dumps(suggestions)

    return HttpResponse(the_data, content_type='application/json')
