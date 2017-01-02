# coding: utf-8

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from zds.search2.models import ESIndexManager, get_django_indexable_objects
from zds.tutorialv2.models.models_database import FakeChapter


class Command(BaseCommand):
    help = 'Index data in ES and manage them'

    indexer = None
    models = get_django_indexable_objects()

    def __init__(self, *args, **kwargs):
        """Overridden because FakeChapter needs to be present for mapping.
        Also, its mapping needs to be defined before the one of PublishedContent for parenting reasons (!!!).
        """

        super(Command, self).__init__(*args, **kwargs)
        self.models.insert(0, FakeChapter)

        self.indexer = ESIndexManager(**settings.ES_SEARCH_INDEX)

    def add_arguments(self, parser):
        parser.add_argument(
            'action', type=str, help='action to perform', choices=['setup', 'clear', 'index-all', 'index-flagged'])

    def handle(self, *args, **options):

        if options['action'] == 'setup':
            self.setup_es()
        elif options['action'] == 'clear':
            self.clear_es()
        elif options['action'] == 'index-all':
            self.index_documents(force_reindexing=True)
        elif options['action'] == 'index-flagged':
            self.index_documents(force_reindexing=False)
        else:
            raise CommandError('unknown action {}'.format(options['action']))

    def setup_es(self):

        self.indexer.reset_es_index(self.models)
        self.indexer.setup_custom_analyzer()

    def clear_es(self):
        self.indexer.clear_es_index()

        for model in self.models:
            self.indexer.clear_indexing_of_model(model)

    def index_documents(self, force_reindexing=False):

        if force_reindexing:
            self.setup_es()  # remove all previous data

        for model in self.models:
            self.indexer.es_bulk_indexing_of_model(model, force_reindexing=force_reindexing)

        self.indexer.refresh_index()
