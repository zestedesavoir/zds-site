from django.contrib.contenttypes.models import ContentType
from django.core.management import BaseCommand

from zds.forum.models import Topic
from zds.notification.models import Notification


class Command(BaseCommand):
    help = "Fix all persistent notifications."

    def handle(self, *args, **options):
        content_type = ContentType.objects.get_for_model(Topic)
        notifications = Notification.objects.filter(content_type=content_type, is_read=False).all()
        count = 0
        print("")
        for notification in notifications:
            if notification.subscription.content_object != notification.content_object.forum:
                notification.is_read = True
                notification.is_dead = True
                notification.save()
                print(notification)
                count += 1
        print(f"{count} notifications have been fixed")
