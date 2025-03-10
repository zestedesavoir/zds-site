import contextlib
from pathlib import Path

from django.core.management import BaseCommand
from django.utils import translation
from django.utils.translation import gettext_lazy as _

from zds.tutorialv2.models.database import PublishedContent
from zds.tutorialv2.models.versioned import NotAPublicVersion
from zds.tutorialv2.publication_utils import FailureDuringPublication, PublicatorRegistry


class Command(BaseCommand):
    args = "[id=1,2,3,4,5]"
    help = "Generate markdown of published contents"
    # python manage.py generate_markdown id=3

    def add_arguments(self, parser):
        parser.add_argument("id", nargs="*", type=str)

    def handle(self, *__, **options):
        try:
            ids = list(set(options.get("id")[0].replace("id=", "").split(",")))
        except IndexError:
            ids = []

        if len(ids) > 0:
            public_contents = PublishedContent.objects.filter(content_pk__in=ids, must_redirect=False).all()
        else:
            public_contents = PublishedContent.objects.filter(must_redirect=False).all()

        num_of_contents = len(public_contents)

        if num_of_contents == 0:
            self.stdout.write(_("Aucun contenu n'a été sélectionné, aucun markdown ne sera généré"))
            return

        self.stdout.write(
            _("Génération de epub pour {} contenu {}").format(num_of_contents, "s" if num_of_contents > 1 else "")
        )

        for content in public_contents:
            with contextlib.suppress(NotAPublicVersion, FailureDuringPublication):
                self.stdout.write(_("- {}").format(content.content_public_slug), ending="")
                extra_content_dir = content.get_extra_contents_directory()
                building_extra_content_path = Path(
                    str(Path(extra_content_dir).parent) + "__building", "extra_contents", content.content_public_slug
                )
                if not building_extra_content_path.exists():
                    building_extra_content_path.mkdir(parents=True)
                base_name = str(Path(str(extra_content_dir), content.content_public_slug))

                PublicatorRegistry.get("md").publish(
                    base_name + ".md",
                    str(building_extra_content_path),
                    cur_language=translation.get_language(),
                    versioned=content.content.load_version(public=True),
                )

            # check:
            if Path(base_name + ".md").exists():
                self.stdout.write(" [OK]")
            else:
                self.stdout.write(" [ERREUR]")
