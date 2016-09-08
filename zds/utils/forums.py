# coding: utf-8

import json
from datetime import datetime

from django.http import HttpResponse, StreamingHttpResponse
from django.shortcuts import render, render_to_response
from django.views.generic import CreateView
from django.views.generic.detail import SingleObjectMixin

from zds.forum.models import Topic, Post
from zds.member.views import get_client_ip
from zds.utils.mixins import QuoteMixin
from zds.utils.models import CommentVote


def create_topic(
        request,
        author,
        forum,
        title,
        subtitle,
        text,
        tags='',
        key=None,
        related_publishable_content=None):
    """create topic in forum"""

    # Creating the thread
    n_topic = Topic()
    n_topic.forum = forum
    n_topic.title = title
    n_topic.subtitle = subtitle
    n_topic.pubdate = datetime.now()
    n_topic.author = author
    n_topic.key = key

    n_topic.save()
    if related_publishable_content is not None:
        related_publishable_content.beta_topic = n_topic
        related_publishable_content.save()
    if tags:
        n_topic.add_tags(tags.split(','))
    n_topic.save()

    # Add the first message
    send_post(request, n_topic, n_topic.author, text)

    return n_topic


def send_post(request, topic, author, text,):
    post = Post()
    post.topic = topic
    post.author = author
    post.update_content(text)
    post.pubdate = datetime.now()
    if topic.last_message is not None:
        post.position = topic.last_message.position + 1
    else:
        post.position = 1
    post.ip_address = get_client_ip(request)
    post.save()

    topic.last_message = post
    topic.save()
    return topic


def lock_topic(topic):
    topic.is_locked = True
    topic.save()


def unlock_topic(topic):
    topic.is_locked = False
    topic.save()


class CreatePostView(CreateView, SingleObjectMixin, QuoteMixin):
    posts = None

    def get(self, request, *args, **kwargs):
        assert self.posts is not None, ('Posts cannot be None.')

        text = ''

        # Using the quote button
        if "cite" in request.GET:
            text = self.build_quote(request.GET.get('cite'))

            if request.is_ajax():
                return HttpResponse(json.dumps({'text': text}), content_type='application/json')

        form = self.create_forum(self.form_class, **{'text': text})
        context = {
            'topic': self.object,
            'posts': list(self.posts),
            'last_post_pk': self.object.last_message.pk,
            'form': form,
        }

        votes = CommentVote.objects.filter(user_id=self.request.user.pk,
                                           comment_id__in=[p.pk for p in context['posts']]).all()
        context["user_like"] = [vote.comment_id for vote in votes if vote.positive]
        context["user_dislike"] = [vote.comment_id for vote in votes if not vote.positive]
        context["is_staff"] = self.request.user.has_perm('forum.change_topic')

        if hasattr(self.object, 'antispam'):
            context['isantispam'] = self.object.antispam()

        if self.request.user.has_perm('forum.change_topic'):
            context["user_can_modify"] = [post.pk for post in context['posts']]
        else:
            context["user_can_modify"] = [post.pk for post in context['posts'] if post.author == self.request.user]

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = self.get_form(self.form_class)
        new_post = None
        if not request.is_ajax():
            new_post = self.object.last_message.pk != int(request.POST.get('last_post'))

        if 'preview' in request.POST or new_post:
            if request.is_ajax():
                content = render_to_response('misc/previsualization.part.html', {'text': request.POST.get('text')})
                return StreamingHttpResponse(content)
            else:
                form = self.create_forum(self.form_class, **{'text': request.POST.get('text')})
        elif form.is_valid():
            return self.form_valid(form)

        return render(request, self.template_name, {
            'topic': self.object,
            'posts': self.posts,
            'last_post_pk': self.object.last_message.pk,
            'newpost': new_post,
            'form': form,
        })

    def create_forum(self, form_class, **kwargs):
        raise NotImplementedError('`create_forum()` must be implemented.')
