# coding: utf-8

from django.core.management.base import BaseCommand, CommandError

from zds.search2 import INDEX_NAME, setup_es_connections
from zds.search2.models import ESIndexManager, get_django_indexable_objects


class Command(BaseCommand):
    help = 'Manage data from/to ES'

    indexer = None
    models = get_django_indexable_objects()

    def add_arguments(self, parser):
        parser.add_argument('action', type=str)

    def handle(self, *args, **options):
        setup_es_connections()
        self.indexer = ESIndexManager(INDEX_NAME)

        if options['action'] == 'setup':
            self.setup_es()
        elif options['action'] == 'index-all':
            self.index_documents(force_reindexing=True)
        elif options['action'] == 'index-flagged':
            self.index_documents(force_reindexing=False)
        else:
            raise CommandError('unknown action {}'.format(options['action']))

    def setup_es(self):
        self.indexer.reset_es_index()
        self.indexer.setup_es_mappings(self.models)

    def index_documents(self, force_reindexing=False):

        if force_reindexing:
            self.setup_es()  # remove all previous data

        for model in self.models:
            self.indexer.es_bulk_action_on_model(model, force_reindexing=force_reindexing)
