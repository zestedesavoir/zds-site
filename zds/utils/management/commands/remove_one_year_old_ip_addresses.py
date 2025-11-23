from datetime import datetime, timedelta

from django.core.management.base import BaseCommand

from zds.utils.models import Comment


class Command(BaseCommand):
    help = "Removes IP addresses that are more than one year old"

    def handle(self, *args, **options):
        one_year_ago = datetime.now() - timedelta(days=365)
        Comment.objects.filter(pubdate__lte=one_year_ago).exclude(ip_address="").update(ip_address="")
        self.stdout.write(self.style.SUCCESS(f"Successfully removed IP addresses that are more than one year old!"))
