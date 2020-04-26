from datetime import datetime

from django.views.generic.detail import SingleObjectMixin
from django.http import Http404
from django.shortcuts import get_object_or_404

from zds.mp.models import PrivateTopicRead, PrivatePost
from zds.utils.templatetags.emarkdown import emarkdown
from zds.notification import signals


class LeavePrivateTopic(object):
    """
    Leave a private topic.
    """

    def perform_destroy(self, instance):
        if instance.participants.count() == 0:
            instance.delete()
        elif self.get_current_user().pk == instance.author.pk:
            move = instance.participants.first()
            instance.author = move
            instance.participants.remove(move)
            instance.save()
        else:
            instance.participants.remove(self.get_current_user())
            instance.save()

    def get_current_user(self):
        raise NotImplementedError('`get_current_user()` must be implemented.')


class UpdatePrivatePost(object):
    """
    Updates a private topic.
    """

    def perform_update(self, instance, data, hat=None):
        instance.hat = hat
        instance.text = data.get('text')
        instance.text_html = emarkdown(data.get('text'))
        instance.update = datetime.now()
        instance.save()
        return instance

    @staticmethod
    def perform_unread_private_post(post, user):
        """
        Mark the private post as unread. If it is in first position, the whole topic is marked as unread.
        """
        # mark the previous post as read
        try:
            previous_post = PrivatePost.objects.get(privatetopic=post.privatetopic,
                                                    position_in_topic=post.position_in_topic - 1)
            # update the record, if it exists
            try:
                topic = PrivateTopicRead.objects.get(privatetopic=post.privatetopic, user=user)
                topic.privatepost = previous_post
            # no existing record to update, create a new record
            except PrivateTopicRead.DoesNotExist:
                topic = PrivateTopicRead(privatepost=previous_post, privatetopic=post.privatetopic, user=user)
            topic.save()
        # no previous post to mark as read, remove the topic from read list instead
        except PrivatePost.DoesNotExist:
            try:
                topic = PrivateTopicRead.objects.get(privatetopic=post.privatetopic, user=user)
                topic.delete()
            except PrivateTopicRead.DoesNotExist:  # record already removed, nothing to do
                pass

        signals.answer_unread.send(sender=post.privatetopic.__class__, instance=post, user=user)


class SinglePrivatePostObjectMixin(SingleObjectMixin):
    object = None

    def get_object(self, queryset=None):
        try:
            post_pk = int(self.request.GET.get('message'))
        except (KeyError, ValueError, TypeError):
            raise Http404
        return get_object_or_404(PrivatePost, pk=post_pk)
