import json
import logging
from datetime import datetime

from django.contrib import messages
from django.http import HttpResponse, StreamingHttpResponse
from django.shortcuts import render
from django.utils.translation import gettext as _
from django.views.generic import CreateView
from django.views.generic.detail import SingleObjectMixin

from zds.forum.models import Forum, Post, Topic
from zds.member.views import get_client_ip
from zds.utils.misc import contains_utf8mb4, is_ajax
from zds.utils.mixins import QuoteMixin
from zds.utils.models import CommentVote, get_hat_from_request


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
    current_tag = ""
    current_title = ""
    tags = []
    continue_parsing_tags = True
    original_title = title

    for char in title:
        if char == "[" and nb_bracket == 0 and continue_parsing_tags:
            nb_bracket += 1
        elif nb_bracket > 0 and char != "]" and continue_parsing_tags:
            current_tag = current_tag + char
            if char == "[":
                nb_bracket += 1
        elif char == "]" and nb_bracket > 0 and continue_parsing_tags:
            nb_bracket -= 1
            if nb_bracket == 0 and current_tag.strip() != "":
                tags.append(current_tag.strip())
                current_tag = ""
            elif current_tag.strip() != "" and nb_bracket > 0:
                current_tag = current_tag + char

        elif (char != "[" and char.strip() != "") or not continue_parsing_tags:
            continue_parsing_tags = False
            current_title = current_title + char

    title = current_title
    # if we did not succed in parsing the tags
    if nb_bracket != 0:
        return [], original_title

    tags = [tag for tag in tags if not contains_utf8mb4(tag)]

    return tags, title.strip()


def create_topic(request, author, forum, title, subtitle, text, tags="", related_publishable_content=None):
    """create topic in forum"""

    # Creating the thread
    n_topic = Topic()
    n_topic.forum = forum
    n_topic.title = title
    n_topic.subtitle = subtitle
    n_topic.pubdate = datetime.now()
    n_topic.author = author

    n_topic.save()
    if related_publishable_content is not None:
        related_publishable_content.beta_topic = n_topic
        related_publishable_content.save()
    if tags:
        n_topic.add_tags(tags.split(","))
    n_topic.save()

    # Add the first message
    send_post(request, n_topic, n_topic.author, text)

    return n_topic


def send_post(
    request,
    topic,
    author,
    text,
):
    post = Post()
    post.topic = topic
    post.author = author
    post.pubdate = datetime.now()
    if topic.last_message is not None:
        post.position = topic.last_message.position + 1
    else:
        post.position = 1
    if request:
        post.update_content(
            text,
            on_error=lambda m: messages.error(request, _("Erreur du serveur Markdown:\n{}").format("\n- ".join(m))),
        )
        post.ip_address = get_client_ip(request)
        post.hat = get_hat_from_request(request)
    else:
        post.update_content(text, on_error=lambda m: logging.getLogger(__name__).error("--".join(m)))
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
        assert self.posts is not None, "Posts cannot be None."

        text = ""

        # Using the quote button
        if "cite" in request.GET:
            text = self.build_quote(request.GET.get("cite"), request.user)

            if is_ajax(request):
                return HttpResponse(json.dumps({"text": text}), content_type="application/json")

        form = self.create_forum(self.form_class, **{"text": text})
        context = {
            "topic": self.object,
            "posts": list(self.posts),
            "last_post_pk": self.object.last_message.pk,
            "form": form,
        }

        votes = CommentVote.objects.filter(
            user_id=self.request.user.pk, comment_id__in=[p.pk for p in context["posts"]]
        ).all()
        context["user_like"] = [vote.comment_id for vote in votes if vote.positive]
        context["user_dislike"] = [vote.comment_id for vote in votes if not vote.positive]
        context["is_staff"] = self.request.user.has_perm("forum.change_topic")

        if hasattr(self.object, "antispam"):
            context["is_antispam"] = self.object.antispam()

        if self.request.user.has_perm("forum.change_topic"):
            context["user_can_modify"] = [post.pk for post in context["posts"]]
        else:
            context["user_can_modify"] = [post.pk for post in context["posts"] if post.author == self.request.user]

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = self.get_form(self.form_class)
        new_post = None
        if not is_ajax(request):
            new_post = self.object.last_message.pk != int(request.POST.get("last_post"))

        if "preview" in request.POST or new_post:
            if is_ajax(request):
                content = render(request, "misc/preview.part.html", {"text": request.POST.get("text")})
                return StreamingHttpResponse(content)
            else:
                form = self.create_forum(self.form_class, **{"text": request.POST.get("text")})
        elif form.is_valid():
            return self.form_valid(form)

        return render(
            request,
            self.template_name,
            {
                "topic": self.object,
                "posts": self.posts,
                "last_post_pk": self.object.last_message.pk,
                "newpost": new_post,
                "form": form,
            },
        )

    def create_forum(self, form_class, **kwargs):
        raise NotImplementedError("`create_forum()` must be implemented.")
