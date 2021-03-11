from django.core.management.base import BaseCommand

from zds.tutorialv2.models.database import PublishedContent


class Command(BaseCommand):
    """
    `python manage.py adjust_char_count`; set the number of characters for every published content.

    """

    help = "Set the number of characters for every published content"

    def add_arguments(self, parser):
        parser.add_argument("--id", dest="id", type=str)

    def handle(self, *args, **options):
        opt = options.get("id")
        if opt:
            ids = list(set(opt.split(",")))
            query = PublishedContent.objects.filter(content_pk__in=ids, must_redirect=False)
        else:
            query = PublishedContent.objects.filter(must_redirect=False)

        for content in query:
            self.stdout.write(f"Processing « {content.title()} »...")
            content.char_count = content.get_char_count()
            content.save()
            self.stdout.write(f"  It got {content.char_count} letters.")
