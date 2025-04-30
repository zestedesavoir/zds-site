import contextlib
import logging
import os
import re
import shutil
from collections import namedtuple
from os import path
from pathlib import Path
from shutil import copy
from urllib import parse

from bs4 import BeautifulSoup
from django.conf import settings
from django.template.loader import render_to_string

from zds.tutorialv2.publish_container import publish_container
from zds.utils import old_slugify


def __build_mime_type_conf():
    # this is just a way to make the "mime" more mockable. For now it's compatible with
    # EPUB 3 standard (https://fr.flossmanuals.net/creer-un-epub/epub-3/ (fr))
    return {"filename": "mimetype", "content": "application/epub+zip"}


def __traverse_and_identify_images(root_image_dir, current_dir=None):
    """
    :param root_image_dir: Root folder of the images
    :type root_image_dir: pathlib.Path
    :param current_dir:  Folder currently explored
    :type current_dir: pathlib.Path
    :return:
    """
    media_type_map = {
        ".png": "image/png",
        ".jpeg": "image/jpeg",
        ".jpg": "image/jpeg",
        ".gif": "image/gif",
        ".svg": "image/svg",
    }

    if current_dir is None:
        current_dir = root_image_dir

    for image_file_path in current_dir.iterdir():
        if image_file_path.is_dir():
            yield from __traverse_and_identify_images(root_image_dir, image_file_path)
            continue
        ext = path.splitext(image_file_path.name)[1]
        ebook_image_path = Path("images", image_file_path.relative_to(root_image_dir))
        identifier = "image_" + str(ebook_image_path)[7:].lower().replace(".", "-").replace("@", "-").replace("/", "-")
        yield ebook_image_path, identifier, media_type_map.get(ext.lower(), "image/png")


def build_html_chapter_file(published_object, versioned_object, working_dir, root_dir, image_handler):
    """
    Parses the full html file, extracts the ``<hX>`` tags and splits their content into new files.
    Yields all the produced files.

    :param root_dir: the root directory into which dump the ebook
    :type root_dir: pathlib.Path
    :param working_dir:
    :type working_dir: pathlib.Path
    :param versioned_object: the object representing the public version in git file system
    :type versioned_object: zds.tutorialv2.models.models_versioned.VersionedContent
    :param published_object: the published content as saved in database
    :type published_object: zds.tutorialv2.models.models_database.PublishedContent
    :type image_handler: ImageHandling
    :return: a generator of tuples composed as ``[splitted_html_file_relative_path, chapter-identifier, chapter-title]``
    """
    DirTuple = namedtuple("DirTuple", ["absolute", "relative"])
    img_dir = working_dir.parent / "images"
    path_to_title_dict = publish_container(
        published_object,
        str(working_dir),
        versioned_object,
        template="tutorialv2/export/ebook/chapter.html",
        file_ext="xhtml",
        image_callback=image_handler.handle_images,
        image_directory=DirTuple(str(img_dir.absolute()), str(img_dir.relative_to(root_dir))),
        relative=".",
        intro_ccl_template="tutorialv2/export/ebook/introduction.html",
    )
    for container_path, title in path_to_title_dict.items():
        # TODO: check if a function exists in the std lib to get rid of `root_dir + '/'`
        yield container_path.replace(str(root_dir.absolute()) + "/", ""), "chapter-" + old_slugify(title), title


def build_toc_ncx(chapters, tutorial, working_dir):
    with Path(working_dir, "toc.ncx").open("w", encoding="utf-8") as toc_ncx_path:
        toc_ncx_path.write(
            render_to_string(
                "tutorialv2/export/ebook/toc.ncx.html",
                context={
                    "chapters": chapters,
                    "title": tutorial.title,
                    "description": tutorial.description,
                    "content": tutorial,
                },
            )
        )


def build_content_opf(content, chapters, images, working_dir):
    with Path(working_dir, "content.opf").open("w", encoding="utf-8") as content_opf_path:
        content_opf_path.write(
            render_to_string(
                "tutorialv2/export/ebook/content.opf.xml",
                context={"content": content, "chapters": chapters, "images": images},
            )
        )


def build_container_xml(working_dir):
    with Path(working_dir, "container.xml").open("w", encoding="utf-8") as f:
        f.write(render_to_string("tutorialv2/export/ebook/container.xml"))


def build_nav_xhtml(working_dir, content, chapters):
    with Path(working_dir, "nav.xhtml").open("w", encoding="utf-8") as f:
        f.write(render_to_string("tutorialv2/export/ebook/nav.html", {"content": content, "chapters": chapters}))


def build_ebook(published_content_entity, working_dir, final_file_path):
    ops_dir = Path(working_dir, "ebook", "OPS")
    text_dir_path = Path(ops_dir, "Text")
    style_dir_path = Path(ops_dir, "styles")
    font_dir_path = Path(ops_dir, "Fonts")
    meta_inf_dir_path = Path(working_dir, "ebook", "META-INF")
    target_image_dir = Path(ops_dir, "images")

    with contextlib.suppress(FileExistsError):  # Forced to use this until python 3.5 is used and ok_exist appears
        text_dir_path.mkdir(parents=True)
    with contextlib.suppress(FileExistsError):
        style_dir_path.mkdir(parents=True)
    with contextlib.suppress(FileExistsError):
        font_dir_path.mkdir(parents=True)
    with contextlib.suppress(FileExistsError):
        meta_inf_dir_path.mkdir(parents=True)
    with contextlib.suppress(FileExistsError):
        target_image_dir.mkdir(parents=True)

    mimetype_conf = __build_mime_type_conf()
    mime_path = Path(working_dir, "ebook", mimetype_conf["filename"])
    with contextlib.suppress(FileExistsError, FileNotFoundError):
        for img in published_content_entity.content.gallery.get_gallery_path().iterdir():
            shutil.copy(str(img), str(target_image_dir))

    with mime_path.open(mode="w", encoding="utf-8") as mimefile:
        mimefile.write(mimetype_conf["content"])
    image_handler = ImageHandling()
    chapters = list(
        build_html_chapter_file(
            published_content_entity.content,
            published_content_entity.content.load_version(sha=published_content_entity.sha_public),
            working_dir=text_dir_path,
            root_dir=Path(working_dir, "ebook"),
            image_handler=image_handler,
        )
    )
    build_toc_ncx(chapters, published_content_entity, ops_dir)
    copy_or_create_empty(settings.ZDS_APP["content"]["epub_stylesheets"]["toc"], style_dir_path, "toc.css")
    copy_or_create_empty(settings.ZDS_APP["content"]["epub_stylesheets"]["full"], style_dir_path, "zmd.css")
    copy_or_create_empty(settings.ZDS_APP["content"]["epub_stylesheets"]["katex"], style_dir_path, "katex.css")
    style_images_path = settings.BASE_DIR / "dist" / "images"
    smiley_images_path = settings.BASE_DIR / "dist" / "smileys" / "svg"
    if style_images_path.exists():
        import_asset(style_images_path, target_image_dir)
    if smiley_images_path.exists():
        import_asset(smiley_images_path, target_image_dir)
    images = list(__traverse_and_identify_images(target_image_dir))
    image_handler.names.add("sprite.png")
    images = image_handler.remove_unused_image(target_image_dir, images)
    build_content_opf(published_content_entity, chapters, images, ops_dir)
    build_container_xml(meta_inf_dir_path)
    build_nav_xhtml(ops_dir, published_content_entity, chapters)

    zip_logger = logging.getLogger(__name__ + ".zip")
    zip_logger.setLevel(logging.WARN)
    shutil.make_archive(str(final_file_path), format="zip", root_dir=str(Path(working_dir, "ebook")), logger=zip_logger)
    shutil.move(str(final_file_path) + ".zip", str(final_file_path))


def import_asset(style_images_path, target_image_dir):
    for img_path in style_images_path.iterdir():
        if img_path.is_file():
            shutil.copy2(str(img_path), str(target_image_dir))
        else:
            import_asset(img_path, target_image_dir)


def copy_or_create_empty(src_path, dst_path, default_name):
    if src_path.exists():
        copy(str(src_path), str(dst_path))
    else:
        with Path(dst_path, default_name).open("w", encoding="utf-8") as f:
            f.write("")


class ImageHandling:
    def __init__(self):
        self.names = set()
        self.url_scheme_matcher = re.compile(r"^https?://")

    def handle_images(self, relative_path):
        def handle_image_path_with_good_img_dir_path(html_code):
            soup_parser = BeautifulSoup(html_code, "lxml")
            for image in soup_parser.find_all("img"):
                if not image.get("src", ""):
                    continue
                image_url = image["src"]
                if self.url_scheme_matcher.search(image_url):
                    splitted = parse.urlsplit(image_url)
                    final_path = splitted.path
                elif (not (Path(settings.MEDIA_URL).is_dir() and Path(image_url).exists())) and image_url.startswith(
                    settings.MEDIA_URL
                ):
                    # do not go there if image_url is the path on the system
                    # and not a portion of web URL
                    # (image_url.startswith(settings.MEDIA_URL) can be True if
                    # zds-site is in a directory under /media (the default
                    # value of settings.MEDIA_URL))
                    final_path = Path(image_url).name
                elif Path(image_url).is_absolute() and "images" in image_url:
                    root = Path(image_url)
                    while root.name != "images":
                        root = root.parent
                    final_path = str(Path(image_url).relative_to(root))
                else:
                    final_path = Path(image_url).name
                image_path_in_ebook = relative_path + "/images/" + str(final_path).replace("%20", "_")
                image["src"] = str(image_path_in_ebook)
                self.names.add(final_path)
            ids = {}
            for element in soup_parser.find_all(name=None, attrs={"id": (lambda s: True)}):
                while element.get("id", None) and element["id"] in ids:
                    element["id"] += "-1"
                if element.get("id", None):
                    ids[element["id"]] = True
            return soup_parser.prettify("utf-8").decode("utf-8")

        return handle_image_path_with_good_img_dir_path

    def remove_unused_image(self, image_path: Path, imglist):
        # Remove unused images:
        for image in image_path.rglob("*"):
            if str(Path(image).relative_to(image_path)) not in self.names and not image.is_dir():
                os.remove(str(image))
                imglist = [i for i in imglist if i[0].name.replace("%20", "_") != image.name]
        # Remove empty folders:
        for item in image_path.iterdir():
            if item.is_dir() and len(list(item.iterdir())) == 0:
                os.rmdir(str(item))
        return imglist
