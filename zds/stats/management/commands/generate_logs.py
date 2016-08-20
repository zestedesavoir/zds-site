# coding: utf-8

from django.core.management.base import BaseCommand, CommandError
import os
import re
from datetime import datetime
from user_agents import parse
import pygeoip
from django.conf import settings
from urlparse import urlparse
from hashlib import md5
from zds.tutorialv2.models.models_database import PublishedContent
from zds.stats.factories import LogRandomFactory

class Command(BaseCommand):
    args = '--path=<path_to_file> --lines=<number_of_log_lines>'
    help = 'Genrate access logs for test'

    def handle(self, *args, **options):
        if "path" not in options:
            raise CommandError(u"Veuillez préciser le chemin du fichier de la log avec l'option --path")
        if "lines" not in options:
            raise CommandError(u"Veuillez préciser le nombre de lignes du fichier de log avec l'option --lines")                        

        source = open(options["path"], "w")

        for x in range(0, int(options["lines"])):
            factory = LogRandomFactory()
            source.write("{}\n".format(factory))
        source.close()