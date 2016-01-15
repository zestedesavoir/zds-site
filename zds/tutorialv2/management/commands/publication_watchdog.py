from os.path import dirname, join
import os
import time

import shutil
from django.core.management import BaseCommand
from pathtools.path import listdir
from watchdog.observers import Observer
from watchdog.events import FileCreatedEvent, FileSystemEventHandler, LoggingEventHandler
from zds import settings
from zds.tutorialv2.publication_utils import generate_exernal_content
from codecs import open


class TutorialIsPublished(FileSystemEventHandler):
    def on_created(self, event):
        super(TutorialIsPublished, self).on_created(event)
        pandoc_debug_str = ""

        if settings.PANDOC_LOG_STATE:
            pandoc_debug_str = " 2>&1 | tee -a " + settings.PANDOC_LOG
        if isinstance(event, FileCreatedEvent):
            with open(event.src_path, encoding="utf-8") as f:
                infos = f.read().strip().split(";")
            md_file_path = infos[1]
            base_name = infos[0]
            extra_contents_path = dirname(md_file_path)
            if not os.path.exists(extra_contents_path):
                os.makedirs(extra_contents_path)
            generate_exernal_content(base_name, extra_contents_path, md_file_path,
                                     pandoc_debug_str, overload_settings=True)
            for listed in listdir(extra_contents_path, recursive=False):
                try:
                    shutil.copy(join(extra_contents_path, listed), extra_contents_path.replace("__building", ""))
                except Exception:
                    pass
            shutil.rmtree(extra_contents_path)
            os.remove(event.src_path)


class Command(BaseCommand):
    help = 'Launch a watchdog that generate all exported formats (epub, pdf...) files without blocking request handling'

    def handle(self, *args, **options):
        path = settings.ZDS_APP['content']['extra_content_watchdog_dir']
        event_handler = TutorialIsPublished()
        observer = Observer()
        observer.schedule(event_handler, path, recursive=True)
        observer.schedule(LoggingEventHandler(), path)
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
