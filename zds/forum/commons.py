from datetime import datetime

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from django.views.generic.detail import SingleObjectMixin
from django.contrib.auth.decorators import permission_required

from zds.forum.models import Forum, Post, TopicRead
from zds.notification import signals
from zds.notification.models import TopicAnswerSubscription, Notification, NewTopicSubscription
from zds.utils.models import Alert, CommentEdit, get_hat_from_request


class ForumEditMixin(object):
    @staticmethod
    def perform_follow(forum_or_tag, user):
        return NewTopicSubscription.objects.toggle_follow(forum_or_tag, user).is_active

    @staticmethod
    def perform_follow_by_email(forum_or_tag, user):
        return NewTopicSubscription.objects.toggle_follow(forum_or_tag, user, True).is_active


class TopicEditMixin(object):
    @staticmethod
    def perform_follow(topic, user):
        return TopicAnswerSubscription.objects.toggle_follow(topic, user)

    @staticmethod
    def perform_follow_by_email(topic, user):
        return TopicAnswerSubscription.objects.toggle_follow(topic, user, True)

    @staticmethod
    def perform_solve_or_unsolve(user, topic):
        if user == topic.author or user.has_perm('forum.change_topic'):
            topic.solved_by = None if topic.solved_by else user
            return topic.is_solved
        else:
            raise PermissionDenied

    @staticmethod
    @permission_required('forum.change_topic', raise_exception=True)
    def perform_lock(request, topic):
        topic.is_locked = request.POST.get('lock') == 'true'
        if topic.is_locked:
            success_message = _('Le sujet « {0} » est désormais verrouillé.').format(topic.title)
        else:
            success_message = _('Le sujet « {0} » est désormais déverrouillé.').format(topic.title)
        messages.success(request, success_message)

    @staticmethod
    @permission_required('forum.change_topic', raise_exception=True)
    def perform_sticky(request, topic):
        topic.is_sticky = request.POST.get('sticky') == 'true'
        if topic.is_sticky:
            success_message = _('Le sujet « {0} » est désormais épinglé.').format(topic.title)
        else:
            success_message = _("Le sujet « {0} » n'est désormais plus épinglé.").format(topic.title)
        messages.success(request, success_message)

    def perform_move(self):
        if self.request.user.has_perm('forum.change_topic'):
            try:
                forum_pk = int(self.request.POST.get('forum'))
            except (KeyError, ValueError, TypeError) as e:
                raise Http404('Forum not found', e)
            forum = get_object_or_404(Forum, pk=forum_pk)
            self.object.forum = forum

            # Save topic to update update_index_date
            self.object.save()

            signals.edit_content.send(sender=self.object.__class__, instance=self.object, action='move')
            message = _('Le sujet « {0} » a bien été déplacé dans « {1} ».').format(self.object.title, forum.title)
            messages.success(self.request, message)
        else:
            raise PermissionDenied()

    @staticmethod
    def perform_edit_info(request, topic, data, editor):
        topic.title = data.get('title')
        topic.subtitle = data.get('subtitle')
        topic.save()

        PostEditMixin.perform_edit_post(request, topic.first_post(), editor, data.get('text'))

        # add tags
        topic.tags.clear()
        if data.get('tags'):
            topic.add_tags(data.get('tags').split(','))

        return topic


class PostEditMixin(object):
    @staticmethod
    def perform_hide_message(request, post, user, data):
        is_staff = user.has_perm('forum.change_post')
        if post.author == user or is_staff:
            for alert in post.alerts_on_this_comment.all():
                alert.solve(user, _('Le message a été masqué.'))
            post.is_visible = False
            post.editor = user

            if is_staff:
                post.text_hidden = data.get('text_hidden', '')

            messages.success(request, _('Le message est désormais masqué.'))
            for user in Notification.objects.get_users_for_unread_notification_on(post):
                signals.content_read.send(sender=post.topic.__class__, instance=post.topic, user=user)
        else:
            raise PermissionDenied

    @staticmethod
    @permission_required('forum.change_post', raise_exception=True)
    def perform_show_message(request, post):
        post.is_visible = True
        post.text_hidden = ''

    @staticmethod
    def perform_alert_message(request, post, user, alert_text):
        alert = Alert(
            author=user,
            comment=post,
            scope='FORUM',
            text=alert_text,
            pubdate=datetime.now())
        alert.save()

        messages.success(request, _("Une alerte a été envoyée à l'équipe concernant ce message."))

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
        topic_read = TopicRead.objects.filter(topic=post.topic, user=user).first()
        # issue 3227 proves that you can have post.position==1 AND topic_read to None
        # it can happen whether on double click (the event "mark as not read" is therefore sent twice)
        # or if you have two tabs in your browser.
        if topic_read is None and post.position > 1:
            unread = Post.objects.filter(topic=post.topic, position=(post.position - 1)).first()
            topic_read = TopicRead(post=unread, topic=unread.topic, user=user)
            topic_read.save()
        else:
            if post.position > 1:
                unread = Post.objects.filter(topic=post.topic, position=(post.position - 1)).first()
                topic_read.post = unread
                topic_read.save()
            elif topic_read:
                topic_read.delete()

        signals.answer_unread.send(sender=post.topic.__class__, instance=post, user=user)

    @staticmethod
    def perform_edit_post(request, post, user, text):
        # create an archive
        edit = CommentEdit()
        edit.comment = post
        edit.editor = user
        edit.original_text = post.text
        edit.save()

        post.update_content(
            text,
            on_error=lambda m: messages.error(
                request,
                _('Erreur du serveur Markdown:\n{}').format('\n- '.join(m))))
        post.hat = get_hat_from_request(request, post.author)
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
