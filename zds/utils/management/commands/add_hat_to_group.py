# coding: utf-8

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group

from zds.utils.models import Hat


class Command(BaseCommand):
    help = 'Adds a hat to all members of a group.'

    def add_arguments(self, parser):
        parser.add_argument('group', type=str)
        parser.add_argument('hat', type=str)

    def handle(self, *args, **options):
        try:
            group = Group.objects.get(name=options['group'])
        except Group.DoesNotExist:
            raise CommandError('Group {} does not exist.'.format(options['group']))

        try:
            hat = Hat.objects.get(name__iexact=options['hat'])
        except Hat.DoesNotExist:
            hat = Hat(name=options['hat'])
            hat.save()

        for user in group.user_set.all():
            user.profile.hats.add(hat)
            self.stdout.write(self.style.SUCCESS('{0} was added to {1}.'.format(hat.name, user.username)))
