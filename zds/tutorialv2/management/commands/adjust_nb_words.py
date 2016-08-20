# coding: utf-8
import logging

from os.path import join

from django.core.management.base import BaseCommand

from zds.tutorialv2.models.models_database import PublishedContent
from zds.tutorialv2.publication_utils import NumberOfWordPublicator


class Command(BaseCommand):
    """
    `python manage.py adjust_slugs`; fix content's slugs for which the title contains single quote(s).
    """

    def handle(self, *args, **options):
        publicator = NumberOfWordPublicator()
        for content in PublishedContent.objects.filter(must_redirect=True, nb_word=None):
            publicator.publish(join(content.get_extra_contents_directory(), content.content_public_slug + '.md'),
                               content.content_public_slug)
            logging.info("content %s got %d words", content.title(), content.nb_word)
