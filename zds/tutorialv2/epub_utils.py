import contextlib
import logging
import shutil
from pathlib import Path
from shutil import copytree, copy
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
    """

    :param image_dir:
    :type image_dir: pathlib.Path
    :return:
    """
    media_type_map = {
        'png': 'image/png',
        'jpeg': 'image/jpeg',
        'jpg': 'image/jpeg',
        'gif': 'image/gif',
        'svg': 'image/svg',
    }

    for image_file_path in image_dir.iterdir():
        from os import path
        ext = path.splitext(image_file_path.name)[1]
        yield image_file_path.absolute(), str(uuid4()), media_type_map.get(ext.lower(), 'image/png')


def build_html_chapter_file(publishable_object, versioned_object, working_dir, root_dir):
    """
    parses an the full html file, extracts the ``<hX>`` tags and split their content into new files.
    it yields all the produced files

    :param full_html_file:
    :return: a generator of tuples composed as ``[plitted_html_file_relative_path,chapter_full_title]``
    """
    path_to_title_dict = publish_container(publishable_object, str(working_dir), versioned_object,
                                           template='tutorialv2/export/ebook/chapter.html')
    for path, title in path_to_title_dict.items():
        # TODO: check if a function exists in the std lib to get rid of `root_dir + '/'`
        yield path.replace(str(root_dir.absolute()) + '/', ''), title


def build_toc_ncx(chapters, tutorial, working_dir):
    with Path(working_dir, 'toc.ncx').open('w', encoding='utf-8') as toc_ncx_path:
        toc_ncx_path.write(render_to_string('tutorialv2/export/ebook/toc.ncx.html',
                                            context={
                                                'chapters': chapters,
                                                'title': tutorial.title,
                                                'description': tutorial.description
                                            }))


def build_content_opf(content, chapters, images, working_dir):
    with Path(working_dir, 'content.opf').open('w', encoding='utf-8') as content_opf_path:
        content_opf_path.write(render_to_string('tutorialv2/export/ebook/content.opf.xml',
                                                context={
                                                    'content': content,
                                                    'chapters': chapters,
                                                    'images': images
                                                }))


def build_container_xml(working_dir):
    with Path(working_dir, 'container.xml').open('w', encoding='utf-8') as f:
        f.write(render_to_string('tutorialv2/export/ebook/container.xml'))


def build_nav_xhtml(working_dir, content):
    with Path(working_dir, 'nav.xhtml').open('w', encoding='utf-8') as f:
        f.write(
            render_to_string('tutorialv2/export/ebook/nav.html', {'content': content})
        )


def build_ebook(published_content_entity, working_dir, final_file_path):
    ops_dir = Path(working_dir, 'ebook', 'OPS')
    text_dir_path = Path(ops_dir, 'Text')
    style_dir_path = Path(ops_dir, 'Text')
    font_dir_path = Path(ops_dir, 'Fonts')
    meta_inf_dir_path = Path(working_dir, 'ebook', 'META-INF')
    original_image_dir = Path(working_dir, 'images')
    target_image_dir = Path(ops_dir, 'Images')
    with contextlib.suppress(FileExistsError):  # Forced to use this until python 3.5 is used and ok_exist appears
        text_dir_path.mkdir(parents=True)
    with contextlib.suppress(FileExistsError):
        style_dir_path.mkdir(parents=True)
    with contextlib.suppress(FileExistsError):
        font_dir_path.mkdir(parents=True)
    with contextlib.suppress(FileExistsError):
        meta_inf_dir_path.mkdir(parents=True)
    copytree(str(original_image_dir), str(target_image_dir))
    mimetype_conf = __build_mime_type_conf()
    mime_path = Path(working_dir, 'ebook', mimetype_conf['filename'])
    with mime_path.open(mode='w', encoding='utf-8') as mimefile:
        mimefile.write(mimetype_conf['content'])
    chapters = list(
        build_html_chapter_file(published_content_entity.content,
                                published_content_entity.content.load_version(sha=published_content_entity.sha_public),
                                working_dir=text_dir_path,
                                root_dir=Path(working_dir, 'ebook'))
    )
    build_toc_ncx(chapters, published_content_entity, ops_dir)
    images = __traverse_and_identify_images(target_image_dir)
    build_content_opf(published_content_entity, chapters, images, ops_dir)
    build_container_xml(meta_inf_dir_path)
    build_nav_xhtml(ops_dir, published_content_entity)
    if settings.ZDS_APP['content']['epub_stylesheets']['toc'].exists():
        copy(str(settings.ZDS_APP['content']['epub_stylesheets']['toc']), str(style_dir_path))
    else:
        with Path(style_dir_path, 'toc.css').open('w', encoding='utf-8') as f:
            f.write('')
    style_path = settings.ZDS_APP['content']['epub_stylesheets']['full']
    if style_path.exists():
        copy(str(settings.ZDS_APP['content']['epub_stylesheets']['full']), str(style_dir_path))
    else:

        with Path(style_dir_path, style_path.name).open('w', encoding='utf-8') as f:
            f.write('')
    shutil.make_archive(str(final_file_path), format='zip', root_dir=str(Path(working_dir, 'ebook')),
                        logger=logging.getLogger(__name__))
    shutil.move(str(final_file_path) + '.zip', str(final_file_path))
