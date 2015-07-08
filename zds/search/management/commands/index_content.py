# coding: utf-8

from django.core.management import BaseCommand, CommandError
from django.db import transaction

from zds.search import reindex_content
from zds.tutorialv2.models.models_database import PublishedContent


@transaction.atomic
class Command(BaseCommand):
    help = 'Index content on demand'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('id', default=False, nargs='+', type=int)

    def handle(self, *args, **options):
        if options['id']:
            for id in options['id']:
                try:
                    content = PublishedContent.objects.exclude(sha_public__isnull=True) \
                                                      .exclude(sha_public__exact='').get(publishable_content=id)
                except content.DoesNotExist:
                    raise CommandError('Content "%s" does not exist' % content.id)

                reindex_content(content.load_public_version(), content)

                self.stdout.write('Successfully index content with id "%s"' % content.id)
        else:
            for content in PublishedContent.objects.exclude(sha_public__isnull=True)\
                                                   .exclude(sha_public__exact='').all():
                reindex_content(content.load_public_version(), content)
                self.stdout.write('Successfully index content with id "%s"' % content.id)

            self.stdout.write('Successfully indexed content')
