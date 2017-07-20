# coding: utf-8
import codecs
import copy
import logging
import os
from os.path import isdir, dirname
import shutil
import subprocess
import zipfile
from datetime import datetime
from textwrap import dedent

import six
from django.core.exceptions import ObjectDoesNotExist
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

from zds import settings
from zds.settings import ZDS_APP
from zds.tutorialv2.models.database import ContentReaction, PublishedContent
from zds.tutorialv2.signals import content_unpublished
from zds.tutorialv2.utils import retrieve_and_update_images_links
from zds.utils.templatetags.emarkdown import emarkdown, render_markdown, MD_PARSING_ERROR


def publish_content(db_object, versioned, is_major_update=True):
    """
    Publish a given content.

    .. note::
        create a manifest.json without the introduction and conclusion if not needed. Also remove the 'text' field
        of extracts.

    :param db_object: Database representation of the content
    :type db_object: PublishableContent
    :param versioned: version of the content to publish
    :type versioned: VersionedContent
    :param is_major_update: if set to `True`, will update the publication date
    :type is_major_update: bool
    :raise FailureDuringPublication: if something goes wrong
    :return: the published representation
    :rtype: zds.tutorialv2.models.database.PublishedContent
    """

    from zds.tutorialv2.models.database import PublishedContent

    if is_major_update:
        versioned.pubdate = datetime.now()

    # First write the files in a temporary directory: if anything goes wrong,
    # the last published version is not impacted !
    tmp_path = os.path.join(settings.ZDS_APP['content']['repo_public_path'], versioned.slug + '__building')

    if os.path.exists(tmp_path):
        shutil.rmtree(tmp_path)  # erase previous attempt, if any

    # render HTML:
    altered_version = copy.deepcopy(versioned)
    publish_container(db_object, tmp_path, altered_version)
    altered_version.dump_json(os.path.join(tmp_path, 'manifest.json'))

    # make room for 'extra contents'
    extra_contents_path = os.path.join(tmp_path, settings.ZDS_APP['content']['extra_contents_dirname'])
    os.makedirs(extra_contents_path)

    base_name = os.path.join(extra_contents_path, versioned.slug)

    # 1. markdown file (base for the others) :
    # If we come from a command line, we need to activate i18n, to have the date in the french language.
    cur_language = translation.get_language()
    versioned.pubdate = datetime.now()
    try:
        translation.activate(settings.LANGUAGE_CODE)
        parsed = render_to_string('tutorialv2/export/content.md', {'content': versioned})
    finally:
        translation.activate(cur_language)

    parsed_with_local_images = retrieve_and_update_images_links(parsed, directory=extra_contents_path)

    md_file_path = base_name + '.md'
    md_file = codecs.open(md_file_path, 'w', encoding='utf-8')
    try:
        md_file.write(parsed_with_local_images)
    except (UnicodeError, UnicodeEncodeError):
        raise FailureDuringPublication(_('Une erreur est survenue durant la génération du fichier markdown '
                                         'à télécharger, vérifiez le code markdown'))
    finally:
        md_file.close()

    pandoc_debug_str = ''
    if settings.ZDS_APP['content']['extra_content_generation_policy'] == 'SYNC':
        # ok, now we can really publish the thing !
        generate_exernal_content(base_name, extra_contents_path, md_file_path, pandoc_debug_str)
    elif settings.ZDS_APP['content']['extra_content_generation_policy'] == 'WATCHDOG':
        PublicatorRegistery.get('watchdog').publish(md_file_path, base_name, silently_pass=False)

    is_update = False

    if db_object.public_version:
        public_version = db_object.public_version
        is_update = True

        # the content have been published in the past, so clean old files !
        old_path = public_version.get_prod_path()
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
    public_version.save()
    public_version.char_count = public_version.get_char_count(md_file_path)

    for author in db_object.authors.all():
        public_version.authors.add(author)
    public_version.save()
    # move the stuffs into the good position
    if settings.ZDS_APP['content']['extra_content_generation_policy'] != 'WATCHDOG':
        shutil.move(tmp_path, public_version.get_prod_path())
    else:  # if we use watchdog, we use copy to get md and zip file in prod but everything else will be handled by
        # watchdog
        shutil.copytree(tmp_path, public_version.get_prod_path())
    # save public version
    if is_major_update or not is_update:
        public_version.publication_date = datetime.now()
    elif is_update:
        public_version.update_date = datetime.now()

    public_version.sha_public = versioned.current_version
    public_version.save()
    try:
        make_zip_file(public_version)
    except OSError:
        pass

    return public_version


def generate_exernal_content(base_name, extra_contents_path, md_file_path, pandoc_debug_str, overload_settings=False):
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
    for publicator_name, publicator in PublicatorRegistery.get_all_registered(excluded):
        try:
            publicator.publish(md_file_path, base_name, change_dir=extra_contents_path)
        except FailureDuringPublication:
            logging.getLogger(__name__).exception("Could not publish %s format from %s base.",
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


def _read_flat_markdown(md_file_path):
    with codecs.open(md_file_path, encoding='utf-8') as md_file_handler:
        md_flat_content = md_file_handler.read()
    return md_flat_content


@PublicatorRegistery.register('html')
class ZmarkdownHtmlPublicator(Publicator):

    def publish(self, md_file_path, base_name, **kwargs):
        md_flat_content = _read_flat_markdown(md_file_path)
        html_flat_content, _ = render_markdown(md_flat_content, disable_ping=True,
                                               disable_js=True)
        if str(MD_PARSING_ERROR) in html_flat_content:
            logging.getLogger(self.__class__.__name__).error('HTML was not rendered')
            return
        with codecs.open(md_file_path[:-2] + 'html', mode='w', encoding='utf-8') as final_file:
            final_file.write(html_flat_content)


@PublicatorRegistery.register('pdf')
class ZMarkdownRebberLatexPublicator(Publicator):
    def publish(self, md_file_path, base_name, **kwargs):
        md_flat_content = _read_flat_markdown(md_file_path)
        latex_content = render_markdown(md_flat_content, disable_ping=True,
                                        disable_js=True, is_latex=True)
        published_content_entity = PublishedContent.objects\
            .filter(must_redirect=False, content_public_slug=base_name)\
            .first()
        depth_to_size_map = {
            1: 'small',
            2: 'medium',
            3: 'big'
        }
        public_versionned_source = published_content_entity\
            .content\
            .load_version(public=True)
        content_size = depth_to_size_map[public_versionned_source.get_tree_level()]
        title = published_content_entity.title
        comma_separated_authors = ', '.join([a.username for a in published_content_entity.authors.all()])
        licence_type = published_content_entity.content.licence.title
        content = dedent("""
        \\documentclass[%s]{zmdocument}

        \\usepackage{blindtext}
        \\title{%s}
        \\author{%s}
        \\licence{CC-BY-NC-ND}

        \\smileysPath{./test-smileys}
        \\makeglossaries

        \\begin{document}
        \\maketitle
        \\tableofcontents

        %s
        \\end{document}
        """ % (content_size, title, comma_separated_authors, licence_type,
               latex_content))
        with codecs.open(md_file_path[:-2] + 'tex', mode='w', encoding='utf-8') as latex_file:
            latex_file.write(content)

        try:
            self.full_pdf_tex_call(latex_file)
            self.full_pdf_tex_call(latex_file)
            self.make_glossary(base_name, latex_file)
            self.full_pdf_tex_call(latex_file)
        except FailureDuringPublication:
            logging.getLogger(self.__class__.__name__).exception("could not publish %s", base_name)

    def full_pdf_tex_call(self, latex_file):
        success_flag = self.pdftex(latex_file)
        if not success_flag:
            self.handle_pdf_tex_error(latex_file)

    def handle_pdf_tex_error(self, latex_file):
        with codecs.open(latex_file[:-3] + "log") as latex_log:
            errors = '\n'.join(filter(line for line in latex_log if "fatal" in line.lower() or "error" in line.lower()))
        try:
            from raven import breadcrumbs
            breadcrumbs.record(message="pdftex call", data=errors, type="cmd")
        except ImportError:
            pass
        raise FailureDuringPublication(errors)

    def handle_makeglossaries_error(self, latex_file):
        with codecs.open(latex_file[:-3] + "log") as latex_log:
            errors = '\n'.join(filter(line for line in latex_log if "fatal" in line.lower() or "error" in line.lower()))
        raise FailureDuringPublication(errors)

    def pdftex(self, texfile):
        new_err = six.StringIO()

        exit_code = subprocess.call('pdflatex -draftmode -shell-escape -interaction=nonstopmode ' + texfile,
                                    shell=True, cwd=os.path.dirname(texfile), stderr=new_err)
        try:
            from raven import breadcrumbs
            breadcrumbs.record(message="pdftex call",
                               data='pdflatex -draftmode -shell-escape -interaction=nonstopmode ' + texfile,
                               type="cmd")
        except ImportError:
            pass

        if exit_code == 0 and os.exists(texfile[:-3] + "pdf"):
            # success
            return True
        self.handle_pdf_tex_error(new_err.getvalue())

    def make_glossary(self, basename, texfile):
        new_err = six.StringIO()
        exit_code = subprocess.call('makeglossaries ' + basename,
                                    shell=True, cwd=os.path.dirname(texfile), stderr=new_err)
        try:
            from raven import breadcrumbs
            breadcrumbs.record(message="makeglossaries call",
                               data='makeglossaries ' + basename,
                               type="cmd")
        except ImportError:
            pass
        if exit_code == 0:
            return True
        else:
            self.handle_makeglossaries_error(texfile)


@PublicatorRegistery.register('watchdog', settings.ZDS_APP['content']['extra_content_watchdog_dir'])
class WatchdogFilePublicator(Publicator):
    """
    Just create a meta data file for watchdog
    """
    def __init__(self, watched_dir):
        self.watched_directory = watched_dir
        if not isdir(self.watched_directory):
            os.mkdir(self.watched_directory)
        self.__logger = logging.getLogger(__name__ + '.' + self.__class__.__name__)

    def publish(self, md_file_path, base_name, silently_pass=True, **kwargs):
        if silently_pass:
            return
        fname = base_name.replace(dirname(base_name), self.watched_directory)
        with codecs.open(fname, 'w', encoding='utf-8') as w_file:
            w_file.write(';'.join([base_name, md_file_path]))
        self.__logger.debug('Registered {} for generation'.format(md_file_path))


class FailureDuringPublication(Exception):
    """Exception raised if something goes wrong during publication process
    """

    def __init__(self, *args, **kwargs):
        super(FailureDuringPublication, self).__init__(*args, **kwargs)


def publish_container(db_object, base_dir, container):
    """ 'Publish' a given container, in a recursive way

    :param db_object: database representation of the content
    :type db_object: PublishableContent
    :param base_dir: directory of the top container
    :type base_dir: str
    :param container: a given container
    :type container: Container
    :raise FailureDuringPublication: if anything goes wrong
    """

    from zds.tutorialv2.models.versioned import Container

    if not isinstance(container, Container):
        raise FailureDuringPublication(_("Le conteneur n'en est pas un !"))

    template = 'tutorialv2/export/chapter.html'

    # jsFiddle support
    if db_object.js_support:
        is_js = 'js'
    else:
        is_js = ''

    current_dir = os.path.dirname(os.path.join(base_dir, container.get_prod_path(relative=True)))

    if not os.path.isdir(current_dir):
        os.makedirs(current_dir)

    if container.has_extracts():  # the container can be rendered in one template
        parsed = render_to_string(template, {'container': container, 'is_js': is_js})
        f = codecs.open(os.path.join(base_dir, container.get_prod_path(relative=True)), 'w', encoding='utf-8')

        try:
            f.write(parsed)
        except (UnicodeError, UnicodeEncodeError):
            raise FailureDuringPublication(
                _('Une erreur est survenue durant la publication de « {} », vérifiez le code markdown')
                .format(container.title))

        f.close()

        for extract in container.children:
            extract.text = None

        container.introduction = None
        container.conclusion = None

    else:  # separate render of introduction and conclusion

        current_dir = os.path.join(base_dir, container.get_prod_path(relative=True))  # create subdirectory

        if not os.path.isdir(current_dir):
            os.makedirs(current_dir)

        if container.introduction:
            path = os.path.join(container.get_prod_path(relative=True), 'introduction.html')
            f = codecs.open(os.path.join(base_dir, path), 'w', encoding='utf-8')

            try:
                f.write(emarkdown(container.get_introduction(), db_object.js_support))
            except (UnicodeError, UnicodeEncodeError):
                raise FailureDuringPublication(
                    _("Une erreur est survenue durant la publication de l'introduction de « {} »,"
                      ' vérifiez le code markdown').format(container.title))

            container.introduction = path

        if container.conclusion:
            path = os.path.join(container.get_prod_path(relative=True), 'conclusion.html')
            f = codecs.open(os.path.join(base_dir, path), 'w', encoding='utf-8')

            try:
                f.write(emarkdown(container.get_conclusion(), db_object.js_support))
            except (UnicodeError, UnicodeEncodeError):
                raise FailureDuringPublication(
                    _('Une erreur est survenue durant la publication de la conclusion de « {} »,'
                      ' vérifiez le code markdown').format(container.title))

            container.conclusion = path

        for child in container.children:
            publish_container(db_object, base_dir, child)


def make_zip_file(published_content):
    """Create the zip archive extra content from the published content

    :param published_content: a PublishedContent object
    :return:
    """

    publishable = published_content.content
    publishable.sha_public = publishable.sha_draft  # ensure sha update so that archive is updated to
    path = os.path.join(published_content.get_extra_contents_directory(),
                        published_content.content_public_slug + '.zip')
    zip_file = zipfile.ZipFile(path, 'w')
    versioned = publishable.load_version(None, True)
    from zds.tutorialv2.views.contents import DownloadContent
    DownloadContent.insert_into_zip(zip_file, versioned.repository.commit(versioned.current_version).tree)
    zip_file.close()


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

        if os.path.exists(old_path):
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
