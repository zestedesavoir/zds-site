# coding: utf-8
from __future__ import unicode_literals
from os import path, makedirs
from pathlib import Path

from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from zds.utils.templatetags.emarkdown import emarkdown


def publish_container(db_object, base_dir, container, template='tutorialv2/export/chapter.html',
                      file_ext='html', image_callback=None):
    """ 'Publish' a given container, in a recursive way

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
    path_to_title_dict = {}

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
        parsed = render_to_string(template, {'container': container, 'is_js': is_js})

        write_chapter_file(base_dir, container, Path(container.get_prod_path(True, file_ext)),
                           parsed, path_to_title_dict)
        for extract in container.children:
            extract.text = None

        container.introduction = None
        container.conclusion = None

    else:  # separate render of introduction and conclusion

        # create subdirectory
        if not path.isdir(current_dir):
            makedirs(current_dir)

        if container.introduction:
            part_path = Path(container.get_prod_path(relative=True), 'introduction.' + file_ext)
            parsed = emarkdown(container.get_introduction(), db_object.js_support)
            container.introduction = str(part_path)
            write_chapter_file(base_dir, container, part_path, parsed, path_to_title_dict)

        if container.conclusion:
            part_path = Path(container.get_prod_path(relative=True), 'conclusion.' + file_ext)
            parsed = emarkdown(container.get_introduction(), db_object.js_support)
            container.conclusion = str(part_path)
            write_chapter_file(base_dir, container, part_path, parsed, path_to_title_dict)

        for child in container.children:
            path_to_title_dict.update(publish_container(db_object, base_dir, child))
    return path_to_title_dict


def write_chapter_file(base_dir, container, part_path, parsed, path_to_title_dict):
    """
    Takes a chapter (i.e a set of extract gathers in one html text) and write in into the right file.

    :param base_dir: the directory into wich we will write the file
    :param container: the container to publish
    :type container: zds.tutorialv2.models.versioned.Container
    :param part_path: the relative path of the part to publish as html file
    :type part_path: pathlib.Path
    :param parsed: the html code
    :param path_to_title_dict: dictionary to write the data, usefull when dealing with epub.
    """
    full_path = Path(base_dir, part_path)
    with full_path.open('w', encoding='utf-8') as chapter_file:
        try:
            chapter_file.write(parsed)
        except (UnicodeError, UnicodeEncodeError):
            from zds.tutorialv2.publication_utils import FailureDuringPublication
            raise FailureDuringPublication(
                _(u'Une erreur est survenue durant la publication de « {} », vérifiez le code markdown')
                .format(container.title))
    path_to_title_dict[str(part_path)] = container.title
