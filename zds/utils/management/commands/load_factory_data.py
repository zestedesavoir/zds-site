# coding: utf-8

import glob
import os
import yaml

from django.core.management.base import BaseCommand
from django.db import transaction
from zds.settings import MEDIA_ROOT


@transaction.atomic
class Command(BaseCommand):
    args = 'files'
    help = 'Load complex fixtures for ZdS'

    # python manage.py load_factory_data

    def handle(self, *args, **options):
        # create "media" folder if not existing
        if not os.path.exists(MEDIA_ROOT):
            os.mkdir(MEDIA_ROOT)

        for filename in glob.glob(' '.join(args)):
            stream = open(filename, 'r')
            fixture_list = yaml.load(stream)
            for fixture in fixture_list:
                splitted = str(fixture['factory']).split('.')
                module_part = '.'.join(splitted[:-1])
                module = __import__(module_part)
                for comp in splitted[1:-1]:
                    module = getattr(module, comp)

                obj = getattr(module, splitted[-1])(**fixture['fields'])
                print(obj)
