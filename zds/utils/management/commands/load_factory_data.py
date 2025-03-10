import glob
import os

import yaml
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction


@transaction.atomic
class Command(BaseCommand):
    args = "files"
    help = "Load complex fixtures for ZdS"

    def add_arguments(self, parser):
        parser.add_argument("files", nargs="?", type=str)

    # python manage.py load_factory_data

    def handle(self, *args, **options):
        files = options.get("files")

        # create "media" folder if not existing
        if not os.path.exists(settings.MEDIA_ROOT):
            os.mkdir(settings.MEDIA_ROOT)

        for filename in glob.glob(files):
            stream = open(filename)
            fixture_list = yaml.load(stream, Loader=yaml.FullLoader)
            for fixture in fixture_list:
                splitted = str(fixture["factory"]).split(".")
                module_part = ".".join(splitted[:-1])
                module = __import__(module_part)
                for comp in splitted[1:-1]:
                    module = getattr(module, comp)

                obj = getattr(module, splitted[-1])(**fixture["fields"])
                print(obj)
