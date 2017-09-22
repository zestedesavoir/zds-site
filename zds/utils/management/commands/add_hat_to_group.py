# coding: utf-8

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group

from zds.utils.misc import contains_utf8mb4
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

        hat_name = options.get('hat', '').strip()
        if not hat_name:
            raise CommandError('Hat required!')
        if contains_utf8mb4(hat_name):
            raise CommandError('utf8mb4 characters are not allowed.')
        elif len(hat_name) > 40:
            raise CommandError('Hat length is limited to 40 characters.')

        hat, created = Hat.objects.get_or_create(name__iexact=hat_name, defaults={'name': hat_name})
        if created:
            self.stdout.write(self.style.SUCCESS('Hat "{}" created.'.format(hat_name)))

        for user in group.user_set.all():
            user.profile.hats.add(hat)
            self.stdout.write(self.style.SUCCESS('"{0}" was added to {1}.'.format(hat.name, user.username)))
