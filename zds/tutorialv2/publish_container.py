# coding: utf-8
from __future__ import unicode_literals
import codecs
from os import path, makedirs

from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from zds.utils.templatetags.emarkdown import emarkdown


def publish_container(db_object, base_dir, container, template='tutorialv2/export/chapter.html'):
    """ 'Publish' a given container, in a recursive way

    :param db_object: database representation of the content
    :type db_object: PublishableContent
    :param base_dir: directory of the top container
    :type base_dir: str
    :param template: the django template we will use to produce chapter export to html.
    :param container: a given container
    :type container: Container
    :raise FailureDuringPublication: if anything goes wrong
    """

    from zds.tutorialv2.models.models_versioned import Container
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

        write_chapter_file(base_dir, container, parsed, path_to_title_dict)
        for extract in container.children:
            extract.text = None

        container.introduction = None
        container.conclusion = None

    else:  # separate render of introduction and conclusion
        current_dir = path.join(base_dir, container.get_prod_path(relative=True))

        # create subdirectory
        if not path.isdir(current_dir):
            makedirs(current_dir)

        if container.introduction:
            part_path = path.join(container.get_prod_path(relative=True), 'introduction.html')
            write_chapter_file(base_dir, container, emarkdown(container.get_introduction(), db_object.js_support),
                               path_to_title_dict)
            container.introduction = part_path

        if container.conclusion:
            part_path = path.join(container.get_prod_path(relative=True), 'conclusion.html')
            f = codecs.open(path.join(base_dir, part_path), 'w', encoding='utf-8')

            try:
                f.write(emarkdown(container.get_conclusion(), db_object.js_support))
            except (UnicodeError, UnicodeEncodeError):
                raise FailureDuringPublication(
                    _(u'Une erreur est survenue durant la publication de la conclusion de « {} »,'
                      u' vérifiez le code markdown').format(container.title))

            container.conclusion = part_path

        for child in container.children:
            path_to_title_dict.update(publish_container(db_object, base_dir, child))
    return path_to_title_dict


def write_chapter_file(base_dir, container, parsed, path_to_title_dict):
    with codecs.open(path.join(base_dir, container.get_prod_path(relative=True)),
                     'w', encoding='utf-8') as chapter_file:
        try:
            chapter_file.write(parsed)
        except (UnicodeError, UnicodeEncodeError):
            raise FailureDuringPublication(
                _(u'Une erreur est survenue durant la publication de « {} », vérifiez le code markdown')
                    .format(container.title))
    path_to_title_dict[path.join(base_dir, container.get_prod_path(relative=True))] = container.title
