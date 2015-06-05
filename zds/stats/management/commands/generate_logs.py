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
from zds.tutorialv2.models import PublishedContent
from zds.stats.factories import LogRandomFactory

class Command(BaseCommand):
    args = 'path=<path_to_file> lines=<number_of_log_lines>'
    help = 'Genrate access logs'

    def handle(self, *args, **options):
        if len(args) < 1:
            raise CommandError(u"Cette commande nécessite deux paramètres")
        else:
            for arg in args:
                v = arg.split("=")
                if len(v) < 2:
                    raise CommandError(u"Cette commande nécessite deux paramètres (lines et path)")
                elif v[0] == "path":
                    path_generate = v[1]
                elif v[0] == "lines":
                    try:
                        nb_lines = int(v[1])
                    except ValueError:
                        raise CommandError(u"Veuillez préciser un nombre de lignes pour le paramètre lines")
                        

        source = open(path_generate, "w")

        for x in range(0, nb_lines):
            factory = LogRandomFactory()
            source.write("{}\n".format(factory))
        source.close()