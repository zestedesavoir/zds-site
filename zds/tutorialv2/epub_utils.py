import contextlib
import logging
import shutil
from urllib import parse
from os import path
from bs4 import BeautifulSoup
from pathlib import Path
from shutil import copytree, copy
from django.template.loader import render_to_string
from django.conf import settings

from zds.tutorialv2.publish_container import publish_container
from zds.utils import slugify


def __build_mime_type_conf():
    # this is just a way to make the "mime" more mockable. For now it's compatible with
    # EPUB 3 standard (https://fr.flossmanuals.net/creer-un-epub/epub-3/ (fr))
    return {
        'filename': 'mimetype',
        'content': 'application/epub+zip'
    }


def __traverse_and_identify_images(image_dir):
    """
    :param image_dir:
    :type image_dir: pathlib.Path
    :return:
    """
    media_type_map = {
        '.png': 'image/png',
        '.jpeg': 'image/jpeg',
        '.jpg': 'image/jpeg',
        '.gif': 'image/gif',
        '.svg': 'image/svg',
    }

    for image_file_path in image_dir.iterdir():
        ext = path.splitext(image_file_path.name)[1]
        identifier = 'image_{}'.format(image_file_path.name).lower().replace('.', '-')
        ebook_image_path = Path('images', image_file_path.name)
        yield ebook_image_path, identifier, media_type_map.get(ext.lower(), 'image/png')


def build_html_chapter_file(published_object, versioned_object, working_dir, root_dir):
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
    :return: a generator of tuples composed as ``[splitted_html_file_relative_path, chapter-identifier, chapter-title]``
    """
    path_to_title_dict = publish_container(published_object, str(working_dir), versioned_object,
                                           template='tutorialv2/export/ebook/chapter.html',
                                           file_ext='xhtml', image_callback=handle_images,
                                           image_directory=str(working_dir / '..' / 'images'),
                                           relative='.')
    for container_path, title in path_to_title_dict.items():
        # TODO: check if a function exists in the std lib to get rid of `root_dir + '/'`
        yield container_path.replace(str(root_dir.absolute()) + '/', ''), 'chapter-' + slugify(title), title


def build_toc_ncx(chapters, tutorial, working_dir):
    with Path(working_dir, 'toc.ncx').open('w', encoding='utf-8') as toc_ncx_path:
        toc_ncx_path.write(render_to_string('tutorialv2/export/ebook/toc.ncx.html',
                                            context={
                                                'chapters': chapters,
                                                'title': tutorial.title,
                                                'description': tutorial.description,
                                                'content': tutorial
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


def build_nav_xhtml(working_dir, content, chapters):
    with Path(working_dir, 'nav.xhtml').open('w', encoding='utf-8') as f:
        f.write(
            render_to_string('tutorialv2/export/ebook/nav.html', {'content': content,
                                                                  'chapters': chapters}))


def build_ebook(published_content_entity, working_dir, final_file_path):
    ops_dir = Path(working_dir, 'ebook', 'OPS')
    text_dir_path = Path(ops_dir, 'Text')
    style_dir_path = Path(ops_dir, 'Text', 'styles')
    font_dir_path = Path(ops_dir, 'Fonts')
    meta_inf_dir_path = Path(working_dir, 'ebook', 'META-INF')
    target_image_dir = Path(ops_dir, 'images')

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
    mime_path = Path(working_dir, 'ebook', mimetype_conf['filename'])
    with contextlib.suppress(FileExistsError):
        copytree(published_content_entity.content.gallery.get_gallery_path(), str(target_image_dir))

    with mime_path.open(mode='w', encoding='utf-8') as mimefile:
        mimefile.write(mimetype_conf['content'])

    chapters = list(
        build_html_chapter_file(published_content_entity.content,
                                published_content_entity.content.load_version(sha=published_content_entity.sha_public),
                                working_dir=text_dir_path,
                                root_dir=Path(working_dir, 'ebook')))
    build_toc_ncx(chapters, published_content_entity, ops_dir)
    copy_or_create_empty(settings.ZDS_APP['content']['epub_stylesheets']['toc'], style_dir_path, 'toc.css')
    copy_or_create_empty(settings.ZDS_APP['content']['epub_stylesheets']['full'], style_dir_path, 'zmd.css')
    copy_or_create_empty(settings.ZDS_APP['content']['epub_stylesheets']['katex'], style_dir_path, 'katex.css')
    style_images_path = Path(settings.BASE_DIR, 'dist', 'images')
    smiley_images_path = Path(settings.BASE_DIR, 'dist', 'smileys')
    if style_images_path.exists():
        import_asset(style_images_path, target_image_dir)
    if smiley_images_path.exists():
        import_asset(smiley_images_path, target_image_dir)
    images = __traverse_and_identify_images(target_image_dir)
    build_content_opf(published_content_entity, chapters, images, ops_dir)
    build_container_xml(meta_inf_dir_path)
    build_nav_xhtml(ops_dir, published_content_entity, chapters)

    shutil.make_archive(str(final_file_path), format='zip', root_dir=str(Path(working_dir, 'ebook')),
                        logger=logging.getLogger(__name__))
    shutil.move(str(final_file_path) + '.zip', str(final_file_path))


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
        with Path(dst_path, default_name).open('w', encoding='utf-8') as f:
            f.write('')


def handle_images(relative_path):
    def _(html_code):
        soup_parser = BeautifulSoup(html_code, 'lxml')
        for image in soup_parser.find_all('img'):
            if not image.get('src', ''):
                continue
            image_url = image['src']
            if image_url.startswith('http://') or image_url.startswith('https://'):
                splitted = parse.urlsplit(image_url)
                final_path = splitted.path
            else:
                final_path = image_url
            if not path.splitext(final_path)[1]:
                final_path += '.png'
            if final_path.endswith('svg') or final_path.endswith('gif'):
                final_path = final_path[:-3] + 'png'
            image_path_in_ebook = relative_path + '/images/' + Path(final_path).name.replace('%20', '_')
            image['src'] = str(image_path_in_ebook)
        ids = {}
        for element in soup_parser.find_all(name=None, attrs={'id': (lambda s: True)}):
            while element.get('id', None) and element['id'] in ids:
                element['id'] += '-1'
            if element.get('id', None):
                ids[element['id']] = True
        return soup_parser.prettify('utf-8').decode('utf-8')
    return _
