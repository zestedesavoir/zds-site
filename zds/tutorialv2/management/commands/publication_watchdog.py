import logging
import time
from pathlib import Path

from django.core.management import BaseCommand

from zds.tutorialv2.models.database import PublicationEvent
from zds.tutorialv2.publication_utils import PublicatorRegistry

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Launch a watchdog that generate all exported formats (epub, pdf...) files without blocking request handling'

    def handle(self, *args, **options):
        while True:
            Command.launch_publicators()
            time.sleep(10)

    @staticmethod
    def launch_publicators():
        query_set = PublicationEvent.objects.select_related('published_object', 'published_object__content',
                                                            'published_object__content__image') \
                                            .filter(state_of_processing='REQUESTED')

        for publication_event in query_set.iterator():
            logger.info('Export %s -- format=%s', publication_event.published_object.title(),
                        publication_event.format_requested)
            content = publication_event.published_object
            publicator = PublicatorRegistry.get(publication_event.format_requested)

            extra_content_dir = content.get_extra_contents_directory()
            building_extra_content_path = Path(str(Path(extra_content_dir).parent) + '__building',
                                               'extra_contents', content.content_public_slug)
            if not building_extra_content_path.exists():
                building_extra_content_path.mkdir(parents=True)
            base_name = str(building_extra_content_path)
            md_file_path = base_name + '.md'

            publication_event.state_of_processing = 'RUNNING'
            publication_event.save()
            try:
                publicator.publish(md_file_path, base_name)
                publication_event.state_of_processing = 'SUCCESS'
            except Exception as e:
                publication_event.state_of_processing = 'FAILURE'
                logger.error('error while producing %s of %s', publication_event.format_requested,
                             publication_event.published_object.title(), exc_info=e)
            publication_event.save()
