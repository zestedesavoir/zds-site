import logging
import time

from pathlib import Path

from django.core.management import BaseCommand

from zds.tutorialv2.models.database import PublicationEvent
from zds.tutorialv2.publication_utils import PublicatorRegistry, FailureDuringPublication

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Launch a watchdog that generate all exported formats (epub, pdf...) files without blocking request handling"

    def handle(self, *args, **options):
        # We mark running events as failure, in case this command failed while running
        running_events = PublicationEvent.objects.filter(state_of_processing="RUNNING")
        for publication_event in running_events.iterator():
            publication_event.state_of_processing = "FAILURE"
            publication_event.save()

        while True:
            requested_events = PublicationEvent.objects.filter(state_of_processing="REQUESTED")
            while requested_events.count() == 0:
                time.sleep(60)

            self.run()

    def run(self):
        requested_events = PublicationEvent.objects.select_related(
            "published_object", "published_object__content", "published_object__content__image"
        ).filter(state_of_processing="REQUESTED")

        for publication_event in requested_events.iterator():
            content = publication_event.published_object
            extra_content_dir = content.get_extra_contents_directory()
            building_extra_content_path = Path(
                str(Path(extra_content_dir).parent) + "__building", "extra_contents", content.content_public_slug
            )
            if not building_extra_content_path.exists():
                building_extra_content_path.mkdir(parents=True)
            base_name = str(building_extra_content_path)
            md_file_path = base_name + ".md"

            logger.info("Exporting « %s » as %s", content.title(), publication_event.format_requested)
            publication_event.state_of_processing = "RUNNING"
            publication_event.save()

            publicator = PublicatorRegistry.get(publication_event.format_requested)
            try:
                publicator.publish(md_file_path, base_name)
            except FailureDuringPublication:
                logger.error("Failed to export « %s » as %s", content.title(), publication_event.format_requested)
                publication_event.state_of_processing = "FAILURE"
            else:
                logger.info("Succeed to export « %s » as %s", content.title(), publication_event.format_requested)
                publication_event.state_of_processing = "SUCCESS"
            publication_event.save()
