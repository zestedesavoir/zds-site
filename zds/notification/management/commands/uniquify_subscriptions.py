from django.core.management import BaseCommand
from django.db.models import Count

from zds.notification.models import Subscription


class Command(BaseCommand):
    help = "Delete all but last duplicate subscriptions"

    def handle(self, *args, **options):
        self.stdout.write("Starting uniquifying subscriptions")
        count = 0
        # Find all duplicates
        duplicates = (
            Subscription.objects.values("user", "content_type", "object_id")
            .annotate(Count("id"))
            .filter(id__count__gt=1)
        )

        for sub in duplicates:
            del sub["id__count"]
            # Find PKs of duplicates, exclude the most recent one
            pks = Subscription.objects.filter(**sub).order_by("-pubdate").values_list("id", flat=True)[1:]
            count = count + len(pks)
            # Delete each of them
            for pk in pks:
                Subscription.objects.filter(pk=pk).delete()

        self.stdout.write(f"Deleted {count} duplicates")
