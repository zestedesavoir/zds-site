from zds.tutorialv2.models import Extract, VersionedContent, Container
from django.core.management.base import BaseCommand
from zds.gallery.models import Gallery, UserGallery
from zds.utils import slugify
from zds.utils.models import Licence
from datetime import datetime
from zds.utils import slugify
import os
try:
    import ujson as json_reader
except ImportError:
    try:
        import simplejson as json_reader
    except:
        import json as json_reader

class Command(BaseCommand):
    help = 'Create a v2.0 manifest from a 1.0 manifest.json'
    args = 'manifest_path'
    def handle(self, *args, **options):
        if len(args) == 0:
            exit()
        _file = args[0]
        if os.path.isfile(_file) and _file[-5:]==".json":
            with open(_file, "r") as json_file:
                data = json_reader.load(json_file)
            _type = "TUTORIAL"
            if "type" not in data:
                _type = "ARTICLE"
            versioned = VersionedContent("", _type, data["title"], slugify(data["title"]))
            versioned.description = data["description"]
            versioned.introduction = data["introduction"]
            versioned.conclusion = data["conclusion"]
            versioned.licence = Licence.objects.filter(code=data["licence"]).first()
            versioned.version = "2.0"
            versioned.slug = slugify(data["title"])
            if "parts" in data:
                # if it is a big tutorial
                for part in data["parts"]:
                    current_part = Container(part["title"],
                        str(part["pk"]) + "_" + slugify(part["title"]))
                    current_part.introduction = part["introduction"]
                    current_part.conclusion = part["conclusion"]
                    versioned.add_container(current_part)
                    for chapter in part["chapters"]:
                        current_chapter = Container(chapter["title"],
                            str(chapter["pk"]) + "_" + slugify(chapter["title"]))
                        current_chapter.introduction = chapter["introduction"]
                        current_chapter.conclusion = chapter["conclusion"]
                        current_part.add_container(current_chapter)
                        for extract in chapter["extracts"]:
                            current_extract = Extract(extract["title"],
                                str(extract["pk"]) + "_" + slugify(extract["title"]))
                            current_chapter.add_extract(current_extract)
                            current_extract.text = current_extract.get_path(True)
                            
            elif "chapter" in data:
                # if it is a mini tutorial
                for extract in data["chapter"]["extracts"]:
                    current_extract = Extract(extract["title"],
                        str(extract["pk"]) + "_" + slugify(extract["title"]))
                    current_extract.text = current_extract.get_path(True)
                    versioned.add_extract(current_extract)
            
            with open(_file, "w") as json_file:
                json_file.write(versioned.get_json().encode('utf-8'))
