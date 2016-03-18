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


def get_tag_by_title(title):
    """
    Extract tags from title.
    In a title, tags can be set this way:
    > [Tag 1][Tag 2] There is the real title
    Rules to detect tags:
    - Tags are enclosed in square brackets. This allows multi-word tags instead of hashtags.
    - Tags can embed square brackets: [Tag] is a valid tag and must be written [[Tag]] in the raw title
    - All tags must be declared at the beginning of the title. Example: _"Title [tag]"_ will not create a tag.
    - Tags and title correctness (example: empty tag/title detection) is **not** checked here
    :param title: The raw title
    :return: A tuple: (the tag list, the title without the tags).
    """
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
            if char == u"[":
                nb_bracket += 1
        elif char == u"]" and nb_bracket > 0 and continue_parsing_tags:
            nb_bracket -= 1
            if nb_bracket == 0 and current_tag.strip() != u"":
                tags.append(current_tag.strip())
                current_tag = u""
            elif current_tag.strip() != u"" and nb_bracket > 0:
                current_tag = current_tag + char

        elif (char != u"[" and char.strip() != "") or not continue_parsing_tags:
            continue_parsing_tags = False
            current_title = current_title + char
    title = current_title
    # if we did not succed in parsing the tags
    if nb_bracket != 0:
        return [], original_title

    return tags, title.strip()


def create_topic(
        request,
        author,
        forum,
        title,
        subtitle,
        text,
        key=None,
        related_publishable_content=None):
    """create topic in forum"""

    (tags, title_only) = get_tag_by_title(title[:Topic._meta.get_field('title').max_length])

    # Creating the thread
    n_topic = Topic()
    n_topic.forum = forum
    n_topic.title = title_only
    n_topic.subtitle = subtitle
    n_topic.pubdate = datetime.now()
    n_topic.author = author
    n_topic.key = key

    n_topic.save()
    if related_publishable_content is not None:
        related_publishable_content.beta_topic = n_topic
        related_publishable_content.save()
    n_topic.add_tags(tags)
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
        return render(request, self.template_name, {
            'topic': self.object,
            'posts': self.posts,
            'last_post_pk': self.object.last_message.pk,
            'form': form,
        })

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
