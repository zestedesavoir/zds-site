# -*- coding: utf-8 -*-
from datetime import datetime
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404
from zds.forum.models import Forum, TopicFollowed, follow, follow_by_email
from django.utils.translation import ugettext as _
from zds.utils.forums import get_tag_by_title


class TopicEditMixin(object):
    def perform_follow(self, topic, user):
        return follow(topic, user)

    def perform_follow_by_email(self, topic, user):
        return follow_by_email(topic, user)

    def perform_solved(self, user, topic):
        if user == topic.author or user.has_perm("forum.change_topic"):
            topic.is_solved = not topic.is_solved
            return topic.is_solved
        else:
            raise PermissionDenied

    def perform_lock(self, topic, request):
        if request.user.has_perm("forum.change_topic"):
            topic.is_locked = request.POST.get('lock') == "true"
            if topic.is_locked:
                success_message = _(u'Le sujet {0} est désormais verrouillé.').format(topic.title)
            else:
                success_message = _(u'Le sujet {0} est désormais déverrouillé.').format(topic.title)
            messages.success(request, success_message)
        else:
            raise PermissionDenied

    def perform_sticky(self, topic, request):
        if request.user.has_perm("forum.change_topic"):
            topic.is_sticky = request.POST.get('sticky') == 'true'
            if topic.is_sticky:
                success_message = _(u'Le sujet « {0} » est désormais épinglé.').format(topic.title)
            else:
                success_message = _(u'Le sujet « {0} » n\'est désormais plus épinglé.').format(topic.title)
            messages.success(request, success_message)
        else:
            raise PermissionDenied

    def perform_move(self, request, topic):
        if request.user.has_perm("forum.change_topic"):
            try:
                forum_pk = int(request.POST.get('forum'))
            except (KeyError, ValueError, TypeError):
                raise Http404
            forum = get_object_or_404(Forum, pk=forum_pk)
            topic.forum = forum

            # If the topic is moved in a restricted forum, users that cannot read this topic any more un-follow it.
            # This avoids unreachable notifications.
            followers = TopicFollowed.objects.filter(topic=topic)
            for follower in followers:
                if not forum.can_read(follower.user):
                    follower.delete()
            messages.success(request, _(u"Le sujet {0} a bien été déplacé dans {1}.").format(topic.title, forum.title))
        else:
            raise PermissionDenied

    def perform_edit_info(self, topic, data, editor):
        (tags, title) = get_tag_by_title(data.get('title'))
        topic.title = title
        topic.subtitle = data.get('subtitle')
        topic.save()

        post = topic.first_post()
        post.update_content(data.get('text'))
        post.update = datetime.now()
        post.editor = editor
        post.save()

        # add tags
        topic.tags.clear()
        topic.add_tags(tags)
        return topic
