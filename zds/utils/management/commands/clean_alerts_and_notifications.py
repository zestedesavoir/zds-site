import datetime
import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import BaseCommand
from django.db import transaction
from django.utils.translation import gettext as _

from zds.utils.models import Alert


@transaction.atomic
class Command(BaseCommand):
    help = "Clean up useless notifications & alerts."

    def add_arguments(self, parser):
        parser.add_argument(
            "--moderator", type=str, dest="moderator_name", default=settings.ZDS_APP["member"]["anonymous_account"]
        )

    def handle(self, *args, **options):
        moderator = User.objects.filter(username=options["moderator_name"]).first()
        if not moderator:
            logging.error("Could not use this moderator %s", options["moderator_name"])
            return 1
        Alert.objects.first(content__isnull=False, content__public_version__isnull=True).update(
            moderator=moderator,
            solved=True,
            solved_date=datetime.datetime.now(),
            resolve_reason=_("Résolution automatique."),
        )
        Alert.objects.filter(
            scope="CONTENT",
            comment__related_content__isnull=False,
            comment__related_content__public_version__isnull=True,
        ).update(
            moderator=moderator,
            solved=True,
            solved_date=datetime.datetime.now(),
            resolve_reason=_("Résolution automatique."),
        )
