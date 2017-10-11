# coding: utf-8
import contextlib
import copy
import logging
import shutil
import subprocess
import zipfile
from datetime import datetime
from os import makedirs, mkdir, path
from pathlib import Path

from django.core.exceptions import ObjectDoesNotExist
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

from django.conf import settings
from zds.tutorialv2.epub_utils import build_ebook
from zds.tutorialv2.models.database import ContentReaction, PublishedContent
from zds.tutorialv2.publish_container import publish_container
from zds.tutorialv2.signals import content_unpublished
from zds.tutorialv2.utils import retrieve_and_update_images_links
from zds.utils.templatetags.emarkdown import render_markdown, MD_PARSING_ERROR
from zds.utils.templatetags.smileys_def import SMILEYS_BASE_PATH

logger = logging.getLogger(__name__)


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
    versioned.pubdate = datetime.now()
    try:
        translation.activate(settings.LANGUAGE_CODE)
        parsed = render_to_string('tutorialv2/export/content.md', {'content': versioned})
    finally:
        translation.activate(cur_language)

    parsed_with_local_images = retrieve_and_update_images_links(parsed, directory=build_extra_contents_path)

    md_file_path = base_name + '.md'
    with open(md_file_path, 'w', encoding='utf-8')as md_file:
        try:
            md_file.write(parsed_with_local_images)
        except UnicodeError:
            logger.error('Could not encode %s in UTF-8, publication aborted', versioned.title)
            raise FailureDuringPublication(_('Une erreur est survenue durant la génération du fichier markdown '
                                             'à télécharger, vérifiez le code markdown'))

    is_update = False

    if db_object.public_version:
        public_version = db_object.public_version
        is_update = True

        # the content have been published in the past, so clean old files !
        old_path = public_version.get_prod_path()
        logging.getLogger(__name__).debug('erase ' + old_path)
        shutil.rmtree(old_path)

        # if the slug change, instead of using the same object, a new one will be created
        if versioned.slug != public_version.content_public_slug:
            public_version.must_redirect = True  # set redirection
            publication_date = public_version.publication_date
            public_version.save()
            db_object.public_version = PublishedContent()
            public_version = db_object.public_version

            # if content have already been published, keep publication date !
            public_version.publication_date = publication_date

    else:
        public_version = PublishedContent()

    # make the new public version
    public_version.content_public_slug = versioned.slug
    public_version.content_type = versioned.type
    public_version.content_pk = db_object.pk
    public_version.content = db_object
    public_version.must_reindex = True
    # TODO: use update instead of save !
    public_version.save()
    public_version.char_count = public_version.get_char_count(md_file_path)

    for author in db_object.authors.all():
        public_version.authors.add(author)
    public_version.save()
    # save public version
    if is_major_update or not is_update:
        public_version.publication_date = datetime.now()
    elif is_update:
        public_version.update_date = datetime.now()

    public_version.sha_public = versioned.current_version
    # TODO: use update
    public_version.save()

    # this puts the manifest.json and base json file on the prod path.
    shutil.rmtree(public_version.get_prod_path(), ignore_errors=True)
    shutil.copytree(tmp_path, public_version.get_prod_path())
    if settings.ZDS_APP['content']['extra_content_generation_policy'] == 'SYNC':
        # ok, now we can really publish the thing!
        generate_external_content(base_name, build_extra_contents_path, md_file_path)
    elif settings.ZDS_APP['content']['extra_content_generation_policy'] == 'WATCHDOG':
        PublicatorRegistery.get('watchdog').publish(md_file_path, base_name, silently_pass=False)
    db_object.sha_public = versioned.current_version
    return public_version


def generate_external_content(base_name, extra_contents_path, md_file_path, overload_settings=False):
    """
    generate all static file that allow offline access to content

    :param base_name: base nae of file (without extension)
    :param extra_contents_path: internal directory where all files will be pushed
    :param md_file_path: bundled markdown file path
    :param pandoc_debug_str: *specific to pandoc publication : avoid subprocess to be errored*
    :param overload_settings: this option force the function to generate all registered formats even when settings \
    ask for PDF not to be published
    :return:
    """
    excluded = []
    if not settings.ZDS_APP['content']['build_pdf_when_published'] and not overload_settings:
        excluded.append('pdf')
    # TODO: exclude watchdog
    for publicator_name, publicator in PublicatorRegistery.get_all_registered(excluded):
        try:
            publicator.publish(md_file_path, base_name, change_dir=extra_contents_path)
        except FailureDuringPublication:
            logging.getLogger(__name__).exception('Could not publish %s format from %s base.',
                                                  publicator_name, md_file_path)


class PublicatorRegistery:
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
        for key, value in list(cls.registry.items()):
            if key not in exclude:
                yield key, value

    @classmethod
    def unregister(cls, name):
        """
        Remove Publicator registered at name if exists, run silently otherwise.

        :param name: publicator name.
        """
        if name in cls.registry:
            del cls.registry[name]

    @classmethod
    def get(cls, name):
        """
        get publicator with required name.

        :param name:
        :return: the wanted publicator
        :rtype: Publicator
        :raise KeyError: if name is not registered
        """
        return cls.registry[name]


class Publicator:
    """
    Publicator base object, all methods must be overridden
    """

    def publish(self, md_file_path, base_name, **kwargs):
        """called function to generate a content export

        :param md_file_path: base markdown file path
        :param base_name: file name without extension
        :param kwargs: other publicator dependant options
        """
        raise NotImplemented()

    def get_published_content_entity(self, md_file_path):
        content_slug = PublishedContent.get_slug_from_file_path(md_file_path)
        published_content_entity = PublishedContent.objects \
            .filter(must_redirect=False, content_public_slug=content_slug) \
            .first()
        return published_content_entity


def _read_flat_markdown(md_file_path):
    with open(md_file_path, encoding='utf-8') as md_file_handler:
        md_flat_content = md_file_handler.read()
    return md_flat_content


@PublicatorRegistery.register('zip')
class ZipPublicator(Publicator):
    def publish(self, md_file_path, base_name, **kwargs):
        try:
            published_content_entity = self.get_published_content_entity(md_file_path)
            if published_content_entity is None:
                raise ValueError('published_content_entity is None')
            make_zip_file(published_content_entity)
            # for zip no need to move it because this is already dumped in the public directory
        except (IOError, ValueError) as e:
            raise FailureDuringPublication('Zip could not be created', e)


@PublicatorRegistery.register('html')
class ZmarkdownHtmlPublicator(Publicator):

    def publish(self, md_file_path, base_name, **kwargs):
        md_flat_content = _read_flat_markdown(md_file_path)
        published_content_entity = self.get_published_content_entity(md_file_path)
        html_flat_content, _ = render_markdown(md_flat_content, disable_ping=True,
                                               disable_js=True)
        html_file_path = path.splitext(md_file_path)[0] + '.html'
        if str(MD_PARSING_ERROR) in html_flat_content:
            logging.getLogger(self.__class__.__name__).error('HTML was not rendered')
            return
        # TODO zmd: fix extension parsing
        with open(html_file_path, mode='w', encoding='utf-8') as final_file:
            final_file.write(html_flat_content)
        shutil.move(html_file_path, published_content_entity.get_extra_contents_directory())


@PublicatorRegistery.register('pdf')
class ZMarkdownRebberLatexPublicator(Publicator):
    """
    use zmarkdown and rebber stringifier to produce latex & pdf output.
    """
    def publish(self, md_file_path, base_name, **kwargs):
        md_flat_content = _read_flat_markdown(md_file_path)
        published_content_entity = self.get_published_content_entity(md_file_path)
        depth_to_size_map = {
            1: 'small',  # in fact this is an "empty" tutorial (i.e it is empty or has intro and/or conclusion)
            2: 'small',
            3: 'medium',
            4: 'big'
        }
        public_versionned_source = published_content_entity.content\
            .load_version(sha=published_content_entity.sha_public)
        content_type = depth_to_size_map[public_versionned_source.get_tree_level()]
        title = published_content_entity.title()
        authors = [a.username for a in published_content_entity.authors.all()]
        smileys_directory = SMILEYS_BASE_PATH
        licence = published_content_entity.content.licence.title
        toc = True

        content, _ = render_markdown(
            md_flat_content,
            disable_ping=True,
            disable_js=True,
            to_latex_document=True,
            # latex template arguments
            contentType=content_type,
            title=title,
            authors=authors,
            license=licence,
            smileysDirectory=smileys_directory,
            toc=toc
        )

        latex_file_path = base_name + '.tex'
        pdf_file_path = base_name + '.pdf'
        with open(latex_file_path, mode='w', encoding='utf-8') as latex_file:
            latex_file.write(content)

        try:
            self.full_pdftex_call(latex_file_path)
            self.full_pdftex_call(latex_file_path)
            self.make_glossary(base_name.split('/')[-1], latex_file_path)
            self.full_pdftex_call(latex_file_path)
        except FailureDuringPublication:
            logging.getLogger(self.__class__.__name__).exception('could not publish %s', base_name)
        else:
            shutil.copy2(latex_file_path, published_content_entity.get_extra_contents_directory())
            shutil.copy2(pdf_file_path, published_content_entity.get_extra_contents_directory())
            logging.info('published latex=%s, pdf=%s', published_content_entity.has_type('tex'),
                         published_content_entity.has_type('pdf'))

    def full_pdftex_call(self, latex_file):
        success_flag = self.pdftex(latex_file)
        if not success_flag:
            handle_pdftex_error(latex_file)

    def handle_makeglossaries_error(self, latex_file):
        with open(path.splitext(latex_file)[0] + '.log') as latex_log:
            errors = '\n'.join(filter(line for line in latex_log if 'fatal' in line.lower() or 'error' in line.lower()))
        raise FailureDuringPublication(errors)

    def pdftex(self, texfile):
        command = 'lualatex -shell-escape -interaction=nonstopmode {}'.format(texfile)
        # TODO zmd: make sure the shell spawned here has venv in its path, needed to shell-escape into Pygments
        command_process = subprocess.Popen(command,
                                           shell=True, cwd=path.dirname(texfile),
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        command_process.communicate()

        try:
            from raven import breadcrumbs
            breadcrumbs.record(message='lualatex call',
                               data=command,
                               type='cmd')
        except ImportError:
            pass

        pdf_file_path = path.splitext(texfile)[0] + '.pdf'
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


def handle_pdftex_error(latex_file_path):
    # TODO zmd: fix extension parsing
    log_file_path = latex_file_path[:-3] + 'log'
    errors = ['Error occured, log file {} not found.'.format(log_file_path)]
    with contextlib.suppress(FileNotFoundError):
        with Path(log_file_path).open(encoding='utf-8') as latex_log:
            # TODO zmd: see if the lines we extract here contain enough info for debugging purpose
            errors = '\n'.join([line for line in latex_log if 'fatal' in line.lower() or 'error' in line.lower()])
    logger.debug('%s', errors)
    with contextlib.suppress(ImportError):
        from raven import breadcrumbs
        breadcrumbs.record(message='luatex call', data=errors, type='cmd')

    raise FailureDuringPublication(errors)


@PublicatorRegistery.register('epub')
class ZMarkdownEpubPublicator(Publicator):
    def publish(self, md_file_path, base_name, **kwargs):
        try:
            published_content_entity = self.get_published_content_entity(md_file_path)
            epub_file_path = Path(path.splitext(md_file_path)[0] + '.epub')
            build_ebook(published_content_entity,
                        path.dirname(md_file_path),
                        epub_file_path)
        except (IOError, OSError):
            raise FailureDuringPublication('Error while generating epub file.')
        else:
            shutil.move(str(epub_file_path), published_content_entity.get_extra_contents_directory())


@PublicatorRegistery.register('watchdog', settings.ZDS_APP['content']['extra_content_watchdog_dir'])
class WatchdogFilePublicator(Publicator):
    """
    Just create a meta data file for watchdog
    """
    def __init__(self, watched_dir):
        self.watched_directory = watched_dir
        if not path.isdir(self.watched_directory):
            mkdir(self.watched_directory)
        self.__logger = logging.getLogger(__name__ + '.' + self.__class__.__name__)

    def publish(self, md_file_path, base_name, silently_pass=True, **kwargs):
        if silently_pass:
            return
        filename = base_name.replace(path.dirname(base_name), self.watched_directory)
        with open(filename, 'w', encoding='utf-8') as w_file:
            w_file.write(';'.join([base_name, md_file_path]))
        self.__logger.debug('Registered {} for generation'.format(md_file_path))


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
    # TODO zmd: fix extension parsing
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
    :return: ``True`` if unpublished, ``False`` otherwise
    :rtype: bool
    """

    from zds.tutorialv2.models.database import PublishedContent

    try:
        public_version = PublishedContent.objects.get(pk=db_object.public_version.pk)

        # clean files
        old_path = public_version.get_prod_path()

        if path.exists(old_path):
            shutil.rmtree(old_path)

        list([
            content_unpublished.send(sender=reaction.__class__, instance=reaction)
            for reaction in [ContentReaction.objects.filter(related_content=db_object).all()]
        ])

        # remove public_version:
        public_version.delete()
        update_params = {}
        update_params['public_version'] = None

        if db_object.is_opinion:
            update_params['sha_public'] = None
            update_params['sha_picked'] = None
            update_params['pubdate'] = None

        db_object.update(**update_params)
        content_unpublished.send(sender=db_object.__class__, instance=db_object)

        return True

    except (ObjectDoesNotExist, OSError):
        pass

    return False
