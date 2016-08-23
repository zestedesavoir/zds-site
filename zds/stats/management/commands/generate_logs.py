# coding: utf-8

from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from zds.stats.factories import LogRandomFactory


class Command(BaseCommand):
    args = '--path=<path_to_file> --lines=<number_of_log_lines>'
    help = 'Genrate access logs for test'
    option_list = BaseCommand.option_list + (
        make_option('--path',
                    default='test-log.log',
                    help='Log path to generate'),
    ) + (
        make_option('--lines',
                    default=100,
                    help='Lines number to generate'),
    )

    def handle(self, *args, **options):
        if 'path' not in options:
            raise CommandError(u'Veuillez préciser le chemin du fichier de la log avec l\'option --path')
        if 'lines' not in options:
            raise CommandError(u'Veuillez préciser le nombre de lignes du fichier de log avec l\'option --lines')

        source = open(options['path'], 'w')

        for x in range(0, int(options['lines'])):
            factory = LogRandomFactory()
            source.write('{}\n'.format(factory))
        source.close()
