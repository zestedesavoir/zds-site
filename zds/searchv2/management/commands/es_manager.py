from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from zds.searchv2.models import SearchIndexManager, get_django_indexable_objects
from zds.tutorialv2.models.database import FakeChapter


class Command(BaseCommand):
    help = "Index data in ES and manage them"

    index_manager = None
    models = get_django_indexable_objects()

    def __init__(self, *args, **kwargs):
        """Overridden because FakeChapter needs to be present for schema.
        Also, its schema needs to be defined before the one of PublishedContent for parenting reasons (!!!).
        """

        super().__init__(*args, **kwargs)
        self.models.insert(0, FakeChapter)

        self.index_manager = SearchIndexManager()

        if not self.index_manager.connected_to_search:
            raise Exception("Unable to connect to Typesense, aborting.")

    def add_arguments(self, parser):
        parser.add_argument(
            "action", type=str, help="action to perform", choices=["setup", "clear", "index_all", "index_flagged"]
        )

    def handle(self, *args, **options):

        if options["action"] == "setup":
            self.setup_es()
        elif options["action"] == "clear":
            self.clear_es()
        elif options["action"] == "index_all":
            self.index_documents(force_reindexing=True)
        elif options["action"] == "index_flagged":
            self.index_documents(force_reindexing=False)
        else:
            raise CommandError("unknown action {}".format(options["action"]))

    def setup_es(self):

        self.index_manager.reset_index(self.models)
        # self.index_manager.setup_custom_analyzer()

    def clear_es(self):
        self.index_manager.clear_index()

        for model in self.models:
            self.index_manager.clear_indexing_of_model(model)

    def index_documents(self, force_reindexing=False):

        if force_reindexing:
            self.setup_es()  # remove all previous data

        for model in self.models:
            if model is FakeChapter:
                continue

            if force_reindexing:
                print(f"- indexing {model.get_document_type()}s")

            indexed_counter = self.index_manager.es_bulk_indexing_of_model(model, force_reindexing=force_reindexing)
            if force_reindexing:
                print(f"  {indexed_counter}\titems indexed")
