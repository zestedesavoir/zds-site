from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from zds.searchv2.models import SearchIndexManager, get_all_indexable_objects
from zds.tutorialv2.models.database import FakeChapter


class Command(BaseCommand):
    help = "Index data in Typesense and manage them"

    search_engine_manager = None
    models = get_all_indexable_objects()

    def __init__(self, *args, **kwargs):
        """Overridden because FakeChapter needs to be present for schema.
        Also, its schema needs to be defined before the one of PublishedContent for parenting reasons (!!!).
        """

        super().__init__(*args, **kwargs)
        self.models.insert(0, FakeChapter)

        self.search_engine_manager = SearchIndexManager()

        if not self.search_engine_manager.connected_to_search_engine:
            raise Exception("Unable to connect to the search engine, aborting.")

    def add_arguments(self, parser):
        parser.add_argument(
            "action", type=str, help="action to perform", choices=["setup", "clear", "index_all", "index_flagged"]
        )
        parser.add_argument("-q", "--quiet", action="store_true", default=False)

    def handle(self, *args, **options):
        if options["action"] == "setup":
            self.setup_search_engine()
        elif options["action"] == "clear":
            self.clear_search_engine()
        elif options["action"] == "index_all":
            self.index_documents(force_reindexing=True, quiet=options["quiet"])
        elif options["action"] == "index_flagged":
            self.index_documents(force_reindexing=False, quiet=options["quiet"])
        else:
            raise CommandError("unknown action {}".format(options["action"]))

    def setup_search_engine(self):
        self.search_engine_manager.reset_index(self.models)

    def clear_search_engine(self):
        self.search_engine_manager.clear_index()

        for model in self.models:
            self.search_engine_manager.clear_indexing_of_model(model)

    def index_documents(self, force_reindexing=False, quiet=False):
        if force_reindexing:
            self.setup_search_engine()  # remove all previous data

        for model in self.models:
            if model is FakeChapter:
                continue

            if force_reindexing:
                self.stdout.write(f"- indexing {model.get_document_type()}s")

            indexed_counter = self.search_engine_manager.indexing_of_model(
                model, force_reindexing=force_reindexing, verbose=not quiet
            )
            if force_reindexing:
                self.stdout.write(f"  {indexed_counter}\titems indexed")
