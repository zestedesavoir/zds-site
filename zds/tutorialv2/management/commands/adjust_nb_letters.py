# coding: utf-8
import logging
from django.core.management.base import BaseCommand
from zds.tutorialv2.models.models_database import PublishedContent


class Command(BaseCommand):
    """
    `python manage.py adjust_nb_letters`; set the number of letter for every published content.
    """

    def handle(self, *args, **options):
        for content in PublishedContent.objects.filter(nb_letter=None):
            content.nb_letter = content.get_nb_letters()
            content.save()
            logging.info('content %s got %d letters', content.title(), content.nb_letter)
