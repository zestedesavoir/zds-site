import os

from django.core.management.base import BaseCommand

from zds import json_handler
from zds.tutorialv2.models.versioned import Container, Extract, VersionedContent
from zds.utils.models import Licence
from zds.utils.uuslug_wrapper import slugify


class Command(BaseCommand):
    help = "Create a v2.0 manifest from a 1.0 manifest.json"

    def add_arguments(self, parser):
        parser.add_argument("manifest_path", type=str)

    def handle(self, *args, **options):
        _file = options["manifest_path"]
        if os.path.isfile(_file) and _file[-5:] == ".json":
            with open(_file) as json_file:
                data = json_handler.load(json_file)
            _type = "TUTORIAL"
            if data["type"].lower() == "article":
                _type = "ARTICLE"
            versioned = VersionedContent("", _type, data["title"], slugify(data["title"]))
            versioned.description = data["description"]
            if "introduction" in data:
                versioned.introduction = data["introduction"]
            if "conclusion" in data:
                versioned.conclusion = data["conclusion"]
            versioned.licence = Licence.objects.filter(code=data["licence"]).first()
            versioned.version = "2.0"
            versioned.slug = slugify(data["title"])
            if "parts" in data:
                # if it is a big tutorial
                for part in data["parts"]:
                    current_part = Container(part["title"], str(part["pk"]) + "_" + slugify(part["title"]))
                    if "introduction" in part:
                        current_part.introduction = part["introduction"]
                    if "conclusion" in part:
                        current_part.conclusion = part["conclusion"]
                    versioned.add_container(current_part)
                    for chapter in part["chapters"]:
                        current_chapter = Container(
                            chapter["title"], str(chapter["pk"]) + "_" + slugify(chapter["title"])
                        )
                        if "introduction" in chapter:
                            current_chapter.introduction = chapter["introduction"]
                        if "conclusion" in chapter:
                            current_chapter.conclusion = chapter["conclusion"]
                        current_part.add_container(current_chapter)
                        for extract in chapter["extracts"]:
                            current_extract = Extract(
                                extract["title"], str(extract["pk"]) + "_" + slugify(extract["title"])
                            )
                            current_chapter.add_extract(current_extract)
                            current_extract.text = current_extract.get_path(True)

            elif "chapter" in data:
                # if it is a mini tutorial
                for extract in data["chapter"]["extracts"]:
                    current_extract = Extract(extract["title"], str(extract["pk"]) + "_" + slugify(extract["title"]))
                    versioned.add_extract(current_extract)
                    current_extract.text = current_extract.get_path(True)

            elif versioned.type == "ARTICLE":
                extract = Extract("text", "text")
                versioned.add_extract(extract)
                extract.text = extract.get_path(True)

            with open(_file, "w") as json_file:
                json_file.write(versioned.get_json())
