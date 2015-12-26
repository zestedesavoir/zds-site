import codecs
import copy
import os
import shutil
import subprocess
from datetime import datetime

from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

from zds import settings
from zds.settings import ZDS_APP
from zds.tutorialv2.utils import publish_container, retrieve_and_update_images_links, FailureDuringPublication, \
    make_zip_file


def publish_content(db_object, versioned, is_major_update=True):
    """Publish a given content.

    Note: create a manifest.json without the introduction and conclusion if not needed. Also remove the "text" field
    of extracts.

    :param db_object: Database representation of the content
    :type db_object: PublishableContent
    :param versioned: version of the content to publish
    :type versioned: VersionedContent
    :param is_major_update: if set to `True`, will update the publication date
    :type is_major_update: bool
    :raise FailureDuringPublication: if something goes wrong
    :return: the published representation
    :rtype: zds.tutorialv2.models.models_database.PublishedContent
    """

    from zds.tutorialv2.models.models_database import PublishedContent

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

    # make room for "extra contents"
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
        raise FailureDuringPublication(_(u'Une erreur est survenue durant la génération du fichier markdown '
                                         u'à télécharger, vérifiez le code markdown'))
    md_file.close()

    pandoc_debug_str = ""
    if settings.PANDOC_LOG_STATE:
        pandoc_debug_str = " 2>&1 | tee -a " + settings.PANDOC_LOG

    generate_exernal_content(base_name, extra_contents_path, md_file_path, pandoc_debug_str)# ok, now we can really publish the thing !
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
    for author in db_object.authors.all():
        public_version.authors.add(author)
    public_version.save()
    # move the stuffs into the good position
    shutil.move(tmp_path, public_version.get_prod_path())

    # save public version
    if is_major_update or not is_update:
        public_version.publication_date = datetime.now()
    elif is_update:
        public_version.update_date = datetime.now()

    public_version.sha_public = versioned.current_version
    public_version.save()
    try:
        make_zip_file(public_version)
    except IOError:
        pass

    return public_version


def generate_exernal_content(base_name, extra_contents_path, md_file_path, pandoc_debug_str, overload_settings=False):
    """generate all static file that allow offline access to content

    :param base_name: base nae of file (without extension)
    :param extra_contents_path: internal directory where all files will be pushed
    :param md_file_path: bundled markdown file path
    :param pandoc_debug_str: *specific to pandoc publication : avoid subprocess to be errored*
    :param overload_settings: this option force the function to generate all registered formats even when settings
    ask for PDF not to be published
    :return:
    """
    excluded = []
    if ZDS_APP['content']['build_pdf_when_published'] and not overload_settings:
        excluded.append("pdf")
    for _, publicator in PublicatorRegistery.get_all_registered(excluded):

        publicator.publish(md_file_path, base_name, change_dir=extra_contents_path, pandoc_debug_str=pandoc_debug_str)


class PublicatorRegistery:
    registry = {}

    @classmethod
    def register(cls,  publicator_name, *args):
        def decorated(func):
            cls.registry[publicator_name] = func(args)
            return func
        return decorated


    @classmethod
    def get_all_registered(cls, exclude=None):
        if exclude is None:
            exclude = []
        for key, value in cls.registry.items():
            if key not in exclude:
                yield key, value


class Publicator:
    def publish(self, md_file_path, base_name, **kwargs):
        raise NotImplemented()


@PublicatorRegistery.register("pdf", settings.PANDOC_LOC, "pdf", settings.PANDOC_PDF_PARAM)
@PublicatorRegistery.register("epub", settings.PANDOC_LOC, "epub")
@PublicatorRegistery.register("html", settings.PANDOC_LOC, "html")
class PandocPublicator:
    def __init__(self, pandoc_loc, _format, pandoc_pdf_param=None):
        self.pandoc_loc = pandoc_loc
        self.pandoc_pdf_param = pandoc_pdf_param
        self.format = _format

    def publish(self, md_file_path, base_name, change_dir=".", pandoc_debug_str="", **kwargs):
        if self.pandoc_pdf_param:
            subprocess.call(
                self.pandoc_loc + "pandoc " + self.pandoc_pdf_param + " " + md_file_path + " -o " +
                base_name + "." + self.format + " " + pandoc_debug_str,
                shell=True,
                cwd=change_dir)
        else:
            subprocess.call(
                self.pandoc_loc + "pandoc -s -S --toc " + md_file_path + " -o " +
                base_name + "." + self.format + " " + pandoc_debug_str,
                shell=True,
                cwd=change_dir)