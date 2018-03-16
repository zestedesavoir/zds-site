# coding: utf-8
from __future__ import unicode_literals

import collections
import contextlib
from os import path, makedirs
from pathlib import Path
import copy
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from zds.utils.templatetags.emarkdown import emarkdown


def publish_container(db_object, base_dir, container, template='tutorialv2/export/chapter.html',
                      file_ext='html', image_callback=None, **ctx):
    """ 'Publish' a given container, in a recursive way

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
    ctx['relative'] = ctx.get('relative', '.')
    if not isinstance(container, Container):
        raise FailureDuringPublication(_(u"Le conteneur n'en est pas un !"))

    # jsFiddle support
    is_js = ''
    if db_object.js_support:
        is_js = 'js'

    current_dir = path.dirname(path.join(base_dir, container.get_prod_path(relative=True)))

    if not path.isdir(current_dir):
        makedirs(current_dir)

    if container.has_extracts():  # the container can be rendered in one template
        wrapped_image_callback = image_callback(ctx['relative']) if image_callback else image_callback
        args = {'container': container, 'is_js': is_js}
        args.update(ctx)
        parsed = render_to_string(template, args)
        write_chapter_file(base_dir, container, Path(container.get_prod_path(True, file_ext)),
                           parsed, path_to_title_dict, wrapped_image_callback)
        for extract in container.children:
            extract.text = None

        container.introduction = None
        container.conclusion = None

    else:  # separate render of introduction and conclusion
        wrapped_image_callback = image_callback(ctx['relative']) if image_callback else image_callback
        # create subdirectory
        if not path.isdir(current_dir):
            makedirs(current_dir)
        ctx['relative'] = '../' + ctx['relative']
        if container.introduction and container.get_introduction():
            part_path = Path(container.get_prod_path(relative=True), 'introduction.' + file_ext)
            parsed = emarkdown(container.get_introduction(), db_object.js_support)
            container.introduction = str(part_path)
            write_chapter_file(base_dir, container, part_path, parsed, path_to_title_dict,
                               wrapped_image_callback)
        children = copy.copy(container.children)
        container.children = []
        container.children_dict = {}
        for child in filter(lambda c: c.ready_to_publish, children):

            altered_version = copy.copy(child)
            container.children.append(altered_version)
            container.children_dict[altered_version.slug] = altered_version
            result = publish_container(db_object, base_dir, altered_version, file_ext=file_ext,
                                       image_callback=image_callback, template=template, **ctx)
            path_to_title_dict.update(result)
        if container.conclusion and container.get_conclusion():
            part_path = Path(container.get_prod_path(relative=True), 'conclusion.' + file_ext)
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
    with full_path.open('w', encoding='utf-8') as chapter_file:
        try:
            chapter_file.write(parsed)
        except (UnicodeError, UnicodeEncodeError):
            from zds.tutorialv2.publication_utils import FailureDuringPublication
            raise FailureDuringPublication(
                _(u'Une erreur est survenue durant la publication de « {} », vérifiez le code markdown')
                .format(container.title))
    path_to_title_dict[str(part_path)] = container.title
