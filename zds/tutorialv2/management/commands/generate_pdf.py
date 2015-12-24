# coding: utf-8

import os
from django.core.management.base import BaseCommand
from django.utils.translation import ugettext_lazy as _
from zds import settings
from zds.tutorialv2.models.models_database import PublishedContent
from zds.tutorialv2.utils import build_pdf_of_published


class Command(BaseCommand):
    args = '[id=1,2,3,4,5]'
    help = 'Generate pdfs of published contents'
    # python manage.py generate_pdf id=3

    def handle(self, *args, **options):
        ids = []

        for arg in args:
            param = arg.split("=")
            if len(param) < 2:
                continue
            elif len(param) > 1:
                if param[0] in ["id", "ids"]:
                    ids = param[1].split(",")

        if len(ids) > 0:
            public_contents = PublishedContent.objects.filter(content_pk__in=ids, must_redirect=False).all()
        else:
            public_contents = PublishedContent.objects.filter(must_redirect=False).all()

        num_of_contents = len(public_contents)

        if num_of_contents == 0:
            self.stdout.write(_(u'Aucun contenu n\'a été sélectionné, aucun PDF ne sera généré'))
            return

        self.stdout.write(_(u'Génération de PDF pour {} contenu{}').format(
            num_of_contents, 's' if num_of_contents > 1 else ''))

        for content in public_contents:
            self.stdout.write(_(u"- {}").format(content.content_public_slug), ending='')
            build_pdf_of_published(content)

            # check:
            if content.have_type('pdf'):
                self.stdout.write(_(u' [OK]'))
            else:
                self.stdout.write(_(u' [ERREUR]'))

        os.chdir(settings.BASE_DIR)
