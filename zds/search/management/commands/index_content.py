# coding: utf-8
from optparse import make_option
import traceback

from django.core.management import BaseCommand
import sys
from zds.search.utils import reindex_content
from zds.tutorialv2.models.models_database import PublishedContent


class Command(BaseCommand):
    help = 'Copy content\'s informations into search tables database. It doesn\'t affect the search engine, ' \
           'you have to do a manage.py rebuild_index. \n ' \
           'You can choose to only copy content with certain id. Pass as argument the content id, you want to copy.' \
           'Example, manage.py index_content 1, will copy content id 1 information into database.' \
           ''

    option_list = BaseCommand.option_list + tuple([
        make_option('--only-flagged',
                    action='store_true',
                    dest='only-flagged',
                    default=False,
                    help='Only copy content informations that have been flagged by the system.')
    ])

    def handle(self, *args, **options):

        # Do the Query
        query_set = PublishedContent.objects.published()\
                                            .prefetch_related('content')\
                                            .prefetch_related('content__subcategory')\
                                            .prefetch_related('content__authors')\
                                            .prefetch_related('content__licence')\
                                            .prefetch_related('content__image')

        if args:
            query_set = query_set.filter(content__pk__in=args)

        if 'only-flagged' in options:
            if options['only-flagged']:
                query_set = query_set.filter(content__must_reindex=True)

        # Start to copy informations
        for content in query_set.all():

            try:

                self.stdout.write('Copying content information with id {0} into database ({1})'
                                  .format(content.content.id, content.content.title), ending='')

                reindex_content(content)

            # Voluntary broad exception, in any case, we must stop the process.
            except:
                self.stdout.write(' [FAIL]')
                print_error()
                continue

            self.stdout.write(' [OK]')


def print_error():
    exc_type, exc_value, exc_traceback = sys.exc_info()
    to_display = traceback.format_exception(exc_type, exc_value, exc_traceback)
    sys.stdout.write('\n'.join(to_display))
