import logging

from django.core.management import BaseCommand
from django.utils.translation import gettext as _

from zds.tutorialv2.models.database import PublishableContent, Validation
from zds.tutorialv2.publication_utils import (
    FailureDuringPublication,
    notify_update,
    publish_content,
    save_validation_state,
)


class Command(BaseCommand):
    help = "Publish one content by its id. This require the content to be in validation and reserved by someone"

    def add_arguments(self, parser):
        parser.add_argument("content", type=Command.id_validator)
        parser.add_argument("--major", dest="is_major", action="store_true")
        parser.add_argument("--source", dest="source", type=str, default="")

    @staticmethod
    def id_validator(content_pk):
        try:
            content_pk = int(content_pk)
        except ValueError:
            raise ValueError("Identifier should be integer")
        content = PublishableContent.objects.filter(pk=content_pk).first()
        if not content:
            raise ValueError("Content does not exist")

        if not Validation.objects.filter(content=content, status="PENDING_V").first():
            raise ValueError("Content is not being validated")

        return content

    def handle(self, *args, content: PublishableContent, is_major=False, **options):
        content.current_validation = Validation.objects.filter(content=content, status="PENDING_V").first()
        versioned = content.load_version(sha=content.current_validation.version)
        is_update = content.sha_public
        try:
            published = publish_content(content, versioned, is_major_update=is_major)
        except FailureDuringPublication as e:
            self.stdout.write("Publication failed")
            logging.getLogger(__name__).exception("Failure during publication", exc_info=e)
        else:
            save_validation_state(
                content,
                is_update,
                published,
                content.current_validation,
                versioned,
                options.get("source", ""),
                is_major,
                user=content.current_validation.validator,
                comment=_("Géré depuis la commande d'administration"),
            )
            notify_update(content, is_update, is_major)
            self.stdout.write(_("La contenu a été validé"))
