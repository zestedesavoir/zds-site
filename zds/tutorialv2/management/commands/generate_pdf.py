# coding: utf-8

import os
import subprocess
from django.core.management.base import BaseCommand
from django.utils.translation import ugettext_lazy as _
from zds import settings
from zds.tutorialv2.models.models_database import PublishedContent


class Command(BaseCommand):
    args = '[id=1,2,3,4,5]'
    help = 'Generate pdfs of published contents'
    # python manage.py generate_pdf id=3

    def add_arguments(self, parser):
        parser.add_argument('id', nargs='*', type=str)

    def handle(self, *args, **options):
        try:
            ids = list(set(options.get('id')[0].replace('id=', '').split(',')))
        except IndexError:
            ids = []

        pandoc_debug_str = ''
        if settings.PANDOC_LOG_STATE:
            pandoc_debug_str = ' 2>&1 | tee -a ' + settings.PANDOC_LOG

        if len(ids) > 0:
            public_contents = PublishedContent.objects.filter(content_pk__in=ids, must_redirect=False).all()
        else:
            public_contents = PublishedContent.objects.filter(must_redirect=False).all()

        num_of_contents = len(public_contents)

        if num_of_contents == 0:
            self.stdout.write(_(u"Aucun contenu n'a été sélectionné, aucun PDF ne sera généré"))
            return

        self.stdout.write(_(u'Génération de PDF pour {} contenu{}').format(
            num_of_contents, 's' if num_of_contents > 1 else ''))

        for content in public_contents:
            self.stdout.write(_(u'- {}').format(content.content_public_slug), ending='')
            extra_content_dir = content.get_extra_contents_directory()

            base_name = os.path.join(extra_content_dir, content.content_public_slug)

            # delete previous one
            if os.path.exists(base_name + '.pdf'):
                os.remove(base_name + '.pdf')

            # generate PDF (assume images)
            subprocess.call(
                settings.PANDOC_LOC + 'pandoc ' + settings.PANDOC_PDF_PARAM + ' ' +
                base_name + '.md -o ' + base_name + '.pdf' + pandoc_debug_str,
                shell=True,
                cwd=extra_content_dir)

            # check:
            if os.path.exists(base_name + '.pdf'):
                self.stdout.write(' [OK]')
            else:
                self.stdout.write(' [ERREUR]')

        os.chdir(settings.BASE_DIR)
