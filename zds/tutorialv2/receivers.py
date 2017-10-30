# coding: utf-8


import datetime
import logging

from django.dispatch.dispatcher import receiver
from django.utils.translation import ugettext_lazy as _
from django.db import models

from zds.tutorialv2.models.database import PublishableContent
from zds.tutorialv2.signals import content_unpublished
from zds.gallery.models import Gallery
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


@receiver(models.signals.post_delete, sender=Gallery)
@receiver(models.signals.post_delete, sender=PublishableContent)
def log_content_deletion(sender, instance, **kwargs):
    """
    When a content or gallery is deleted, this action is logged.
    """

    logger = logging.getLogger(__name__)
    current_user = get_current_user()

    if current_user is None:
        logger.info('%(instance_model)s #%(instance_pk)d (%(instance_slug)s) has been deleted. User not found.',
                    {'instance_model': type(instance).__name__, 'instance_pk': instance.pk,
                     'instance_slug': instance.slug})
    else:
        logger.info('%(instance_model)s #%(instance_pk)d (%(instance_slug)s) has been deleted '
                    'by user #%(user_pk)d (%(username)s).', {'instance_model': type(instance).__name__,
                                                             'instance_pk': instance.pk, 'instance_slug': instance.slug,
                                                             'user_pk': current_user.pk,
                                                             'username': current_user.username})
