import collections
import contextlib
import copy
from os import makedirs, path
from pathlib import Path

import requests
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from zds.tutorialv2.models.database import PublishableContent
from zds.tutorialv2.models.versioned import Container, VersionedContent
from zds.tutorialv2.utils import export_content
from zds.utils.templatetags.emarkdown import emarkdown, render_markdown


def publish_use_manifest(db_object, base_dir, versionable_content: VersionedContent):
    base_content = export_content(versionable_content, with_text=True)

    md, metadata, __ = render_markdown(
        base_content, disable_jsfiddle=not db_object.js_support, full_json=True, stats=True
    )
    publish_container_new(db_object, base_dir, versionable_content, md)
    return metadata.get("stats", {}).get("signs", 0)


def publish_container_new(
    db_object,
    base_dir,
    container: Container,
    rendered,
    template="tutorialv2/export/chapter.html",
    file_ext="html",
    **ctx,
):
    """
    Generate the browser-diplay or epub of a content and its possible hierarchy
    :param db_object:
    :type db_object: zds.tutorialv2.models.database.PublishableContent
    :param base_dir: ``contents-public/{tutorial_slug}``
    :param container: tutorial/part/chapter depending of the depth of recursivity
    :type container: zds.tutorialv2.models.versionable.Container
    :param rendered: dictionary of html-rendered parts of the tutorial
    :type rendered: dict
    :param template: template to render a Container with extract
    :param file_ext: html (for zds) for xml, please see ``publish_content``
    :param ctx: keyword args to pass to template
    """
    current_dir = path.dirname(path.join(base_dir, container.get_prod_path(relative=True)))
    if container.has_extracts():  # the container can be rendered in one template
        render_chapter_or_minituto(base_dir, container, ctx, rendered, template)
    else:  # separate render of introduction and conclusion
        # create subdirectory
        if not path.isdir(current_dir):
            makedirs(current_dir)
        relative_ccl_path = "../" + ctx.get("relative", ".")
        # if we are on big tuto, parts are rendered as
        # | Introduction
        # +-------------
        # | Table content of part
        # +-------------
        # | Conclusion
        if container.introduction and container.get_introduction():
            render_introduction(base_dir, container, ctx, file_ext, relative_ccl_path, rendered)
        children = copy.copy(container.children)
        container.children = []
        container.children_dict = {}

        for i, child in enumerate(children):
            # Do not publish if element is not ready to publish
            if not child.ready_to_publish:
                continue
            # render chapters
            altered_version = copy.copy(child)
            container.children.append(altered_version)
            container.children_dict[altered_version.slug] = altered_version
            publish_container_new(db_object, base_dir, altered_version, rendered["children"][i], **ctx)

        if container.conclusion and container.get_conclusion():
            render_conclusion(base_dir, container, ctx, file_ext, relative_ccl_path, rendered)


def render_conclusion(base_dir, container, ctx, file_ext, relative_ccl_path, rendered):
    part_path = Path(container.get_prod_path(relative=True), "conclusion." + file_ext)
    args = {"text": container.get_conclusion()}
    args.update(ctx)
    args["relative"] = relative_ccl_path
    parsed = rendered["conclusion"]
    container.conclusion = str(part_path)
    write_chapter_file(base_dir, container, part_path, parsed, {})


def render_introduction(base_dir, container, ctx, file_ext, relative_ccl_path, rendered):
    part_path = Path(container.get_prod_path(relative=True), "introduction." + file_ext)
    args = {"text": container.get_introduction()}
    args.update(ctx)
    args["relative"] = relative_ccl_path
    if ctx.get("intro_ccl_template", None):
        parsed = render_to_string(ctx.get("intro_ccl_template"), args)
    else:
        parsed = rendered["introduction"]
    container.introduction = str(part_path)
    write_chapter_file(base_dir, container, part_path, parsed, {})


def render_chapter_or_minituto(base_dir, container, ctx, rendered, template):
    rendered["children"] = zip(rendered["children"], container.children)
    args = {"container": rendered, "versioned_object": container}
    args.update(ctx)
    parsed = render_to_string(template, args)
    write_chapter_file(
        base_dir,
        container,
        Path(container.get_prod_path(True)),
        parsed,
        {},
    )
    for extract in container.children:
        extract.text = None
    container.introduction = None
    container.conclusion = None


def publish_container(
    db_object,
    base_dir,
    container,
    template="tutorialv2/export/chapter.html",
    file_ext="html",
    image_callback=None,
    **ctx,
):
    """'Publish' a given container, in a recursive way
    Only here for epub publication (complexity of image/path traversal for the archive to be built)

    :param image_callback: callback used to change images tags on the created html
    :type image_callback: callable
    :param db_object: database representation of the content
    :type db_object: PublishableContent
    :param base_dir: directory of the top container
    :type base_dir: str
    :param template: the django template we will use to produce chapter export to html.
    :param container: a given container
    :type container: Container
    :param file_ext: output file extension
    :raise FailureDuringPublication: if anything goes wrong
    """

    from zds.tutorialv2.models.versioned import Container
    from zds.tutorialv2.publication_utils import FailureDuringPublication

    path_to_title_dict = collections.OrderedDict()
    ctx["relative"] = ctx.get("relative", ".")
    if not isinstance(container, Container):
        raise FailureDuringPublication(_("Le conteneur n'en est pas un !"))

    # jsFiddle support
    is_js = ""
    if db_object.js_support:
        is_js = "js"

    current_dir = path.dirname(path.join(base_dir, container.get_prod_path(relative=True)))

    if not path.isdir(current_dir):
        makedirs(current_dir)

    img_relative_path = ".." if ctx["relative"] == "." else "../" + ctx["relative"]
    wrapped_image_callback = image_callback(img_relative_path) if image_callback else None
    if container.has_extracts():  # the container can be rendered in one template
        args = {"container": container, "is_js": is_js}
        args.update(ctx)
        args["relative"] = img_relative_path
        parsed = render_to_string(template, args)
        write_chapter_file(
            base_dir,
            container,
            Path(container.get_prod_path(True, file_ext)),
            parsed,
            path_to_title_dict,
            wrapped_image_callback,
        )
        for extract in container.children:
            extract.text = None

        container.introduction = None
        container.conclusion = None
    else:  # separate render of introduction and conclusion
        # create subdirectory
        if not path.isdir(current_dir):
            makedirs(current_dir)
        relative_ccl_path = "../" + ctx.get("relative", ".")
        if container.introduction and container.get_introduction():
            part_path = Path(container.get_prod_path(relative=True), "introduction." + file_ext)
            args = {"text": container.get_introduction()}
            args.update(ctx)
            args["relative"] = relative_ccl_path
            if ctx.get("intro_ccl_template", None):
                parsed = render_to_string(ctx.get("intro_ccl_template"), args)
            else:
                parsed = emarkdown(container.get_introduction(), db_object.js_support)
            container.introduction = str(part_path)
            write_chapter_file(base_dir, container, part_path, parsed, path_to_title_dict, wrapped_image_callback)
        children = copy.copy(container.children)
        container.children = []
        container.children_dict = {}
        for child in filter(lambda c: c.ready_to_publish, children):
            altered_version = copy.copy(child)
            container.children.append(altered_version)
            container.children_dict[altered_version.slug] = altered_version
            if not child.has_extracts():
                ctx["relative"] = "../" + ctx["relative"]
            result = publish_container(
                db_object,
                base_dir,
                altered_version,
                file_ext=file_ext,
                image_callback=image_callback,
                template=template,
                **ctx,
            )
            path_to_title_dict.update(result)
        if container.conclusion and container.get_conclusion():
            part_path = Path(container.get_prod_path(relative=True), "conclusion." + file_ext)
            args = {"text": container.get_conclusion()}
            args.update(ctx)
            args["relative"] = relative_ccl_path
            if ctx.get("intro_ccl_template", None):
                parsed = render_to_string(ctx.get("intro_ccl_template"), args)
            else:
                parsed = emarkdown(container.get_conclusion(), db_object.js_support)
            container.conclusion = str(part_path)
            write_chapter_file(base_dir, container, part_path, parsed, path_to_title_dict, wrapped_image_callback)

    return path_to_title_dict


def write_chapter_file(base_dir, container, part_path, parsed, path_to_title_dict, image_callback=None):
    """
    Takes a chapter (i.e a set of extract gathers in one html text) and write in into the right file.

    :param image_callback: a callback taking html code and transforming img tags
    :type image_callback: callable
    :param base_dir: the directory into wich we will write the file
    :param container: the container to publish
    :type container: zds.tutorialv2.models.versioned.Container
    :param part_path: the relative path of the part to publish as html file
    :type part_path: pathlib.Path
    :param parsed: the html code
    :param path_to_title_dict: dictionary to write the data, usefull when dealing with epub.
    """
    full_path = Path(base_dir, part_path)
    if image_callback:
        parsed = image_callback(parsed)
    if not full_path.parent.exists():
        with contextlib.suppress(OSError):
            full_path.parent.mkdir(parents=True)
    with full_path.open("w", encoding="utf-8") as chapter_file:
        try:
            chapter_file.write(parsed)
        except (UnicodeError, UnicodeEncodeError):
            from zds.tutorialv2.publication_utils import FailureDuringPublication

            raise FailureDuringPublication(
                _("Une erreur est survenue durant la publication de « {} », vérifiez le code markdown").format(
                    container.title
                )
            )
    # fix duplicate of introduction and conclusion in ebook ids
    if part_path.name.startswith("conclusion.") or part_path.name.startswith("introduction."):
        path_to_title_dict[str(part_path)] = part_path.name.split(".")[0] + "_" + container.title
    else:
        path_to_title_dict[str(part_path)] = container.title
