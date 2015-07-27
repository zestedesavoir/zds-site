# coding: utf-8

from django.core.management import BaseCommand
from django.db import transaction
from zds.search.utils import reindex_content

from zds.tutorialv2.models.models_database import PublishedContent


@transaction.atomic
class Command(BaseCommand):
    help = 'Index content on demand'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('id', default=False, nargs='+', type=int)

    def handle(self, *args, **options):
        query_set = PublishedContent.objects.exclude(sha_public__isnull=True).exclude(sha_public__exact='')

        if 'id' in options:
            query_set = query_set.filter(publishable_content__pk__in=options['id'])

        for content in query_set.all():
            reindex_content(content.load_public_version(), content)
            self.stdout.write('Successfully index content with id "%s"' % content.id)
            self.stdout.write('Successfully indexed content')
