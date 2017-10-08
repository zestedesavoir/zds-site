# coding: utf-8

from social.apps.django_app.middleware import SocialAuthExceptionMiddleware
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
import logging

from zds.notification.models import TopicAnswerSubscription

logger = logging.getLogger(__name__)


class ZDSCustomizeSocialAuthExceptionMiddleware(SocialAuthExceptionMiddleware):
    """
    For more information, \
    see http://python-social-auth.readthedocs.io/en/latest/configuration/django.html#exceptions-middleware.
    """
    def get_message(self, request, exception):
        # this message aims to be displayed in our "error" widget
        message = _('Un problème a eu lieu lors de la communication avec le réseau social.')
        logger.warn('Social error %s', exception)
        messages.error(request, message)
        # this one is just for social auth compatibility (will be passed as get param)
        return 'Bad communication'

    def get_redirect_uri(self, *_, **__):
        return reverse('member-login')


def add_user_to_group(request, user, group):
    user.groups.add(group)
    messages.success(request, _('{0} appartient maintenant au groupe {1}.')
                     .format(user.username, group.name))


def remove_user_from_group(request, user, group):
    user.groups.remove(group)
    messages.warning(request, _('{0} n\'appartient maintenant plus au groupe {1}.')
                     .format(user.username, group.name))
    topics_followed = TopicAnswerSubscription.objects.get_objects_followed_by(user)
    for topic in topics_followed:
        if isinstance(topic, Topic) and group in topic.forum.groups.all():
            TopicAnswerSubscription.objects.toggle_follow(topic, user)


def remove_user_from_every_group(request, user, usergroups):
    for group in usergroups:
        topics_followed = TopicAnswerSubscription.objects.get_objects_followed_by(user)
        for topic in topics_followed:
            if isinstance(topic, Topic) and group in topic.forum.groups.all():
                TopicAnswerSubscription.objects.toggle_follow(topic, user)
    user.groups.clear()
    messages.warning(request, _('{0} n\'appartient (plus ?) à aucun groupe.')
                     .format(user.username))
