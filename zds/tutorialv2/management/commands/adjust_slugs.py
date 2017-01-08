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
            if "'" in c.title:
                good_slug = slugify(c.title)
                if c.slug != good_slug:
                    if os.path.isdir(os.path.join(ZDS_APP['content']['repo_private_path'], good_slug)):
                        # this content was created before v16 and is probably broken
                        self.stdout.write(u'Fixing pre-v16 content #{} (« {} ») ... '.format(c.pk, c.title), ending='')
                        c.save()
                        if os.path.isdir(c.get_repo_path()):
                            self.stdout.write(u'[OK]')
                        else:
                            self.stdout.write(u'[KO]')
                    elif os.path.isdir(os.path.join(ZDS_APP['content']['repo_private_path'], c.slug)):
                        # this content was created during v16 and will be broken if nothing is done
                        self.stdout.write(u'Fixing in-v16 content #{} (« {} ») ... '.format(c.pk, c.title), ending='')
                        try:
                            versioned = c.load_version()
                        except IOError:
                            self.stdout.write(u'[KO]')
                        else:
                            c.sha_draft = versioned.repo_update_top_container(
                                c.title,
                                good_slug,
                                versioned.get_introduction(),
                                versioned.get_conclusion(),
                                commit_message='[hotfix] Corrige le slug')

                            c.save()

                            if os.path.isdir(c.get_repo_path()):
                                self.stdout.write(u'[OK]')
                            else:
                                self.stdout.write(u'[KO]')
                    else:
                        self.stderr.write(
                            u'Content #{} (« {} ») is an orphan: there is no directory named "{}" or "{}".\n'.
                            format(c.pk, c.title, good_slug, c.slug))
