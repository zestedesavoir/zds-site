# coding: utf-8
from optparse import make_option
import os
import shutil

from django.core.management import BaseCommand
from git import Git
import sys
from zds import settings
from zds.search.utils import reindex_content
from zds.tutorialv2.models.models_database import PublishedContent


class Command(BaseCommand):
    help = 'Copy content\'s informations into search tables database. It doesn\'t affect the search engine, ' \
           'you have to do a manage.py rebuild_index. \n ' \
           'You can choose to only copy content with certain id. Pass as argument the content id, you want to copy.' \
           'Example, manage.py index_content 1, will copy content id 1 information into database.' \
           ''

    option_list = BaseCommand.option_list + (
        make_option('--copy-repository',
                    action='store_true',
                    dest='copy-repository',
                    default=False,
                    help='Create the markdown folder in the public repository on the fly'),

        make_option('--only-flagged',
                    action='store_true',
                    dest='only-flagged',
                    default=False,
                    help='Only copy content informations that have been flagged by the system.')
    )

    def handle(self, *args, **options):

        # Alert user that we shouldn't use the website during the copy of the markdown operation
        if 'copy-repository' in options:
            if options['copy-repository']:
                self.stdout.write("This argument should not be used when the website is running. "
                                  "Please, be sure that the website isn't running and no process can access the "
                                  "contents-private repository. Is the website running ? y/N")
                user_confirmation = raw_input()

                if user_confirmation == 'y' or user_confirmation == 'yes':
                    self.stdout.write("Please delete this option or kill every process that use the contents-private "
                                      "repository.")
                    sys.exit(0)

        # Do the Query
        query_set = PublishedContent.objects.exclude(sha_public__isnull=True) \
                                            .exclude(sha_public__exact='') \
                                            .exclude(must_redirect=True)

        if args:
            query_set = query_set.filter(content__pk__in=args)

        if 'only-flagged' in options:
            if options['only-flagged']:
                query_set = query_set.filter(content__must_reindex=True)

        # Start to copy informations
        for content in query_set.all():

            # Check first if there is markdown folder in extra_contents
            path = os.path.join(settings.ZDS_APP['content']['repo_public_path'], content.content.slug,
                                'extra_contents', content.content.slug)

            if 'copy-repository' in options and not os.path.isdir(path):

                # Checkout the right commit
                repo = Git(content.content.get_repo_path())
                repo.checkout(content.content.sha_public)

                # Copy the markdown folder
                shutil.copytree(content.content.get_repo_path(), path)

                # Checkout the draft version
                repo.checkout(content.content.sha_draft)

            reindex_content(content.load_public_version(), content.content)

            self.stdout.write('Successfully copy content information with id %s into database' % content.content.id)
