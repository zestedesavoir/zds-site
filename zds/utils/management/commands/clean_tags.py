from django.core.management import BaseCommand

from zds.forum.models import Topic
from zds.tutorialv2.models.database import PublishableContent
from zds.utils.models import Tag


class Command(BaseCommand):
    help = "Strip tags, uniquify them, modify every reference to deleted tags"

    def handle(self, *args, **options):
        def title_pk(tag):
            if isinstance(tag, dict):
                return '"{}" ({})'.format(tag["title"], tag["pk"])
            return f'"{tag.title}" ({tag.pk})'

        def replace(tag_to_delete, tag_to_use_instead):
            self.stdout.write(f"Replacing {title_pk(tag_to_delete)} with {title_pk(tag_to_use_instead)}")

            topics = Topic.objects.filter(tags__pk=tag_to_delete["pk"])
            for topic in topics:
                self.stdout.write(f'    Replaced on topic "{topic}"')
                topic.tags.add(tag_to_use_instead.pk)
                topic.tags.remove(tag_to_delete["pk"])

            contents = PublishableContent.objects.filter(tags__pk=tag_to_delete["pk"])
            for content in contents:
                self.stdout.write(f'    Replaced on content "{content}"')
                content.tags.add(tag_to_use_instead.pk)
                content.tags.remove(tag_to_delete["pk"])

            self.stdout.write(f"    Deleting {title_pk(tag_to_delete)}")
            Tag.objects.get(pk=tag_to_delete["pk"]).delete()

        self.stdout.write(self.help)

        tags = Tag.objects.order_by("pk").all()

        # all tags which weren't stripped
        tags_tmp_dict = {
            tag.title: dict(
                pk=tag.pk,
                title=tag.title,
                stripped=tag.title.strip(),
            )
            for tag in tags
            if tag.title.strip() != tag.title
        }

        for title, tag in tags_tmp_dict.items():
            tag_to_use_instead = Tag.objects.filter(title=tag["stripped"]).first()
            if tag_to_use_instead:
                # if we got something to use instead
                replace(tag, tag_to_use_instead)
            else:
                # otherwise simply strip our tag
                stripped = Tag.objects.get(pk=tag["pk"])
                stripped.name = tag["stripped"]
                stripped.save()
                self.stdout.write(f"Stripped {title_pk(tag)} to {title_pk(stripped)}")
