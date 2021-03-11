from django.contrib.contenttypes.models import ContentType
from django.core.management import BaseCommand

from zds.member.models import Profile
from zds.notification.models import Notification


class Command(BaseCommand):
    help = "Remove useless notifications for private topics."

    def handle(self, *args, **options):
        for profile in Profile.objects.all():
            self.stdout.write(f"Remove all useless notifications of {profile.user.username}...")
            content_type = ContentType.objects.get(model="privatepost")
            for notification in Notification.objects.filter(
                is_read=False, content_type=content_type, subscription__user=profile.user
            ):
                if notification.content_object is None:
                    notification.is_read = True
                    notification.save()
                    self.stdout.write(f"Notification #{notification.id} marked as read.")
