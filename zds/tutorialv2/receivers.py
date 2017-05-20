# coding: utf-8
from __future__ import unicode_literals

import datetime
from django.dispatch.dispatcher import receiver
from django.utils.translation import ugettext_lazy as _
from zds.tutorialv2.models.models_database import PublishableContent
from zds.tutorialv2.signals import content_unpublished
from zds.utils import get_current_user
from zds.utils.models import Alert


@receiver(content_unpublished, sender=PublishableContent)
def cleanup_validation_alerts(sender, instance, **kwargs):
    """
    When opinions are unpublished (probably permanently), we must be sure all alerts are handled. For now we just \
    resolve them.

    :param sender: sender class
    :param instance: object instance
    :param kwargs: possibily moderator
    """
    if instance.is_opinion:
        moderator = kwargs.get('moderator', get_current_user())
        Alert.objects.filter(scope='CONTENT', content=instance).update(moderator=moderator,
                                                                       resolve_reason=_('Le billet a été dépublié.'),
                                                                       solved_date=datetime.datetime.now(),
                                                                       solved=True)
