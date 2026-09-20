from django.dispatch import Signal
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps
import logging
import os

logger = logging.getLogger(__name__)

# arguments: instance, user, by_email
ping = Signal()

# arguments: instance, user
unping = Signal()


def get_profile_model():
    return apps.get_model("member", "Profile")


@receiver(post_save)
def check_profile_spam(sender, instance, created, **kwargs):
    """
    Signal handler to detect spam profiles, triggered upon creation or update of biography.
    """
    if sender == get_profile_model():
        logger.info(f"Profile signal received for: {instance.user.username} (created={created})")

        if not instance.biography:
            logger.info(f"No bio for {instance.user.username} - skip")
            return

        if hasattr(instance, "_spam_checked") and instance._spam_checked:
            logger.info(f"Profile {instance.user.username} already checked - skip")
            return

        if not created:
            from .spam_detector import SpamDetector

            detector = SpamDetector()

            if instance.user.username in detector.reported_users:
                logger.info(f"Profile {instance.user.username} already checked - skip")
                return

        logger.info(f"Spam check started for {instance.user.username}")
        from .spam_detector import SpamDetector

        detector = SpamDetector()

        instance._spam_checked = True
        detector.check_profile(instance)
        logger.info(f"Spam check finished for {instance.user.username}")
