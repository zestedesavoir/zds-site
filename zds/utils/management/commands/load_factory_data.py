# coding: utf-8

import yaml
import zds
from django.core.management.base import BaseCommand
from django.db import transaction
import glob


@transaction.atomic
class Command(BaseCommand):
    args = 'files'
    help = 'Load complex fixtures for ZdS'
    can_import_settings = True

    # python manage.py load_factory_data

    def handle(self, *args, **options):
        for filename in glob.glob(" ".join(args)):
            stream = open(filename, 'r')
            fixture_list = yaml.load(stream)
            for fixture in fixture_list:
                splitted = str(fixture["factory"]).split(".")
                module_part = ".".join(splitted[:-1])
                m = __import__(module_part)
                for comp in splitted[1:-1]:
                    m = getattr(m, comp)

                obj = getattr(m, splitted[-1])(**fixture["fields"])
                print(obj)
