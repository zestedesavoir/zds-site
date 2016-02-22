# coding: utf-8
import os
from uuslug import slugify

from django.core.management.base import BaseCommand
from zds.settings import ZDS_APP
from zds.tutorialv2.models.models_database import PublishableContent


class Command(BaseCommand):
    """
    `python manage.py adjust_slugs`; fix content's slugs for which the title contains single quote(s).
    """

    def handle(self, *args, **options):

        for c in PublishableContent.objects.all():
            if '\'' in c.title:
                good_slug = slugify(c.title)
                if c.slug != good_slug:
                    if os.path.isdir(os.path.join(ZDS_APP['content']['repo_private_path'], good_slug)):
                        self.stdout.write(u'Fixing content #{} (« {} ») ... '.format(c.pk, c.title), ending='')
                        c.save()
                        if os.path.isdir(c.get_repo_path()):
                            self.stdout.write(u'[OK]')
                        else:
                            self.stdout.write(u'[KO]')
                    else:
                        self.stderr.write(
                            u'Content #{} (« {} ») cannot be fixed: there is no directory named "{}" in "{}".\n'.
                            format(c.pk, c.title, good_slug, ZDS_APP['content']['repo_private_path']))
