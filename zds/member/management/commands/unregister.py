from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from zds.member.utils import unregister


class Command(BaseCommand):
    help = "Unregister a member"

    def boolean_input(self, question, default=None):
        # From django/db/migrations/questioner.py
        self.stdout.write(f"{question} ", ending="")
        result = input()
        if not result and default is not None:
            return default
        while not result or result[0].lower() not in "yn":
            self.stdout.write("Please answer yes or no: ", ending="")
            result = input()
        return result[0].lower() == "y"

    def add_arguments(self, parser):
        # Don't use email because on production we have several accounts with the
        # same email...
        parser.add_argument("username", type=str)
        parser.add_argument("-f", "--force", action="store_true", default=False)

    def handle(self, *args, **options):
        username = options.get("username")
        force = options.get("force")

        nb_matching = User.objects.filter(username=username).count()

        if nb_matching == 0:
            self.stderr.write(self.style.ERROR(f"Unknown user '{username}'"))
            return
        elif nb_matching > 1:
            self.stderr.write(self.style.ERROR(f"{nb_matching} users have '{username}' as username"))
            return

        user = User.objects.filter(username=username).first()

        self.stdout.write("Found the following user:")
        self.stdout.write(f"Username: {user.username}")
        self.stdout.write(f"Email: {user.email}")
        self.stdout.write(f"First login: {user.date_joined}")
        self.stdout.write(f"Last login: {user.profile.last_visit}")
        self.stdout.write(f"Is active: {user.is_active}")
        self.stdout.write("")

        if force or self.boolean_input(f"Are you sure you want to unregister user '{username}'? [y/N]", False):
            unregister(user)
            self.stdout.write(self.style.SUCCESS(f"Unregistered user '{username}'"))
        else:
            self.stdout.write("Aborting.")
