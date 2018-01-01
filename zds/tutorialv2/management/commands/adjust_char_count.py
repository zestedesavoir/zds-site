import logging
from django.core.management.base import BaseCommand
from zds.tutorialv2.models.database import PublishedContent


class Command(BaseCommand):
    """
    `python manage.py adjust_char_count`; set the number of characters for every published content.
    """

    def handle(self, *args, **options):
        for content in PublishedContent.objects.filter(char_count=None, must_redirect=False):
            content.char_count = content.get_char_count()
            content.save()
            logging.info('content %s got %d letters', content.title(), content.char_count)
