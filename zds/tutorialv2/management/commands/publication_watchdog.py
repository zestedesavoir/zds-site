import logging
import time

from pathlib import Path

from django.core.management import BaseCommand
from concurrent.futures import Future, ProcessPoolExecutor

from zds.tutorialv2.models.database import PublicationEvent, STATE_CHOICES
from zds.tutorialv2.publication_utils import PublicatorRegistry


class Command(BaseCommand):
    help = 'Launch a watchdog that generate all exported formats (epub, pdf...) files without blocking request handling'

    def handle(self, *args, **options):
        logger = logging.getLogger(Command.__name__)
        with ProcessPoolExecutor(5) as executor:
            try:
                while True:
                    Command.launch_publicators(executor, logger)
                    time.sleep(10)
            except KeyboardInterrupt:
                executor.shutdown(wait=False)

    @staticmethod
    def get_callback_of(publication_event: PublicationEvent):
        def callback(future: Future):
            if future.done():
                publication_event.state_of_processing = 'SUCCESS'
            elif future.cancelled():
                publication_event.state_of_processing = 'FAILURE'
            publication_event.save()
        return callback

    @staticmethod
    def launch_publicators(executor, logger):
        for publication_event in PublicationEvent.objects.filter(state_of_processing=STATE_CHOICES[0][0]):
            logger.info('Export %s -- format=%s', publication_event.published_object.title(),
                        publication_event.format_requested)
            content = publication_event.published_object
            publicator = PublicatorRegistry.get(publication_event.format_requested)

            extra_content_dir = content.get_extra_contents_directory()
            building_extra_content_path = Path(str(Path(extra_content_dir).parent) + '__building',
                                               'extra_contents', content.content_public_slug)
            if not building_extra_content_path.exists():
                building_extra_content_path.mkdir(parents=True)
            base_name = str(Path(str(building_extra_content_path), content.content_public_slug))
            md_file_path = base_name + '.md'

            future = executor.submit(publicator.publish, md_file_path, base_name)
            publication_event.state_of_processing = STATE_CHOICES[1][0]
            publication_event.save()
            future.add_done_callback(Command.get_callback_of(publication_event))
