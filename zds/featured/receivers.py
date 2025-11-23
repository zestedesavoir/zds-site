from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from zds.featured.models import FeaturedRequested
from zds.forum.models import Topic
from zds.tutorialv2.models.database import PublishableContent, PublishedContent


@receiver(pre_delete, sender=PublishableContent)
@receiver(pre_delete, sender=PublishedContent)
@receiver(pre_delete, sender=Topic)
def remove_requested_featured_at_content_object_deletion(sender, instance, **kwargs):
    if isinstance(instance, PublishedContent):
        sender = PublishableContent
        instance = instance.content
    try:
        FeaturedRequested.objects.get(
            content_type=ContentType.objects.get_for_model(sender), object_id=instance.pk
        ).delete()
    except FeaturedRequested.DoesNotExist:
        pass
