# coding: utf-8

from django.core.management.base import BaseCommand
from zds.tutorial.models import Tutorial
from django.conf import settings
import os


class Command(BaseCommand):
    args = 'id=1,2,3,4,5'
    help = 'Generate tutorials pdfs'
    # python manage.py pdf_generator id=3

    def handle(self, *args, **options):
        ids = []

        for arg in args:
            param = arg.split('=')
            if len(param) < 2:
                continue
            else:
                if param[0] in ['id', 'ids']:
                    ids = param[1].split(',')

        pandoc_debug_str = ''

        if len(ids) > 0:
            tutorials = Tutorial.objects.filter(pk__in=ids, sha_public__isnull=False).all()
            self.stdout.write("Génération de PDFs pour les tutoriels dont l'id est dans la liste : {}".format(ids))
        else:
            tutorials = Tutorial.objects.filter(sha_public__isnull=False).all()
            self.stdout.write('Génération de PDFs pour tous les tutoriels du site')

        for tutorial in tutorials:
            prod_path = tutorial.get_prod_path(tutorial.sha_public)
            os.system('cd ' + prod_path + ' && ' + settings.PANDOC_LOC + 'pandoc ' + settings.PANDOC_PDF_PARAM + ' ' +
                      os.path.join(prod_path, tutorial.slug) + '.md ' +
                      '-o ' + os.path.join(prod_path, tutorial.slug) +
                      '.pdf' + pandoc_debug_str)
            self.stdout.write('----> {}'.format(tutorial.title))
