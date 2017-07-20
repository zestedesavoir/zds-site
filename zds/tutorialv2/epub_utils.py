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
    for root, _, files in os.walk(image_dir):
        for image_filename in files:
            yield join(image_dir, image_filename), str(uuid4())


def build_html_chapter_file(full_html_file, working_dir):
    """
    parses an the full html file, extracts the ``<hX>`` tags and split their content into new files.
    it yields all the produced files

    :param full_html_file: 
    :return: a generator of tuples composed as ``[chapter_full_title, splitted_html_file_relative_path]``
    """
    with open(full_html_file, encoding='utf-8') as f:
        html_code = f.read()
    for chapter_title, chapter_html in __traverse_chapter(html_code):
        with open(join(working_dir, slugify(chapter_title)), 'wb', encoding='utf-8') as f:
            f.write(chapter_html)
        yield chapter_title, join(slugify(chapter_title))


def build_toc_cnx(chapters, tutorial, working_dir):
    with open(join(working_dir, 'toc.ncx'), mode='wb', encoding='utf-8') as f:
        f.write(render_to_string('tutorialv2/export/ebook/toc.cnx.html'),
                context={
                    'chapters': chapters,
                    'title': tutorial.title,
                    'description': tutorial.description
                })


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


def build_ebook(published_content_entity, full_html_file_path, working_dir):
    makedirs(join(working_dir, 'ebook', 'OPS', 'Text'))
    makedirs(join(working_dir, 'ebook', 'OPS', 'Style'))
    makedirs(join(working_dir, 'ebook', 'OPS', 'Fonts'))
    makedirs(join(working_dir, 'ebook', 'META-INF'))
    copytree(join(working_dir, 'images'), join(working_dir, 'ebook', 'OPS', 'Images'))
    mimetype_conf = __build_mime_type_conf()
    with open(join(working_dir, 'ebook', mimetype_conf['filename']), mode="w", encoding='utf-8') as mimefile:
        mimefile.write(mimetype_conf['content'])
    chapters = list(build_html_chapter_file(full_html_file_path, join(working_dir, 'ebook', 'OPS', 'Text')))
    build_toc_cnx(chapters, published_content_entity, join(working_dir, 'ebook', 'OPS'))
    images = __traverse_and_identify_images(join(working_dir, 'ebook', 'OPS', 'Images'))
    build_content_opf(published_content_entity, chapters, images, join(working_dir, 'ebook', 'OPS'))
    build_container_xml(join(working_dir, 'ebook', 'META-INF'))
    copy(settings.ZDS_APP['content']['epub_stylesheets']['toc'], join(working_dir, 'ebook', 'OPS', 'Style'))
    copy(settings.ZDS_APP['content']['epub_stylesheets']['full'], join(working_dir, 'ebook', 'OPS', 'Style'))
