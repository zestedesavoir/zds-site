import os
from codecs import open  # I just want to be sure I will never open a file without codecs facility
from uuslug import slugify
from os.path import join
from shutil import copytree, copy
from os import makedirs
from django.template.loader import render_to_string
from django.conf import settings
from lxml import etree
from lxml.html import HTMLParser
from uuid import uuid4

from zds.tutorialv2.publish_container import publish_container


def __build_mime_type_conf():
    # this is just a way to make the "mime" more mockable. For now I'm compatible with
    # EPUB 3 standard (https://fr.flossmanuals.net/creer-un-epub/epub-3/ (fr))
    return {
        'filename': 'mimetype',
        'content': 'application/epub+zip'
    }


def __traverse_chapter(html_code):
    root = etree.fromstring(html_code, HTMLParser())
    all_chapter_headings = root.cssselect('h3')  # header_shift = 2
    for title_element in all_chapter_headings:
        full_title = title_element.text_content()
        stringified = etree.tostring(title_element)
        current = title_element
        while current.getnext() and current.getnext().tag.lower != 'h3':
            current = current.getnext()
            stringified += etree.tostring(current)
        yield full_title, stringified


def __traverse_and_identify_images(image_dir):
    for _, _, files in os.walk(image_dir):
        for image_filename in files:
            yield join(image_dir, image_filename), str(uuid4())


def build_html_chapter_file(publishable_object, versioned_object, working_dir, root_dir):
    """
    parses an the full html file, extracts the ``<hX>`` tags and split their content into new files.
    it yields all the produced files

    :param full_html_file:
    :return: a generator of tuples composed as ``[plitted_html_file_relative_path,chapter_full_title]``
    """
    path_to_title_dict = publish_container(publishable_object, working_dir, versioned_object,
                                           template='tutorialv2/export/ebook/chapter.html')
    for path, title in path_to_title_dict.items():
        # TODO: check if a function exists in the std lib to get rid of `root_dir + '/'`
        yield path.replace(root_dir + '/', ''), title


def build_toc_ncx(chapters, tutorial, working_dir):
    with open(join(working_dir, 'toc.ncx'), mode='wb', encoding='utf-8') as f:
        f.write(render_to_string('tutorialv2/export/ebook/toc.ncx.html',
                                 context={
                                     'chapters': chapters,
                                     'title': tutorial.title,
                                     'description': tutorial.description
        }))


def build_content_opf(content, chapters, images, working_dir):
    with open(join(working_dir, 'content.opf'), mode='wb', encoding='utf-8') as f:
        f.write(render_to_string('tutorialv2/export/ebook/content.opf.xml',
                                 context={
                                     'content': content,
                                     'chapters': chapters,
                                     'images': images
                                 }))


def build_container_xml(working_dir):
    with open(join(working_dir, 'container.xml'), mode='wb', encoding='utf-8') as f:
        f.write(render_to_string('tutorialv2/export/ebook/container.xml'))


def build_ebook(published_content_entity, working_dir):
    makedirs(join(working_dir, 'ebook', 'OPS', 'Text'))
    makedirs(join(working_dir, 'ebook', 'OPS', 'Style'))
    makedirs(join(working_dir, 'ebook', 'OPS', 'Fonts'))
    makedirs(join(working_dir, 'ebook', 'META-INF'))
    copytree(join(working_dir, 'images'), join(working_dir, 'ebook', 'OPS', 'Images'))
    mimetype_conf = __build_mime_type_conf()
    with open(join(working_dir, 'ebook', mimetype_conf['filename']), mode="w", encoding='utf-8') as mimefile:
        mimefile.write(mimetype_conf['content'])
    chapters = list(
        build_html_chapter_file(published_content_entity.content,
                                published_content_entity.content.load_version(sha=published_content_entity.sha_public),
                                working_dir=join(working_dir, 'ebook', 'OPS', 'Text'),
                                root_dir=join(working_dir, 'ebook')))
    build_toc_ncx(chapters, published_content_entity, join(working_dir, 'ebook', 'OPS'))
    images = __traverse_and_identify_images(join(working_dir, 'ebook', 'OPS', 'Images'))
    build_content_opf(published_content_entity, chapters, images, join(working_dir, 'ebook', 'OPS'))
    build_container_xml(join(working_dir, 'ebook', 'META-INF'))
    copy(settings.ZDS_APP['content']['epub_stylesheets']['toc'], join(working_dir, 'ebook', 'OPS', 'Style'))
    copy(settings.ZDS_APP['content']['epub_stylesheets']['full'], join(working_dir, 'ebook', 'OPS', 'Style'))
