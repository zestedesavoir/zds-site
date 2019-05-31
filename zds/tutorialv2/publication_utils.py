import contextlib
import copy
import logging
import os
import shutil
import subprocess
import zipfile
from datetime import datetime
from os import makedirs, mkdir, path
from pathlib import Path

import requests
from django.core.exceptions import ObjectDoesNotExist
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from zds.notification import signals
from zds.tutorialv2.epub_utils import build_ebook
from zds.tutorialv2.models.database import ContentReaction, PublishedContent, PublicationEvent
from zds.tutorialv2.publish_container import publish_container
from zds.tutorialv2.signals import content_unpublished
from zds.utils.templatetags.emarkdown import render_markdown, MD_PARSING_ERROR
from zds.utils.templatetags.smileys_def import SMILEYS_BASE_PATH, LICENSES_BASE_PATH

logger = logging.getLogger(__name__)
licences = {
    'by-nc-nd': 'by-nc-nd.svg',
    'by-nc-sa': 'by-nc-sa.svg',
    'by-nc': 'by-nc.svg',
    'by-nd': 'by-nd.svg',
    'by-sa': 'by-sa.svg',
    'by': 'by.svg',
    '0': '0.svg',
    'copyright': 'copyright.svg'
}


def notify_update(db_object, is_update, is_major):
    if not is_update or is_major:
        # Follow
        signals.new_content.send(sender=db_object.__class__, instance=db_object, by_email=False)


def publish_content(db_object, versioned, is_major_update=True):
    """
    Publish a given content.

    .. note::
        create a manifest.json without the introduction and conclusion if not needed. Also remove the 'text' field
        of extracts.

    :param db_object: Database representation of the content
    :type db_object: zds.tutorialv2.models.database.PublishableContent
    :param versioned: version of the content to publish
    :type versioned: zds.tutorialv2.models.versioned.VersionedContent
    :param is_major_update: if set to `True`, will update the publication date
    :type is_major_update: bool
    :raise FailureDuringPublication: if something goes wrong
    :return: the published representation
    :rtype: zds.tutorialv2.models.database.PublishedContent
    """

    from zds.tutorialv2.models.database import PublishedContent

    if is_major_update:
        versioned.pubdate = datetime.now()

    # First write the files to a temporary directory: if anything goes wrong,
    # the last published version is not impacted !
    tmp_path = path.join(settings.ZDS_APP['content']['repo_public_path'], versioned.slug + '__building')
    if path.exists(tmp_path):
        shutil.rmtree(tmp_path)  # remove previous attempt, if any

    # render HTML:
    altered_version = copy.deepcopy(versioned)
    publish_container(db_object, tmp_path, altered_version)
    altered_version.dump_json(path.join(tmp_path, 'manifest.json'))

    # make room for 'extra contents'
    build_extra_contents_path = path.join(tmp_path, settings.ZDS_APP['content']['extra_contents_dirname'])
    makedirs(build_extra_contents_path)
    base_name = path.join(build_extra_contents_path, versioned.slug)

    # 1. markdown file (base for the others) :
    # If we come from a command line, we need to activate i18n, to have the date in the french language.
    cur_language = translation.get_language()
    altered_version.pubdate = datetime.now()

    md_file_path = base_name + '.md'
    with contextlib.suppress(OSError):
        Path(Path(md_file_path).parent, 'images').mkdir()
    is_update = False

    if db_object.public_version:
        is_update, public_version = update_existing_publication(db_object, versioned)
    else:
        public_version = PublishedContent()

    # make the new public version
    public_version.content_public_slug = versioned.slug
    public_version.content_type = versioned.type
    public_version.content_pk = db_object.pk
    public_version.content = db_object
    public_version.must_reindex = True
    public_version.save()
    with contextlib.suppress(FileExistsError):
        makedirs(public_version.get_extra_contents_directory())
    PublicatorRegistry.get('md').publish(md_file_path, base_name, versioned=versioned, cur_language=cur_language)
    public_version.char_count = public_version.get_char_count(md_file_path)
    if is_major_update or not is_update:
        public_version.publication_date = datetime.now()
    elif is_update:
        public_version.update_date = datetime.now()
    public_version.sha_public = versioned.current_version
    public_version.save()
    with contextlib.suppress(OSError):
        make_zip_file(public_version)

    public_version.save(
        update_fields=['char_count', 'publication_date', 'update_date', 'sha_public'])

    public_version.authors.clear()
    for author in db_object.authors.all():
        public_version.authors.add(author)

    # this puts the manifest.json and base json file on the prod path.
    shutil.rmtree(public_version.get_prod_path(), ignore_errors=True)
    shutil.copytree(tmp_path, public_version.get_prod_path())
    if settings.ZDS_APP['content']['extra_content_generation_policy'] == 'SYNC':
        # ok, now we can really publish the thing!
        generate_external_content(base_name, build_extra_contents_path, md_file_path)
    elif settings.ZDS_APP['content']['extra_content_generation_policy'] == 'WATCHDOG':
        PublicatorRegistry.get('watchdog').publish(md_file_path, base_name, silently_pass=False)
    db_object.sha_public = versioned.current_version
    return public_version


def update_existing_publication(db_object, versioned):
    public_version = db_object.public_version
    # the content has been published in the past, so clean up old files!
    old_path = public_version.get_prod_path()
    logging.getLogger(__name__).debug('erase ' + old_path)
    shutil.rmtree(old_path)
    # if the slug has changed, create a new object instead of reusing the old one
    # this allows us to handle permanent redirection so that SEO is not impacted.
    if versioned.slug != public_version.content_public_slug:
        public_version.must_redirect = True  # set redirection
        public_version.save(update_fields=['must_redirect'])
        publication_date = public_version.publication_date
        db_object.public_version = PublishedContent()
        public_version = db_object.public_version

        # keep the same publication date if the content is already published
        public_version.publication_date = publication_date
    return True, public_version


def write_md_file(md_file_path, parsed_with_local_images, versioned):
    with open(md_file_path, 'w', encoding='utf-8') as md_file:
        try:
            md_file.write(parsed_with_local_images)
        except UnicodeError:
            logger.error('Could not encode %s in UTF-8, publication aborted', versioned.title)
            raise FailureDuringPublication(_('Une erreur est survenue durant la génération du fichier markdown '
                                             'à télécharger, vérifiez le code markdown'))


def generate_external_content(base_name, extra_contents_path, md_file_path, overload_settings=False, excluded=None):
    """
    generate all static file that allow offline access to content

    :param base_name: base nae of file (without extension)
    :param extra_contents_path: internal directory where all files will be pushed
    :param md_file_path: bundled markdown file path
    :param overload_settings: this option force the function to generate all registered formats even when settings \
    ask for PDF not to be published
    :param excluded: list of excluded format, None if no exclusion
    """
    excluded = excluded or ['watchdog']
    excluded.append('md')
    if not settings.ZDS_APP['content']['build_pdf_when_published'] and not overload_settings:
        excluded.append('pdf')
    for publicator_name, publicator in PublicatorRegistry.get_all_registered(excluded):
        try:
            publicator.publish(md_file_path, base_name, change_dir=extra_contents_path)
        except (FailureDuringPublication, OSError):
            logging.getLogger(__name__).exception('Could not publish %s format from %s base.',
                                                  publicator_name, md_file_path)


class PublicatorRegistry:
    """
    Register all publicator as a 'human-readable name/publicator' instance key/value list
    """
    registry = {}

    @classmethod
    def register(cls, publicator_name, *args):
        def decorated(func):
            cls.registry[publicator_name] = func(*args)
            return func
        return decorated

    @classmethod
    def get_all_registered(cls, exclude=None):
        """
        Args:
            exclude: A list of excluded publicator

        Returns:
        """
        if exclude is None:
            exclude = []
        order_key = {
            'zip': 1,
            'html': 2,
            'epub': 3,
            'pdf': 4,
        }
        for key, value in sorted(cls.registry.items(), key=lambda k: order_key.get(k[0], 42)):
            if key not in exclude:
                yield key, value

    @classmethod
    def unregister(cls, name):
        """
        Remove registered Publicator named 'name' if present

        :param name: publicator name.
        """
        if name in cls.registry:
            del cls.registry[name]

    @classmethod
    def get(cls, name):
        """
        Get publicator named 'name'.

        :param name:
        :return: the wanted publicator
        :rtype: Publicator
        :raise KeyError: if publicator is not registered
        """
        return cls.registry[name]


class Publicator:
    """
    Publicator base object, all methods must be overridden
    """

    def publish(self, md_file_path, base_name, **kwargs):
        """
        Function called to generate a content export

        :param md_file_path: base markdown file path
        :param base_name: file name without extension
        :param kwargs: other publicator dependent options
        """
        raise NotImplementedError()

    def get_published_content_entity(self, md_file_path):
        """
        Retrieve the db entity from mdfile path

        :param md_file_path: mdfile path as string
        :type md_file_path: str
        :return: the db entity
        :rtype: zds.tutorialv2.models.models_database.PublishedContent
        """
        content_slug = PublishedContent.get_slug_from_file_path(md_file_path)
        published_content_entity = PublishedContent.objects \
            .filter(content_public_slug=content_slug) \
            .first()
        return published_content_entity


@PublicatorRegistry.register('md')
class MarkdownPublicator(Publicator):
    def publish(self, md_file_path, base_name, *, cur_language, versioned, **kwargs):
        try:
            translation.activate(settings.LANGUAGE_CODE)
            parsed = render_to_string('tutorialv2/export/content.md', {'content': versioned})
        except requests.exceptions.HTTPError:
            raise FailureDuringPublication('Could not publish flat markdown')
        finally:
            translation.activate(cur_language)
        write_md_file(md_file_path, parsed, versioned)
        if '__building' in md_file_path:
            shutil.copy2(md_file_path, md_file_path.replace('__building', ''))


def _read_flat_markdown(md_file_path):
    with open(md_file_path, encoding='utf-8') as md_file_handler:
        md_flat_content = md_file_handler.read()
    return md_flat_content


@PublicatorRegistry.register('zip')
class ZipPublicator(Publicator):
    def publish(self, md_file_path, base_name, **kwargs):
        try:
            published_content_entity = self.get_published_content_entity(md_file_path)
            if published_content_entity is None:
                raise ValueError('published_content_entity is None')
            make_zip_file(published_content_entity)
            # no need to move zip file because it is already dumped to the public directory
        except (IOError, ValueError) as e:
            raise FailureDuringPublication('Zip could not be created', e)


@PublicatorRegistry.register('html')
class ZmarkdownHtmlPublicator(Publicator):

    def publish(self, md_file_path, base_name, **kwargs):
        md_flat_content = _read_flat_markdown(md_file_path)
        published_content_entity = self.get_published_content_entity(md_file_path)
        html_flat_content, *_ = render_markdown(md_flat_content, disable_ping=True,
                                                disable_js=True)
        html_file_path = path.splitext(md_file_path)[0] + '.html'
        if str(MD_PARSING_ERROR) in html_flat_content:
            logging.getLogger(self.__class__.__name__).error('HTML could not be rendered')
            return

        with open(html_file_path, mode='w', encoding='utf-8') as final_file:
            final_file.write(html_flat_content)
        shutil.move(html_file_path, str(
            Path(published_content_entity.get_extra_contents_directory(),
                 published_content_entity.content_public_slug + '.html')))


@PublicatorRegistry.register('pdf')
class ZMarkdownRebberLatexPublicator(Publicator):
    """
    Use zmarkdown and rebber stringifier to produce latex & pdf output.
    """
    def __init__(self, extension='.pdf', latex_classes=''):
        self.extension = extension
        self.doc_type = extension[1:]
        self.latex_classes = latex_classes

    def publish(self, md_file_path, base_name, **kwargs):
        md_flat_content = _read_flat_markdown(md_file_path)
        published_content_entity = self.get_published_content_entity(md_file_path)
        gallery_pk = published_content_entity.content.gallery.pk
        depth_to_size_map = {
            1: 'small',  # in fact this is an "empty" tutorial (i.e it is empty or has intro and/or conclusion)
            2: 'small',
            3: 'middle',
            4: 'big'
        }
        public_versionned_source = published_content_entity.content\
            .load_version(sha=published_content_entity.sha_public)
        base_directory = Path(base_name).parent
        image_dir = base_directory / 'images'
        with contextlib.suppress(FileExistsError):
            image_dir.mkdir(parents=True)
        if Path(settings.MEDIA_ROOT, 'galleries', str(gallery_pk)).exists():
            for image in Path(settings.MEDIA_ROOT, 'galleries', str(gallery_pk)).iterdir():
                with contextlib.suppress(OSError):
                    shutil.copy2(str(image.absolute()), str(image_dir))
        content_type = depth_to_size_map[public_versionned_source.get_tree_level()]
        if self.latex_classes:
            content_type += ', ' + self.latex_classes
        title = published_content_entity.title()
        authors = [a.username for a in published_content_entity.authors.all()]
        smileys_directory = SMILEYS_BASE_PATH

        licence = published_content_entity.content.licence.code
        licence_short = licence.replace('CC', '').strip().lower()
        licence_logo = licences.get(licence_short, False)
        if licence_logo:
            licence_url = 'https://creativecommons.org/licenses/{}/4.0/legalcode'.format(licence_short)
        else:
            licence = str(_('Tous droits réservés'))
            licence_logo = licences['copyright']
            licence_url = ''

        replacement_image_url = settings.MEDIA_ROOT
        if not replacement_image_url.endswith('/') and settings.MEDIA_URL.endswith('/'):
            replacement_image_url += '/'
        elif replacement_image_url.endswith('/') and not settings.MEDIA_URL.endswith('/'):
            replacement_image_url = replacement_image_url[:-1]
        content, __, messages = render_markdown(
            md_flat_content,
            output_format='texfile',
            # latex template arguments
            content_type=content_type,
            title=title,
            authors=authors,
            license=licence,
            license_directory=LICENSES_BASE_PATH,
            license_logo=licence_logo,
            license_url=licence_url,
            smileys_directory=smileys_directory,
            images_download_dir=str(base_directory / 'images'),
            local_url_to_local_path=[settings.MEDIA_URL, replacement_image_url]
        )
        if content == '' and messages:
            raise FailureDuringPublication('Markdown was not parsed due to {}'.format(messages))
        zmd_class_dir_path = Path(settings.ZDS_APP['content']['latex_template_repo'])
        if zmd_class_dir_path.exists() and zmd_class_dir_path.is_dir():
            with contextlib.suppress(FileExistsError):
                zmd_class_link = base_directory / 'zmdocument.cls'
                zmd_class_link.symlink_to(zmd_class_dir_path / 'zmdocument.cls')
                luatex_dir_link = base_directory / 'utf8.lua'
                luatex_dir_link.symlink_to(zmd_class_dir_path / 'utf8.lua', target_is_directory=True)
        true_latex_extension = '.'.join(self.extension.split('.')[:-1]) + '.tex'
        latex_file_path = base_name + true_latex_extension
        pdf_file_path = base_name + self.extension
        default_logo_original_path = Path(__file__).parent / '..' / '..' / 'assets' / 'images' / 'logo.png'
        with contextlib.suppress(FileExistsError):
            shutil.copy(str(default_logo_original_path), str(base_directory / 'default_logo.png'))
        with open(latex_file_path, mode='w', encoding='utf-8') as latex_file:
            latex_file.write(content)

        try:
            self.full_tex_compiler_call(latex_file_path, draftmode='-draftmode')
            self.full_tex_compiler_call(latex_file_path, draftmode='-draftmode')
            self.make_glossary(base_name.split('/')[-1], latex_file_path)
            self.full_tex_compiler_call(latex_file_path)
        except FailureDuringPublication:
            logging.getLogger(self.__class__.__name__).exception('could not publish %s', base_name + self.extension)
        else:
            shutil.copy2(latex_file_path, published_content_entity.get_extra_contents_directory())
            shutil.copy2(pdf_file_path, published_content_entity.get_extra_contents_directory())
            logging.info('published latex=%s, pdf=%s', published_content_entity.has_type('tex'),
                         published_content_entity.has_type(self.doc_type))

    def full_tex_compiler_call(self, latex_file, draftmode: str = ''):
        success_flag = self.tex_compiler(latex_file, draftmode)
        if not success_flag:
            handle_tex_compiler_error(latex_file, self.extension)

    def handle_makeglossaries_error(self, latex_file):
        with open(path.splitext(latex_file)[0] + '.log') as latex_log:
            errors = '\n'.join(filter(line for line in latex_log if 'fatal' in line.lower() or 'error' in line.lower()))
        raise FailureDuringPublication(errors)

    def tex_compiler(self, texfile, draftmode: str = ''):
        command = 'lualatex -shell-escape -interaction=nonstopmode {} {}'.format(draftmode, texfile)
        command_process = subprocess.Popen(command,
                                           shell=True, cwd=path.dirname(texfile),
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        command_process.communicate(timeout=120)

        with contextlib.suppress(ImportError):
            from raven import breadcrumbs
            breadcrumbs.record(message='lualatex call',
                               data=command,
                               type='cmd')

        pdf_file_path = path.splitext(texfile)[0] + self.extension
        return path.exists(pdf_file_path)

    def make_glossary(self, basename, texfile):
        command = 'makeglossaries {}'.format(basename)
        command_process = subprocess.Popen(command,
                                           shell=True, cwd=path.dirname(texfile),
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE)
        std_out, std_err = command_process.communicate()
        with contextlib.suppress(ImportError):
            from raven import breadcrumbs
            breadcrumbs.record(message='makeglossaries call',
                               data=command,
                               type='cmd')
        # TODO: check makeglossary exit codes to see if we can enhance error detection
        if 'fatal' not in std_out.decode('utf-8').lower() and 'fatal' not in std_err.decode('utf-8').lower():
            return True

        self.handle_makeglossaries_error(texfile)


def handle_tex_compiler_error(latex_file_path, ext):
    # TODO zmd: fix extension parsing
    log_file_path = latex_file_path[:-3] + 'log'
    errors = ['Error occured, log file {} not found.'.format(log_file_path)]
    with contextlib.suppress(FileNotFoundError, UnicodeDecodeError):
        with Path(log_file_path).open(encoding='utf-8') as latex_log:
            # TODO zmd: see if the lines we extract here contain enough info for debugging purpose
            print_context = 25
            lines = []
            relevant_line = -print_context
            for idx, line in enumerate(latex_log):
                if 'fatal' in line.lower() or 'error' in line.lower():
                    relevant_line = idx
                    lines.append(line)
                elif idx - relevant_line < print_context:
                    lines.append(line)

            errors = '\n'.join(lines)
    logger.debug('%s ext=%s', errors, ext)
    with contextlib.suppress(ImportError):
        from raven import breadcrumbs
        breadcrumbs.record(message='luatex call', data=errors, type='cmd')

    raise FailureDuringPublication(errors)


@PublicatorRegistry.register('epub')
class ZMarkdownEpubPublicator(Publicator):

    def publish(self, md_file_path, base_name, **kwargs):
        try:
            published_content_entity = self.get_published_content_entity(md_file_path)
            epub_file_path = Path(base_name + '.epub')
            logger.info('Start generating epub')
            build_ebook(published_content_entity,
                        path.dirname(md_file_path),
                        epub_file_path)
        except (IOError, OSError, requests.exceptions.HTTPError):
            raise FailureDuringPublication('Error while generating epub file.')
        else:
            logger.info(epub_file_path)
            epub_path = Path(published_content_entity.get_extra_contents_directory(), Path(epub_file_path.name))
            if epub_path.exists():
                os.remove(str(epub_path))
            if not epub_path.parent.exists():
                epub_path.parent.mkdir(parents=True)
            logger.info('created %s. moving it to %s', epub_file_path,
                        published_content_entity.get_extra_contents_directory())
            shutil.move(str(epub_file_path), published_content_entity.get_extra_contents_directory())


@PublicatorRegistry.register('watchdog')
class WatchdogFilePublicator(Publicator):
    def publish(self, md_file_path, base_name, silently_pass=True, **kwargs):
        if silently_pass:
            return
        published_content = self.get_published_content_entity(md_file_path)
        self.publish_from_published_content(published_content)

    def publish_from_published_content(self, published_content: PublishedContent):
        for requested_format in PublicatorRegistry.get_all_registered(['md', 'watchdog']):
            PublicationEvent.objects.create(state_of_processing='REQUESTED', published_object=published_content,
                                            format_requested=requested_format[0])


class FailureDuringPublication(Exception):
    """Exception raised if something goes wrong during publication process
    """
    def __init__(self, *args, **kwargs):
        super(FailureDuringPublication, self).__init__(*args, **kwargs)


def make_zip_file(published_content):
    """Create the zip archive extra content from the published content

    :param published_content: a PublishedContent object
    :return:
    """

    publishable = published_content.content
    # update SHA so that archive gets updated too
    publishable.sha_public = publishable.sha_draft
    file_path = path.join(published_content.get_extra_contents_directory(),
                          published_content.content_public_slug + '.zip')
    zip_file = zipfile.ZipFile(file_path, 'w')
    versioned = publishable.load_version(None, True)
    from zds.tutorialv2.views.contents import DownloadContent
    DownloadContent.insert_into_zip(zip_file, versioned.repository.commit(versioned.current_version).tree)
    zip_file.close()
    return file_path


def unpublish_content(db_object, moderator=None):
    """
    Remove the given content from the public view.

    .. note::
        This will send content_unpublished event.

    :param db_object: Database representation of the content
    :type db_object: PublishableContent
    :param moderator: the staff user who triggered the unpublish action.
    :type moderator: django.contrib.auth.models.User
    :return: ``True`` if unpublished, ``False`` otherwise
    :rtype: bool
    """

    from zds.tutorialv2.models.database import PublishedContent

    with contextlib.suppress(ObjectDoesNotExist, OSError):
        public_version = PublishedContent.objects.get(pk=db_object.public_version.pk)

        results = [
            content_unpublished.send(sender=reaction.__class__, instance=db_object, target=ContentReaction,
                                     moderator=moderator, user=None)
            for reaction in [ContentReaction.objects.filter(related_content=db_object).all()]
        ]
        logging.debug('Nb_messages=%d, messages=%s', len(results), results)
        # remove public_version:
        public_version.delete()
        update_params = {'public_version': None}

        if db_object.is_opinion:
            update_params['sha_public'] = None
            update_params['sha_picked'] = None
            update_params['pubdate'] = None

        db_object.update(**update_params)
        content_unpublished.send(sender=db_object.__class__, instance=db_object, target=db_object.__class__,
                                 moderator=moderator)
        # clean files
        old_path = public_version.get_prod_path()
        public_version.content.update(public_version=None, sha_public=None)
        if path.exists(old_path):
            shutil.rmtree(old_path)
        return True

    return False
