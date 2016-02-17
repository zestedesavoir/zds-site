# -*- coding: utf-8 -*-
from datetime import datetime
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.generic.detail import SingleObjectMixin
from zds.forum.models import Forum, TopicFollowed, follow, follow_by_email, Post, TopicRead
from django.utils.translation import ugettext as _
from zds.utils.forums import get_tag_by_title
from zds.utils.models import Alert, CommentLike, CommentDislike


class TopicEditMixin(object):
    @staticmethod
    def perform_follow(topic, user):
        return follow(topic, user)

    @staticmethod
    def perform_follow_by_email(topic, user):
        return follow_by_email(topic, user)

    @staticmethod
    def perform_solve_or_unsolve(user, topic):
        if user == topic.author or user.has_perm("forum.change_topic"):
            topic.is_solved = not topic.is_solved
            return topic.is_solved
        else:
            raise PermissionDenied

    @staticmethod
    def perform_lock(topic, request):
        if request.user.has_perm("forum.change_topic"):
            topic.is_locked = request.POST.get('lock') == "true"
            if topic.is_locked:
                success_message = _(u'Le sujet « {0} » est désormais verrouillé.').format(topic.title)
            else:
                success_message = _(u'Le sujet « {0} » est désormais déverrouillé.').format(topic.title)
            messages.success(request, success_message)
        else:
            raise PermissionDenied

    @staticmethod
    def perform_sticky(topic, request):
        if request.user.has_perm("forum.change_topic"):
            topic.is_sticky = request.POST.get('sticky') == 'true'
            if topic.is_sticky:
                success_message = _(u'Le sujet « {0} » est désormais épinglé.').format(topic.title)
            else:
                success_message = _(u'Le sujet « {0} » n\'est désormais plus épinglé.').format(topic.title)
            messages.success(request, success_message)
        else:
            raise PermissionDenied

    @staticmethod
    def perform_move(request, topic):
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

            # Save topic to update update_index_date
            topic.save()
            messages.success(request,
                             _(u"Le sujet « {0} » a bien été déplacé dans « {1} ».").format(topic.title, forum.title))
        else:
            raise PermissionDenied

    @staticmethod
    def perform_edit_info(topic, data, editor):
        (tags, title) = get_tag_by_title(data.get('title'))
        topic.title = title
        topic.subtitle = data.get('subtitle')
        topic.save()

        PostEditMixin.perform_edit_post(topic.first_post(), editor, data.get('text'))

        # add tags
        topic.tags.clear()
        topic.add_tags(tags)
        return topic


class PostEditMixin(object):
    @staticmethod
    def perform_hide_message(request, post, user, data):
        is_staff = user.has_perm('forum.change_post')
        if post.author == user or is_staff:
            post.alerts.all().delete()
            post.is_visible = False
            post.editor = user

            if is_staff:
                post.text_hidden = data.get('text_hidden', '')

            messages.success(request, _(u'Le message est désormais masqué.'))
        else:
            raise PermissionDenied

    @staticmethod
    def perform_show_message(post, user):
        if user.has_perm('forum.change_post'):
            post.is_visible = True
            post.text_hidden = ''
        else:
            raise PermissionDenied

    @staticmethod
    def perform_alert_message(request, post, user, alert_text):
        alert = Alert()
        alert.author = user
        alert.comment = post
        alert.scope = Alert.FORUM
        alert.text = alert_text
        alert.pubdate = datetime.now()
        alert.save()

        messages.success(request, _(u'Une alerte a été envoyée à l\'équipe concernant ce message.'))

    @staticmethod
    def perform_useful(post):
        post.is_useful = not post.is_useful
        post.save()

    @staticmethod
    def perform_unread_message(post, user):
        """
        Marks a post unread so we create a notification between the user and the topic host of the post.
        But, if there is only one post in the topic, we mark the topic unread but we don't create a notification.
        """
        if TopicFollowed.objects.filter(user=user, topic=post.topic).count() == 0:
            TopicFollowed(user=user, topic=post.topic).save()

        topic_read = TopicRead.objects.filter(topic=post.topic, user=user).first()
        if topic_read is None and post.position > 1:
            unread = Post.objects.filter(topic=post.topic, position=(post.position - 1)).first()
            topic_read = TopicRead(post=unread, topic=unread.topic, user=user)
            topic_read.save()
        else:
            if post.position > 1:
                unread = Post.objects.filter(topic=post.topic, position=(post.position - 1)).first()
                topic_read.post = unread
                topic_read.save()
            else:
                topic_read.delete()

    @staticmethod
    def perform_like_post(post, user):
        """
        If the post isn't liked by the user before, the post is liked by the user and a dislike is removed if exists.
        Otherwise, the like is removed.
        """
        if post.author.pk != user.pk:
            if CommentLike.objects.filter(user__pk=user.pk, comments__pk=post.pk).count() == 0:
                like = CommentLike()
                like.user = user
                like.comments = post
                post.like = post.like + 1
                post.save()
                like.save()
                if CommentDislike.objects.filter(user__pk=user.pk, comments__pk=post.pk).count() > 0:
                    CommentDislike.objects.filter(user__pk=user.pk, comments__pk=post.pk).all().delete()
                    post.dislike = post.dislike - 1
                    post.save()
            else:
                CommentLike.objects.filter(user__pk=user.pk, comments__pk=post.pk).all().delete()
                post.like = post.like - 1
                post.save()

    @staticmethod
    def perform_dislike_post(post, user):
        """
        If the post isn't disliked by the user before, the post is disliked by the user and a like is removed if exists.
        Otherwise, the dislike is removed.
        """
        if post.author.pk != user.pk:
            if CommentDislike.objects.filter(user__pk=user.pk, comments__pk=post.pk).count() == 0:
                dislike = CommentDislike()
                dislike.user = user
                dislike.comments = post
                post.dislike = post.dislike + 1
                post.save()
                dislike.save()
                if CommentLike.objects.filter(user__pk=user.pk, comments__pk=post.pk).count() > 0:
                    CommentLike.objects.filter(user__pk=user.pk, comments__pk=post.pk).all().delete()
                    post.like = post.like - 1
                    post.save()
            else:
                CommentDislike.objects.filter(user__pk=user.pk, comments__pk=post.pk).all().delete()
                post.dislike = post.dislike - 1
                post.save()

    @staticmethod
    def perform_edit_post(post, user, text):
        post.update_content(text)
        post.update = datetime.now()
        post.editor = user
        post.save()

        if post.position == 1:
            # Save topic to update update_index_date
            post.topic.save()
        return post


class SinglePostObjectMixin(SingleObjectMixin):
    object = None

    def get_object(self, queryset=None):
        try:
            post_pk = int(self.request.GET.get('message'))
        except (KeyError, ValueError, TypeError):
            raise Http404
        return get_object_or_404(Post, pk=post_pk)
