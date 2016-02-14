# coding: utf-8
from datetime import datetime
import json as json_reader
import zipfile
import shutil
import tempfile
import time

import re
from PIL import Image as ImagePIL
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.utils.encoding import smart_text
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import string_concat
from django.views.generic import FormView, DeleteView, RedirectView
from easy_thumbnails.files import get_thumbnailer
from git import BadName, BadObject, GitCommandError, objects
import os
from zds.forum.models import Forum
from zds.gallery.models import Gallery, UserGallery, Image, GALLERY_WRITE
from zds.member.decorator import LoggedWithReadWriteHability, LoginRequiredMixin, PermissionRequiredMixin
from zds.member.models import Profile
from zds.tutorialv2.forms import ContentForm, JsFiddleActivationForm, AskValidationForm, AcceptValidationForm, \
    RejectValidationForm, RevokeValidationForm, WarnTypoForm, ImportContentForm, ImportNewContentForm, ContainerForm, \
    ExtractForm, BetaForm, MoveElementForm, AuthorForm, CancelValidationForm
from zds.tutorialv2.mixins import SingleContentDetailViewMixin, SingleContentFormViewMixin, SingleContentViewMixin, \
    SingleContentDownloadViewMixin, SingleContentPostMixin
from zds.tutorialv2.models import TYPE_CHOICES_DICT
from zds.tutorialv2.models.models_database import PublishableContent, Validation
from zds.tutorialv2.models.models_versioned import Container, Extract
from zds.tutorialv2.utils import search_container_or_404, get_target_tagged_tree, search_extract_or_404, \
    try_adopt_new_child, TooDeepContainerError, BadManifestError, get_content_from_json, init_new_repo, \
    default_slug_pool, BadArchiveError, InvalidSlugError
from uuslug import slugify
from zds.utils.forums import send_post, lock_topic, create_topic, unlock_topic
from zds.forum.models import Topic, follow, mark_read
from zds.utils.models import Tag, HelpWriting
from zds.utils.mps import send_mp
from zds.utils.paginator import ZdSPagingListView
from zds.utils.models import Licence


class RedirectOldBetaTuto(RedirectView):
    """
    allows to redirect /tutoriels/beta/old_pk/slug to /contenus/beta/new_pk/slug
    """
    permanent = True

    def get_redirect_url(self, **kwargs):
        tutorial = PublishableContent.objects.filter(type="TUTORIAL", old_pk=kwargs["pk"]).first()
        if tutorial is None or tutorial.sha_beta is None or tutorial.sha_beta == "":
            raise Http404(_(u"Aucun contenu en bêta trouvé avec cet ancien identifiant."))
        return tutorial.get_absolute_url_beta()


class CreateContent(LoggedWithReadWriteHability, FormView):
    template_name = 'tutorialv2/create/content.html'
    model = PublishableContent
    form_class = ContentForm
    content = None
    created_content_type = "TUTORIAL"

    def get_form(self, form_class):
        form = super(CreateContent, self).get_form(form_class)
        form.initial["type"] = self.created_content_type
        form.initial['licence'] = Licence.objects.get(pk=settings.ZDS_APP['content']['default_licence_pk'])
        return form

    def form_valid(self, form):
        # create the object:
        self.content = PublishableContent()
        self.content.title = form.cleaned_data['title']
        self.content.description = form.cleaned_data["description"]
        self.content.type = form.cleaned_data["type"]
        self.content.licence = form.cleaned_data["licence"]

        self.content.creation_date = datetime.now()

        # Creating the gallery
        gal = Gallery()
        gal.title = form.cleaned_data["title"]
        gal.slug = slugify(form.cleaned_data["title"])
        gal.pubdate = datetime.now()
        gal.save()

        # Attach user to gallery
        userg = UserGallery()
        userg.gallery = gal
        userg.mode = "W"  # write mode
        userg.user = self.request.user
        userg.save()
        self.content.gallery = gal

        # create image:
        if "image" in self.request.FILES:
            img = Image()
            img.physical = self.request.FILES["image"]
            img.gallery = gal
            img.title = self.request.FILES["image"]
            img.slug = slugify(self.request.FILES["image"].name)
            img.pubdate = datetime.now()
            img.save()
            self.content.image = img

        self.content.save()

        # We need to save the tutorial before changing its author list since it's a many-to-many relationship
        self.content.authors.add(self.request.user)

        # Add subcategories on tutorial
        for subcat in form.cleaned_data["subcategory"]:
            self.content.subcategory.add(subcat)

        # Add helps if needed
        for helpwriting in form.cleaned_data["helps"]:
            self.content.helps.add(helpwriting)

        self.content.save()

        # create a new repo :
        init_new_repo(self.content,
                      form.cleaned_data['introduction'],
                      form.cleaned_data['conclusion'],
                      form.cleaned_data['msg_commit'])

        return super(CreateContent, self).form_valid(form)

    def get_success_url(self):
        return reverse('content:view', args=[self.content.pk, self.content.slug])


class DisplayContent(LoginRequiredMixin, SingleContentDetailViewMixin):
    """Base class that can show any content in any state"""

    model = PublishableContent
    template_name = 'tutorialv2/view/content.html'
    must_be_author = False  # as in beta state anyone that is logged can access to it
    only_draft_version = False

    def get_forms(self, context):
        """get all the auxiliary forms about validation, js fiddle..."""

        validation = Validation.objects.filter(content__pk=self.object.pk) \
            .order_by("-date_proposition") \
            .first()

        form_js = JsFiddleActivationForm(initial={"js_support": self.object.js_support})

        context["formAskValidation"] = AskValidationForm(
            content=self.versioned_object, initial={"source": self.object.source, 'version': self.sha})

        if validation:
            context["formValid"] = AcceptValidationForm(validation, initial={"source": self.object.source})
            context["formReject"] = RejectValidationForm(validation)
            context["formCancel"] = CancelValidationForm(validation)

        if self.versioned_object.sha_public:
            context['formRevokeValidation'] = RevokeValidationForm(
                self.versioned_object, initial={'version': self.versioned_object.sha_public})

        if self.versioned_object.is_beta:
            context['formWarnTypo'] = WarnTypoForm(self.versioned_object, self.versioned_object, public=False)

        context["validation"] = validation
        context["formJs"] = form_js

    def get_context_data(self, **kwargs):
        context = super(DisplayContent, self).get_context_data(**kwargs)

        # check whether this tuto support js fiddle
        if self.object.js_support:
            is_js = "js"
        else:
            is_js = ""
        context["is_js"] = is_js

        self.get_forms(context)

        context['gallery'] = self.object.gallery
        context['public_content_object'] = self.public_content_object

        return context


class DisplayBetaContent(DisplayContent):
    """View to get the beta version of a content"""

    sha = None

    def get_object(self, queryset=None):
        """rewritten to ensure that the version is set to beta, raise Http404 if there is no such version"""
        obj = super(DisplayBetaContent, self).get_object(queryset)

        if not obj.sha_beta or obj.sha_beta == '':
            raise Http404(_(u"Aucune bêta n'existe pour ce contenu."))

        else:
            self.sha = obj.sha_beta

        # make the slug always right in URLs resolution:
        if 'slug' in self.kwargs:
            self.kwargs['slug'] = obj.slug

        return obj


class EditContent(LoggedWithReadWriteHability, SingleContentFormViewMixin):
    template_name = 'tutorialv2/edit/content.html'
    model = PublishableContent
    form_class = ContentForm

    def get_initial(self):
        """rewrite function to pre-populate form"""
        initial = super(EditContent, self).get_initial()
        versioned = self.versioned_object

        initial['title'] = versioned.title
        initial['description'] = versioned.description
        initial['type'] = versioned.type
        initial['introduction'] = versioned.get_introduction()
        initial['conclusion'] = versioned.get_conclusion()
        initial['licence'] = versioned.licence
        initial['subcategory'] = self.object.subcategory.all()
        initial['helps'] = self.object.helps.all()

        initial['last_hash'] = versioned.compute_hash()

        return initial

    def get_context_data(self, **kwargs):
        context = super(EditContent, self).get_context_data(**kwargs)

        context['gallery'] = self.object.gallery

        return context

    def form_valid(self, form):
        versioned = self.versioned_object
        publishable = self.object

        # check if content has changed:
        current_hash = versioned.compute_hash()
        if current_hash != form.cleaned_data['last_hash']:
            data = form.data.copy()
            data['last_hash'] = current_hash
            data['introduction'] = versioned.get_introduction()
            data['conclusion'] = versioned.get_conclusion()
            form.data = data
            messages.error(self.request, _(u'Une nouvelle version a été postée avant que vous ne validiez.'))
            return self.form_invalid(form)

        # first, update DB (in order to get a new slug if needed)
        publishable.title = form.cleaned_data['title']
        publishable.description = form.cleaned_data["description"]
        publishable.licence = form.cleaned_data["licence"]

        publishable.update_date = datetime.now()

        # update gallery and image:
        gal = Gallery.objects.filter(pk=publishable.gallery.pk)
        gal.update(title=publishable.title)
        gal.update(slug=slugify(publishable.title))
        gal.update(update=datetime.now())

        if "image" in self.request.FILES:
            img = Image()
            img.physical = self.request.FILES["image"]
            img.gallery = publishable.gallery
            img.title = self.request.FILES["image"]
            img.slug = slugify(self.request.FILES["image"].name)
            img.pubdate = datetime.now()
            img.save()
            publishable.image = img

        publishable.save()

        # now, update the versioned information
        versioned.description = form.cleaned_data['description']
        versioned.licence = form.cleaned_data['licence']

        sha = versioned.repo_update_top_container(form.cleaned_data['title'],
                                                  publishable.slug,
                                                  form.cleaned_data['introduction'],
                                                  form.cleaned_data['conclusion'],
                                                  form.cleaned_data['msg_commit'])

        # update relationships :
        publishable.sha_draft = sha

        publishable.subcategory.clear()
        for subcat in form.cleaned_data["subcategory"]:
            publishable.subcategory.add(subcat)

        publishable.helps.clear()
        for help in form.cleaned_data["helps"]:
            publishable.helps.add(help)

        publishable.save()

        self.success_url = reverse('content:view', args=[publishable.pk, publishable.slug])
        return super(EditContent, self).form_valid(form)


class DeleteContent(LoggedWithReadWriteHability, SingleContentViewMixin, DeleteView):
    model = PublishableContent
    template_name = None
    http_method_names = [u'delete', u'post']
    object = None
    authorized_for_staff = False  # deletion is creator's privilege

    @method_decorator(transaction.atomic)
    def dispatch(self, *args, **kwargs):
        return super(DeleteContent, self).dispatch(*args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """rewrite delete() function to ensure repository deletion"""

        self.object = self.get_object()
        object_type = self.object.type.lower()

        _type = _(u'ce tutoriel')
        if self.object.type == 'ARTICLE':
            _type = _(u'cet article')

        if self.object.authors.count() > 1:  # if more than one author, just remove author from list
            RemoveAuthorFromContent.remove_author(self.object, self.request.user)
            messages.success(self.request, _(u'Vous avez quitté la rédaction de {}.').format(_type))

        else:
            validation = Validation.objects.filter(content=self.object).order_by("-date_proposition").first()

            if validation and validation.status == 'PENDING_V':  # if the validation have a validator, warn him by PM
                if 'text' not in self.request.POST or len(self.request.POST['text'].strip()) < 3:
                    messages.error(self.request, _(u'Merci de fournir une raison à la  suppression.'))
                    return redirect(self.object.get_absolute_url())
                else:
                    bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
                    msg = render_to_string(
                        'tutorialv2/messages/validation_cancel_on_delete.md',
                        {
                            'content': self.object,
                            'validator': validation.validator.username,
                            'user': self.request.user,
                            'message': '\n'.join(['> ' + line for line in self.request.POST['text'].split('\n')])
                        })

                    send_mp(
                        bot,
                        [validation.validator],
                        _(u"Demande de validation annulée").format(),
                        self.object.title,
                        msg,
                        False,
                    )
            if self.object.beta_topic is not None:
                beta_topic = self.object.beta_topic
                beta_topic.is_locked = True
                beta_topic.add_tags([u"Supprimé"])
                beta_topic.save()
                post = beta_topic.first_post()
                post.update_content(
                    _(u"[[a]]\n"
                      u"| Malheureusement, {} qui était en bêta a été supprimé par son auteur.\n\n").format(_type) +
                    post.text)

                post.save()

            self.object.delete()

            messages.success(self.request, _(u'Vous avez bien supprimé {}.').format(_type))

        return redirect(reverse('content:find-' + object_type, args=[request.user.pk]))


class DownloadContent(LoggedWithReadWriteHability, SingleContentDownloadViewMixin):
    """
    Download a zip archive with all the content of the repository directory
    """

    mimetype = 'application/zip'
    only_draft_version = False  # beta version can also be downloaded
    must_be_author = False  # other user can download archive

    @staticmethod
    def insert_into_zip(zip_file, git_tree):
        """Recursively add file into zip

        :param zip_file: a ``zipfile`` object (with writing permissions)
        :param git_tree: Git tree (from ``repository.commit(sha).tree``)
        """
        for blob in git_tree.blobs:  # first, add files :
            zip_file.writestr(blob.path, blob.data_stream.read())
        if len(git_tree.trees) is not 0:  # then, recursively add dirs :
            for subtree in git_tree.trees:
                DownloadContent.insert_into_zip(zip_file, subtree)

    def get_contents(self):
        """get the zip file stream

        :return: a zip file
        :rtype: byte
        """
        versioned = self.versioned_object

        # create and fill zip
        path = self.object.get_repo_path()
        zip_path = path + self.get_filename()
        zip_file = zipfile.ZipFile(zip_path, 'w')
        self.insert_into_zip(zip_file, versioned.repository.commit(versioned.current_version).tree)
        zip_file.close()

        # return content
        response = open(zip_path, "rb").read()
        os.remove(zip_path)
        return response

    def get_filename(self):
        return self.get_object().slug + '.zip'


class UpdateContentWithArchive(LoggedWithReadWriteHability, SingleContentFormViewMixin):
    """Update a content using an archive"""

    template_name = 'tutorialv2/import/content.html'
    form_class = ImportContentForm

    @staticmethod
    def walk_container(container):
        """Iterator that yield each file path in a Container

        :param container: the container
        :type container: Container
        :rtype: collections.Iterable[str]
        """

        if container.introduction:
            yield container.introduction
        if container.conclusion:
            yield container.conclusion

        for child in container.children:
            if isinstance(child, Container):
                for _y in UpdateContentWithArchive.walk_container(child):
                    yield _y
            else:
                yield child.text

    @staticmethod
    def walk_content(versioned):
        """Iterator that yield each files in a VersionedContent

        :param versioned: the content
        :type versioned: VersionedContent
        :rtype: collections.Iterable[str]
        """

        for _y in UpdateContentWithArchive.walk_container(versioned):
            yield _y

    @staticmethod
    def extract_content_from_zip(zip_archive):
        """Check if the data in the zip file are coherent

        :param zip_archive: the zip archive to analyze
        :type zip_archive: zipfile.ZipFile
        :raise BadArchiveError: if something is wrong in the archive
        :return: the content in the archive
        :rtype: VersionedContent
        """

        try:
            manifest = unicode(zip_archive.read('manifest.json'), 'utf-8')
        except KeyError:
            raise BadArchiveError(_(u'Cette archive ne contient pas de fichier manifest.json.'))
        except UnicodeDecodeError:
            raise BadArchiveError(_(u'L\'encodage du manifest.json n\'est pas de l\'UTF-8.'))

        # is the manifest ok ?
        try:
            json_ = json_reader.loads(manifest)
        except ValueError:
            raise BadArchiveError(
                _(u'Une erreur est survenue durant la lecture du manifest, '
                  u'vérifiez qu\'il s\'agit de JSON correctement formaté.'))
        try:
            versioned = get_content_from_json(json_, None, '',
                                              max_title_len=PublishableContent._meta.get_field('title').max_length)
        except BadManifestError as e:
            raise BadArchiveError(e.message)
        except InvalidSlugError as e:
            e1 = _(u'Le slug "{}" est invalide').format(e)
            e2 = u''
            if e.had_source:
                e2 = _(u' (slug généré à partir de "{}")').format(e.source)
            raise BadArchiveError(_(u'{}{} !').format(e1, e2))
        except Exception as e:
            raise BadArchiveError(_(u'Une erreur est survenue lors de la lecture de l\'archive : {}.').format(e))

        # is there everything in the archive ?
        for f in UpdateContentWithArchive.walk_content(versioned):
            try:
                zip_archive.getinfo(f)
            except KeyError:
                raise BadArchiveError(_(u'Le fichier "{}" n\'existe pas dans l\'archive.').format(f))

        return versioned

    @staticmethod
    def update_from_new_version_in_zip(copy_to, copy_from, zip_file):
        """Copy the information from ``new_container`` into ``copy_to``.
        This function correct path for file if necessary

        :param copy_to: container that to copy to
        :type copy_to: Container
        :param copy_from: copy from container
        :type copy_from: Container
        :param zip_file: zip file that contain the files
        :type zip_file: zipfile.ZipFile
        """

        for child in copy_from.children:
            if isinstance(child, Container):

                introduction = ''
                conclusion = ''

                if child.introduction:
                    try:
                        introduction = unicode(zip_file.read(child.introduction), 'utf-8')
                    except UnicodeDecodeError:
                        raise BadArchiveError(
                            _(u'Le fichier « {} » n\'est pas encodé en UTF-8'.format(child.introduction)))
                if child.conclusion:
                    try:
                        conclusion = unicode(zip_file.read(child.conclusion), 'utf-8')
                    except UnicodeDecodeError:
                        raise BadArchiveError(
                            _(u'Le fichier « {} » n\'est pas encodé en UTF-8'.format(child.conclusion)))

                copy_to.repo_add_container(child.title, introduction, conclusion, do_commit=False, slug=child.slug)
                UpdateContentWithArchive.update_from_new_version_in_zip(copy_to.children[-1], child, zip_file)

            elif isinstance(child, Extract):
                try:
                    text = unicode(zip_file.read(child.text), 'utf-8')
                except UnicodeDecodeError:
                    raise BadArchiveError(
                        _(u'Le fichier « {} » n\'est pas encodé en UTF-8'.format(child.text)))

                copy_to.repo_add_extract(child.title, text, do_commit=False, slug=child.slug)

    @staticmethod
    def use_images_from_archive(request, zip_file, versioned_content, gallery):
        """Extract image from a gallery and then translate the ``![.+](prefix:filename)`` into the final image we want.
        The ``prefix`` is defined into the settings.
        Note that this function does not perform any commit.

        :param zip_file: ZIP archive
        :type zip_file: zipfile.ZipFile
        :param versioned_content: content
        :type versioned_content: VersionedContent
        :param gallery: gallery of image
        :type gallery: Gallery
        """
        translation_dic = {}

        # create a temporary directory:
        temp = os.path.join(tempfile.gettempdir(), str(time.time()))
        if not os.path.exists(temp):
            os.makedirs(temp)

        for image_path in zip_file.namelist():

            image_basename = os.path.basename(image_path)

            if image_basename.strip() == "":  # don't deal with directory
                continue

            temp_image_path = os.path.abspath(os.path.join(temp, image_basename))

            # create a temporary file for the image
            f_im = open(temp_image_path, "wb")
            f_im.write(zip_file.read(image_path))
            f_im.close()

            # if it's not an image, pass
            try:
                ImagePIL.open(temp_image_path)
            except IOError:
                continue

            # if size is too large, pass
            if os.stat(temp_image_path).st_size > settings.ZDS_APP['gallery']['image_max_size']:
                messages.error(
                    request, _(u'Votre image "{}" est beaucoup trop lourde, réduisez sa taille à moins de {:.0f}'
                               u'Kio avant de l\'envoyer.').format(
                                   image_path, settings.ZDS_APP['gallery']['image_max_size'] / 1024))
                continue

            # create picture in database:
            pic = Image()
            pic.gallery = gallery
            pic.title = image_basename
            pic.slug = slugify(image_basename)
            pic.physical = get_thumbnailer(open(temp_image_path, "rb"), relative_name=temp_image_path)
            pic.pubdate = datetime.now()
            pic.save()

            translation_dic[image_path] = settings.ZDS_APP['site']['url'] + pic.physical.url

            # finally, remove image
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)

        zip_file.close()
        if os.path.exists(temp):
            shutil.rmtree(temp)

        # then, modify each extracts
        image_regex = re.compile(r"((?P<start>!\[.*?\]\()" + settings.ZDS_APP['content']['import_image_prefix'] +
                                 r":(?P<path>.*?)(?P<end>\)))")

        for element in versioned_content.traverse(only_container=False):
            if isinstance(element, Container):
                introduction = element.get_introduction()
                introduction = image_regex.sub(
                    lambda g: UpdateContentWithArchive.update_image_link(g, translation_dic), introduction)

                conclusion = element.get_conclusion()
                conclusion = image_regex.sub(
                    lambda g: UpdateContentWithArchive.update_image_link(g, translation_dic), conclusion)
                element.repo_update(element.title, introduction, conclusion, do_commit=False)
            else:
                section_text = element.get_text()
                section_text = image_regex.sub(
                    lambda g: UpdateContentWithArchive.update_image_link(g, translation_dic), section_text)

                element.repo_update(element.title, section_text, do_commit=False)

    @staticmethod
    def update_image_link(group, translation_dic):
        """callback function for the transformation of ``image:xxx`` to the right path in gallery

        :param group: matching object
        :type group: re.MatchObject
        :param translation_dic: image to link into gallery dictionary
        :type translation_dic: dict
        :return: updated link
        :rtype: str
        """
        start, image, end = group.group('start'), group.group('path'), group.group('end')

        if image in translation_dic:
            return start + translation_dic[image] + end
        else:
            return start + settings.ZDS_APP['content']['import_image_prefix'] + ':' + image + end

    def form_valid(self, form):
        versioned = self.versioned_object

        if self.request.FILES['archive']:
            try:
                zfile = zipfile.ZipFile(self.request.FILES['archive'], "r")
            except zipfile.BadZipfile:
                messages.error(self.request, _(u'Cette archive n\'est pas au format ZIP.'))
                return super(UpdateContentWithArchive, self).form_invalid(form)

            try:
                new_version = UpdateContentWithArchive.extract_content_from_zip(zfile)
            except BadArchiveError as e:
                messages.error(self.request, e.message)
                return super(UpdateContentWithArchive, self).form_invalid(form)
            else:

                # warn user if licence have changed:
                manifest = json_reader.loads(unicode(zfile.read('manifest.json'), 'utf-8'))
                if 'licence' not in manifest or manifest['licence'] != new_version.licence.code:
                    messages.info(
                        self.request, _(u'la licence « {} » a été appliquée.').format(new_version.licence.code))

                # first, update DB object (in order to get a new slug if needed)
                self.object.title = new_version.title
                self.object.description = new_version.description
                self.object.licence = new_version.licence
                self.object.type = new_version.type  # change of type is then allowed !!
                self.object.save()

                new_version.slug = self.object.slug  # new slug if any !!

                # ok, then, let's do the import. First, remove everything in the repository
                while True:
                    if len(versioned.children) != 0:
                        versioned.children[0].repo_delete(do_commit=False)
                    else:
                        break  # this weird construction ensure that everything is removed

                versioned.slug_pool = default_slug_pool()  # slug pool to its initial value (to avoid weird stuffs)

                # start by copying extra information
                self.object.insert_data_in_versioned(versioned)  # better have a clean version of those one
                versioned.description = new_version.description
                versioned.type = new_version.type
                versioned.licence = new_version.licence

                # update container (and repo)
                introduction = ''
                conclusion = ''

                if new_version.introduction:
                    introduction = unicode(zfile.read(new_version.introduction), 'utf-8')
                if new_version.conclusion:
                    conclusion = unicode(zfile.read(new_version.conclusion), 'utf-8')

                versioned.repo_update_top_container(
                    new_version.title, new_version.slug, introduction, conclusion, do_commit=False)

                # then do the dirty job:
                try:
                    UpdateContentWithArchive.update_from_new_version_in_zip(versioned, new_version, zfile)
                except BadArchiveError as e:
                    versioned.repository.index.reset()
                    messages.error(self.request, e.message)
                    return super(UpdateContentWithArchive, self).form_invalid(form)

                # and end up by a commit !!
                commit_message = form.cleaned_data['msg_commit']

                if commit_message == '':
                    commit_message = _(u'Importation d\'une archive contenant « {} ».').format(new_version.title)

                sha = versioned.commit_changes(commit_message)

                # now, use the images from the archive if provided. To work, this HAVE TO happen after commiting files !
                if "image_archive" in self.request.FILES:
                    try:
                        zfile = zipfile.ZipFile(self.request.FILES["image_archive"], "r")
                    except zipfile.BadZipfile:
                        messages.error(self.request, _(u'L\'archive contenant les images n\'est pas au format ZIP.'))
                        return self.form_invalid(form)

                    UpdateContentWithArchive.use_images_from_archive(
                        self.request,
                        zfile,
                        versioned,
                        self.object.gallery)

                    commit_message = _(u'Utilisation des images de l\'archive pour « {} »').format(new_version.title)
                    sha = versioned.commit_changes(commit_message)  # another commit

                # of course, need to update sha
                self.object.sha_draft = sha
                self.object.update_date = datetime.now()
                self.object.save()

                self.success_url = reverse('content:view', args=[versioned.pk, versioned.slug])

        return super(UpdateContentWithArchive, self).form_valid(form)


class CreateContentFromArchive(LoggedWithReadWriteHability, FormView):
    """Create a content using an archive"""

    form_class = ImportNewContentForm
    template_name = "tutorialv2/import/content-new.html"
    object = None

    def form_valid(self, form):

        if self.request.FILES['archive']:
            try:
                zfile = zipfile.ZipFile(self.request.FILES['archive'], "r")
            except zipfile.BadZipfile:
                messages.error(self.request, _(u'Cette archive n\'est pas au format ZIP.'))
                return self.form_invalid(form)

            try:
                new_content = UpdateContentWithArchive.extract_content_from_zip(zfile)
            except BadArchiveError as e:
                messages.error(self.request, e.message)
                return super(CreateContentFromArchive, self).form_invalid(form)
            except KeyError as e:
                messages.error(self.request, _(e.message + u" n'est pas correctement renseigné."))
                return super(CreateContentFromArchive, self).form_invalid(form)
            else:

                # warn user if licence have changed:
                manifest = json_reader.loads(unicode(zfile.read('manifest.json'), 'utf-8'))
                if 'licence' not in manifest or manifest['licence'] != new_content.licence.code:
                    messages.info(
                        self.request, _(u'la licence « {} » a été appliquée.'.format(new_content.licence.code)))

                # first, create DB object (in order to get a slug)
                self.object = PublishableContent()
                self.object.title = new_content.title
                self.object.description = new_content.description
                self.object.licence = new_content.licence
                self.object.type = new_content.type  # change of type is then allowed !!
                self.object.creation_date = datetime.now()

                self.object.save()

                new_content.slug = self.object.slug  # new slug (choosen via DB)

                # Creating the gallery
                gal = Gallery()
                gal.title = new_content.title
                gal.slug = slugify(new_content.title)
                gal.pubdate = datetime.now()
                gal.save()

                # Attach user to gallery
                userg = UserGallery()
                userg.gallery = gal
                userg.mode = "W"  # write mode
                userg.user = self.request.user
                userg.save()
                self.object.gallery = gal

                # Add subcategories on tutorial
                for subcat in form.cleaned_data["subcategory"]:
                    self.object.subcategory.add(subcat)

                # We need to save the tutorial before changing its author list since it's a many-to-many relationship
                self.object.authors.add(self.request.user)
                self.object.save()

                # ok, now we can import
                introduction = ''
                conclusion = ''

                if new_content.introduction:
                    introduction = unicode(zfile.read(new_content.introduction), 'utf-8')
                if new_content.conclusion:
                    conclusion = unicode(zfile.read(new_content.conclusion), 'utf-8')

                commit_message = _(u'Création de « {} »').format(new_content.title)
                init_new_repo(self.object, introduction, conclusion, commit_message=commit_message)

                # copy all:
                versioned = self.object.load_version()
                try:
                    UpdateContentWithArchive.update_from_new_version_in_zip(versioned, new_content, zfile)
                except BadArchiveError as e:
                    self.object.delete()  # abort content creation
                    messages.error(self.request, e.message)
                    return super(CreateContentFromArchive, self).form_invalid(form)

                # and end up by a commit !!
                commit_message = form.cleaned_data['msg_commit']

                if commit_message == '':
                    commit_message = _(u'Importation d\'une archive contenant « {} »').format(new_content.title)

                sha = versioned.commit_changes(commit_message)

                # This HAVE TO happen after commiting files (if not, content are None)
                if "image_archive" in self.request.FILES:
                    try:
                        zfile = zipfile.ZipFile(self.request.FILES["image_archive"], "r")
                    except zipfile.BadZipfile:
                        messages.error(self.request, _(u'L\'archive contenant les images n\'est pas au format ZIP.'))
                        return self.form_invalid(form)

                    UpdateContentWithArchive.use_images_from_archive(
                        self.request,
                        zfile,
                        versioned,
                        self.object.gallery)

                    commit_message = _(u'Utilisation des images de l\'archive pour « {} »').format(new_content.title)
                    sha = versioned.commit_changes(commit_message)  # another commit

                # of course, need to update sha
                self.object.sha_draft = sha
                self.object.update_date = datetime.now()
                self.object.save()

                self.success_url = reverse('content:view', args=[versioned.pk, versioned.slug])

        return super(CreateContentFromArchive, self).form_valid(form)


class CreateContainer(LoggedWithReadWriteHability, SingleContentFormViewMixin):
    template_name = 'tutorialv2/create/container.html'
    form_class = ContainerForm
    content = None
    authorized_for_staff = True  # former behaviour

    def get_context_data(self, **kwargs):
        context = super(CreateContainer, self).get_context_data(**kwargs)

        context['container'] = search_container_or_404(self.versioned_object, self.kwargs)
        context['gallery'] = self.object.gallery
        return context

    def render_to_response(self, context, **response_kwargs):
        parent = context['container']
        if not parent.can_add_container():
            messages.error(self.request, _(u'Vous ne pouvez plus ajouter de conteneur à « {} ».').format(parent.title))
            return redirect(parent.get_absolute_url())

        return super(CreateContainer, self).render_to_response(context, **response_kwargs)

    def form_valid(self, form):
        parent = search_container_or_404(self.versioned_object, self.kwargs)

        sha = parent.repo_add_container(form.cleaned_data['title'],
                                        form.cleaned_data['introduction'],
                                        form.cleaned_data['conclusion'],
                                        form.cleaned_data['msg_commit'])

        # then save:
        self.object.sha_draft = sha
        self.object.update_date = datetime.now()
        self.object.save()

        self.success_url = parent.children[-1].get_absolute_url()

        return super(CreateContainer, self).form_valid(form)


class DisplayContainer(LoginRequiredMixin, SingleContentDetailViewMixin):
    """Base class that can show any content in any state"""

    model = PublishableContent
    template_name = 'tutorialv2/view/container.html'
    sha = None
    must_be_author = False  # beta state does not need the author
    only_draft_version = False

    def get_context_data(self, **kwargs):
        """Show the given tutorial if exists."""
        context = super(DisplayContainer, self).get_context_data(**kwargs)
        container = search_container_or_404(self.versioned_object, self.kwargs)
        context['containers_target'] = get_target_tagged_tree(container, self.versioned_object)

        if self.versioned_object.is_beta:
            context['formWarnTypo'] = WarnTypoForm(
                self.versioned_object,
                container,
                public=False,
                initial={'target': container.get_path(relative=True)})

        context['container'] = container

        # pagination: search for `previous` and `next`, if available
        if self.versioned_object.type != 'ARTICLE' and not self.versioned_object.has_extracts():
            chapters = self.versioned_object.get_list_of_chapters()
            try:
                position = chapters.index(container)
            except ValueError:
                pass  # this is not (yet?) a chapter
            else:
                context['has_pagination'] = True
                context['previous'] = None
                context['next'] = None
                if position > 0:
                    context['previous'] = chapters[position - 1]
                if position < len(chapters) - 1:
                    context['next'] = chapters[position + 1]

        # check whether this tuto support js fiddle
        if self.object.js_support:
            is_js = "js"
        else:
            is_js = ""
        context["is_js"] = is_js

        return context


class DisplayBetaContainer(DisplayContainer):
    """View to get the beta version of a container"""

    sha = None

    def get_object(self, queryset=None):
        """rewritten to ensure that the version is set to beta, raise Http404 if there is no such version"""
        obj = super(DisplayBetaContainer, self).get_object(queryset)

        if not obj.sha_beta or obj.sha_beta == '':
            raise Http404(_(u"Aucune bêta n'existe pour ce contenu."))

        else:
            self.sha = obj.sha_beta

        # make the slug always right in URLs resolution:
        if 'slug' in self.kwargs:
            self.kwargs['slug'] = obj.slug

        return obj


class EditContainer(LoggedWithReadWriteHability, SingleContentFormViewMixin):
    template_name = 'tutorialv2/edit/container.html'
    form_class = ContainerForm
    content = None

    def get_context_data(self, **kwargs):
        context = super(EditContainer, self).get_context_data(**kwargs)
        form = kwargs.pop('form', None)
        context['container'] = form.initial['container']
        context['gallery'] = self.object.gallery

        return context

    def get_initial(self):
        """rewrite function to pre-populate form"""
        initial = super(EditContainer, self).get_initial()
        container = search_container_or_404(self.versioned_object, self.kwargs)

        initial['title'] = container.title
        initial['introduction'] = container.get_introduction()
        initial['conclusion'] = container.get_conclusion()
        initial['container'] = container

        initial['last_hash'] = container.compute_hash()

        return initial

    def form_valid(self, form):
        container = search_container_or_404(self.versioned_object, self.kwargs)

        # check if content has changed:
        current_hash = container.compute_hash()
        if current_hash != form.cleaned_data['last_hash']:
            data = form.data.copy()
            data['last_hash'] = current_hash
            data['introduction'] = container.get_introduction()
            data['conclusion'] = container.get_conclusion()
            form.data = data
            messages.error(self.request, _(u'Une nouvelle version a été postée avant que vous ne validiez.'))
            return self.form_invalid(form)

        sha = container.repo_update(form.cleaned_data['title'],
                                    form.cleaned_data['introduction'],
                                    form.cleaned_data['conclusion'],
                                    form.cleaned_data['msg_commit'],
                                    update_slug=self.object.public_version is None)

        # then save
        self.object.sha_draft = sha
        self.object.update_date = datetime.now()
        self.object.save()

        self.success_url = container.get_absolute_url()

        return super(EditContainer, self).form_valid(form)


class CreateExtract(LoggedWithReadWriteHability, SingleContentFormViewMixin):
    template_name = 'tutorialv2/create/extract.html'
    form_class = ExtractForm
    content = None
    authorized_for_staff = True

    def get_context_data(self, **kwargs):
        context = super(CreateExtract, self).get_context_data(**kwargs)
        context['container'] = search_container_or_404(self.versioned_object, self.kwargs)
        context['gallery'] = self.object.gallery

        return context

    def render_to_response(self, context, **response_kwargs):
        parent = context['container']
        if not parent.can_add_extract():
            messages.error(self.request, _(u'Vous ne pouvez plus ajouter de section à « {} ».').format(parent.title))
            return redirect(parent.get_absolute_url())

        return super(CreateExtract, self).render_to_response(context, **response_kwargs)

    def form_valid(self, form):
        parent = search_container_or_404(self.versioned_object, self.kwargs)

        if 'preview' in self.request.POST:
            return self.form_invalid(form)  # using the preview button

        sha = parent.repo_add_extract(form.cleaned_data['title'],
                                      form.cleaned_data['text'],
                                      form.cleaned_data['msg_commit'])

        # then save
        self.object.sha_draft = sha
        self.object.update_date = datetime.now()
        self.object.save()

        self.success_url = parent.children[-1].get_absolute_url()

        return super(CreateExtract, self).form_valid(form)


class EditExtract(LoggedWithReadWriteHability, SingleContentFormViewMixin):
    template_name = 'tutorialv2/edit/extract.html'
    form_class = ExtractForm
    content = None

    def get_context_data(self, **kwargs):
        context = super(EditExtract, self).get_context_data(**kwargs)
        form = kwargs.pop('form', None)
        context['extract'] = form.initial['extract']
        context['gallery'] = self.object.gallery

        return context

    def get_initial(self):
        """rewrite function to pre-populate form"""
        initial = super(EditExtract, self).get_initial()
        extract = search_extract_or_404(self.versioned_object, self.kwargs)

        initial['title'] = extract.title
        initial['text'] = extract.get_text()
        initial['extract'] = extract

        initial['last_hash'] = extract.compute_hash()

        return initial

    def form_valid(self, form):
        extract = search_extract_or_404(self.versioned_object, self.kwargs)

        # check if content has changed:
        current_hash = extract.compute_hash()
        if current_hash != form.cleaned_data['last_hash']:
            data = form.data.copy()
            data['last_hash'] = current_hash
            data['text'] = extract.get_text()
            form.data = data
            messages.error(self.request, _(u'Une nouvelle version a été postée avant que vous ne validiez.'))
            return self.form_invalid(form)

        if 'preview' in self.request.POST:
            return self.form_invalid(form)  # using the preview button

        sha = extract.repo_update(form.cleaned_data['title'],
                                  form.cleaned_data['text'],
                                  form.cleaned_data['msg_commit'])

        # then save
        self.object.sha_draft = sha
        self.object.update_date = datetime.now()
        self.object.save()

        self.success_url = extract.get_absolute_url()

        return super(EditExtract, self).form_valid(form)


class DeleteContainerOrExtract(LoggedWithReadWriteHability, SingleContentViewMixin, DeleteView):
    model = PublishableContent
    template_name = None
    http_method_names = [u'delete', u'post']
    object = None
    versioned_object = None

    def delete(self, request, *args, **kwargs):
        """delete any object, either Extract or Container"""
        self.object = self.get_object()
        self.versioned_object = self.get_versioned_object()
        parent = search_container_or_404(self.versioned_object, self.kwargs)

        # find something to delete and delete it
        to_delete = None
        if 'object_slug' in self.kwargs:
            try:
                to_delete = parent.children_dict[self.kwargs['object_slug']]
            except KeyError:
                raise Http404(_(u"Impossible de récupérer le contenu pour le supprimer."))

        sha = to_delete.repo_delete()

        # then save
        self.object.sha_draft = sha
        self.object.update_date = datetime.now()
        self.object.save()

        return redirect(parent.get_absolute_url())


class DisplayHistory(LoggedWithReadWriteHability, SingleContentDetailViewMixin):
    """
    Display the whole modification history.
    This class has no reason to be adapted to any content type.
    """

    model = PublishableContent
    template_name = "tutorialv2/view/history.html"

    def get_context_data(self, **kwargs):
        context = super(DisplayHistory, self).get_context_data(**kwargs)

        repo = self.versioned_object.repository
        context['commits'] = objects.commit.Commit.iter_items(repo, 'HEAD')

        # Git empty tree is 4b825dc642cb6eb9a060e54bf8d69288fbee4904, see
        # http://stackoverflow.com/questions/9765453/gits-semi-secret-empty-tree
        context['empty_sha'] = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"

        return context


class DisplayDiff(LoggedWithReadWriteHability, SingleContentDetailViewMixin):
    """
    Display the difference between two versions of a content.
    The left version is given in a GET query parameter named from, the right one with to.
    This class has no reason to be adapted to any content type.
    """

    model = PublishableContent
    template_name = "tutorialv2/view/diff.html"
    only_draft_version = False

    def get_context_data(self, **kwargs):
        context = super(DisplayDiff, self).get_context_data(**kwargs)

        if 'from' not in self.request.GET:
            raise Http404(_(u"Paramètre GET 'from' manquant."))
        if 'to' not in self.request.GET:
            raise Http404(u"Paramètre GET 'to' manquant.")

        # open git repo and find diff between two versions
        repo = self.versioned_object.repository
        try:
            # repo.commit raises BadObject or BadName if invalid SHA
            commit_from = repo.commit(self.request.GET['from'])
            commit_to = repo.commit(self.request.GET['to'])
            # commit_to.diff raises GitErrorCommand if 00..00 SHA for instance
            tdiff = commit_to.diff(commit_from, R=True)
        except (GitCommandError, BadName, BadObject):
            raise Http404

        context['commit_from'] = commit_from
        context['commit_to'] = commit_to
        context['modified'] = tdiff.iter_change_type('M')
        context['added'] = tdiff.iter_change_type('A')
        context['deleted'] = tdiff.iter_change_type('D')
        context['renamed'] = tdiff.iter_change_type('R')

        return context


class ManageBetaContent(LoggedWithReadWriteHability, SingleContentFormViewMixin):
    """
    Depending of the value of `self.action`, this class will behave differently;
    - if "set", it will active (of update) the beta
    - if "inactive", it will inactive the beta on the tutorial
    """

    model = PublishableContent
    form_class = BetaForm
    authorized_for_staff = True
    only_draft_version = False

    action = None

    def _get_all_tags(self):
        all_tags = []
        categories = self.object.subcategory.all()
        names = [smart_text(category.title).lower() for category in categories]
        existing_tags = Tag.objects.filter(title__in=names).all()
        existing_tags_names = [tag.title for tag in existing_tags]
        unexisting_tags = list(set(names) - set(existing_tags_names))
        for tag in unexisting_tags:
            new_tag = Tag()
            new_tag.title = tag[:20]
            new_tag.save()
            all_tags.append(new_tag)
        all_tags += existing_tags
        return all_tags

    def _create_beta_topic(self, msg, beta_version, _type, tags):
        topic_title = beta_version.title
        tags = "[beta][{}]".format(_type)
        i = 0
        while len(topic_title) + len(tags) + len(tags[i]) + 2 < Topic._meta.get_field("title").max_length:
            tags += '[{}]'.format(tags[i])
            i += 1
        forum = get_object_or_404(Forum, pk=settings.ZDS_APP['forum']['beta_forum_id'])
        topic = create_topic(request=self.request,
                             author=self.request.user,
                             forum=forum,
                             title=topic_title,
                             subtitle=u"{}".format(beta_version.description),
                             text=msg,
                             related_publishable_content=self.object)
        topic.save()
        # make all authors follow the topic:
        for author in self.object.authors.all():
            if not topic.is_followed(author):
                follow(topic, author)
            mark_read(topic, author)

        return topic

    @method_decorator(transaction.atomic)
    def dispatch(self, *args, **kwargs):
        return super(ManageBetaContent, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        beta_version = self.versioned_object
        sha_beta = beta_version.current_version

        # topic of the beta version:
        topic = self.object.beta_topic

        if topic:
            if topic.forum_id != settings.ZDS_APP['forum']['beta_forum_id']:
                # if the topic is moved from the beta forum, then a new one is created instead
                topic = None

        _type = self.object.type.lower()
        if _type == "tutorial":
            _type = _('tutoriel')

        # perform actions:
        if self.action == 'inactive':
            self.object.sha_beta = None

            msg_post = render_to_string(
                'tutorialv2/messages/beta_desactivate.md', {'content': beta_version, 'type': _type}
            )
            send_post(self.request, topic, self.request.user, msg_post)
            lock_topic(topic)

        elif self.action == 'set':
            already_in_beta = self.object.in_beta()
            all_tags = []

            if not already_in_beta or self.object.sha_beta != sha_beta:
                self.object.sha_beta = sha_beta
                self.versioned_object.in_beta = True
                self.versioned_object.sha_beta = sha_beta

                msg = render_to_string(
                    'tutorialv2/messages/beta_activate_topic.md',
                    {
                        'content': beta_version,
                        'type': _type,
                        'url': settings.ZDS_APP['site']['url'] + self.versioned_object.get_absolute_url_beta()
                    }
                )

                if not topic:
                    # if first time putting the content in beta, send a message on the forum and a PM

                    # find tags
                    all_tags = self._get_all_tags()
                    topic = self._create_beta_topic(msg, beta_version, _type, all_tags)

                    bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
                    msg_pm = render_to_string(
                        'tutorialv2/messages/beta_activate_pm.md',
                        {
                            'content': beta_version,
                            'type': _type,
                            'url': settings.ZDS_APP['site']['url'] + topic.get_absolute_url(),
                            'user': self.request.user
                        }
                    )
                    send_mp(bot,
                            self.object.authors.all(),
                            _(_type[0].upper() + _type[1:].lower() + u" en bêta"),
                            beta_version.title,
                            msg_pm,
                            False)
                else:
                    all_tags = self._get_all_tags()
                    if not already_in_beta:
                        unlock_topic(topic)
                        msg_post = render_to_string(
                            'tutorialv2/messages/beta_reactivate.md',
                            {
                                'content': beta_version,
                                'type': _type,
                                'url': settings.ZDS_APP['site']['url'] + self.versioned_object.get_absolute_url_beta()
                            }
                        )
                    else:
                        msg_post = render_to_string(
                            'tutorialv2/messages/beta_update.md',
                            {
                                'content': beta_version,
                                'type': _type,
                                'url': settings.ZDS_APP['site']['url'] + self.versioned_object.get_absolute_url_beta()
                            }
                        )
                    topic = send_post(self.request, topic, self.request.user, msg_post)

                    # make sure that all authors follow the topic:
                    for author in self.object.authors.all():
                        if not topic.is_followed(author):
                            follow(topic, author)
                            mark_read(topic, author)

            # finally set the tags on the topic
            if topic:
                topic.tags.clear()
                for tag in all_tags:
                    topic.tags.add(tag)
                topic.save()

        self.object.save()

        self.success_url = self.versioned_object.get_absolute_url(version=sha_beta)

        if self.object.is_beta(sha_beta):
            self.success_url = self.versioned_object.get_absolute_url_beta()

        return super(ManageBetaContent, self).form_valid(form)


class WarnTypo(SingleContentFormViewMixin):

    modal_form = True
    form_class = WarnTypoForm
    must_be_author = False
    only_draft_version = False

    object = None

    def get_form_kwargs(self):

        kwargs = super(WarnTypo, self).get_form_kwargs()

        versioned = self.get_versioned_object()
        kwargs['content'] = versioned
        kwargs['targeted'] = versioned

        if self.request.POST['target']:
            kwargs['targeted'] = search_container_or_404(versioned, self.request.POST['target'])

        kwargs['public'] = True

        if versioned.is_beta:
            kwargs['public'] = False
        elif not versioned.is_public:
            raise PermissionDenied

        return kwargs

    def form_valid(self, form):

        user = self.request.user

        authors_reachable = Profile.objects.contactable_members()\
            .filter(user__in=self.object.authors.all())
        authors = []
        for author in authors_reachable:
            authors.append(author.user)

        # check if the warn is done on a public or beta version :
        is_public = False

        if form.content.is_public:
            is_public = True
        elif not form.content.is_beta:
            raise Http404(_(u"Le contenu n'est ni public, ni en bêta."))

        if len(authors) == 0:
            if self.object.authors.count() > 1:
                messages.error(self.request, _(u"Les auteurs sont malheureusement injoignables."))
            else:
                messages.error(self.request, _(u"L'auteur est malheureusement injoignable."))

        elif user in authors:  # author try to PM himself
            messages.error(self.request, _(u'Impossible d\'envoyer la proposition de correction : vous êtes auteur.'))

        else:  # send correction
            text = '\n'.join(['> ' + line for line in form.cleaned_data['text'].split('\n')])

            _type = _(u'l\'article')
            if form.content.type == 'TUTORIAL':
                _type = _(u'le tutoriel')

            msg = render_to_string(
                'tutorialv2/messages/warn_typo.md',
                {
                    'user': user,
                    'content': form.content,
                    'target': form.targeted,
                    'type': _type,
                    'public': is_public,
                    'text': text
                })

            # send it :
            send_mp(user, authors, _(u"Proposition de correction"), form.content.title, msg, leave=False)

            messages.success(self.request, _(u'Merci pour votre proposition de correction.'))

        return redirect(form.previous_page_url)


class ContentsWithHelps(ZdSPagingListView):
    """List all tutorial that needs help, i.e registered as needing at least one HelpWriting or is in beta
    for more documentation, have a look to ZEP 03 specification (fr)"""

    context_object_name = 'contents'
    template_name = 'tutorialv2/view/help.html'
    paginate_by = settings.ZDS_APP['content']['helps_per_page']

    specific_need = None

    def get_queryset(self):
        """get only tutorial that need help and handle filtering if asked"""
        query_set = PublishableContent.objects \
            .annotate(total=Count('helps'), shasize=Count('sha_beta')) \
            .filter((Q(sha_beta__isnull=False) & Q(shasize__gt=0)) | Q(total__gt=0)) \
            .all()
        if 'need' in self.request.GET:
            self.specific_need = self.request.GET.get('need')
            if self.specific_need != '':
                query_set = query_set.filter(helps__slug__in=[self.specific_need])
        if 'type' in self.request.GET:
            filter_type = None
            if self.request.GET['type'] == 'article':
                filter_type = 'ARTICLE'
            elif self.request.GET['type'] == 'tuto':
                filter_type = 'TUTORIAL'
            if filter_type:
                query_set = query_set.filter(type=filter_type)
        return query_set

    def get_context_data(self, **kwargs):
        """Add all HelpWriting objects registered to the context so that the template can use it"""
        context = super(ContentsWithHelps, self).get_context_data(**kwargs)
        queryset = kwargs.pop('object_list', self.object_list)

        helps = HelpWriting.objects

        if self.specific_need:
            context['specific_need'] = helps.filter(slug=self.specific_need).first()

        context['helps'] = helps.all()
        context['total_contents_number'] = queryset.count()
        return context


class ActivateJSFiddleInContent(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """Handles changes a validator or staff member can do on the js fiddle support of the provided content
    Only those members can do it"""

    permissions = ["tutorialv2.change_publishablecontent"]
    form_class = JsFiddleActivationForm
    http_method_names = ["post"]

    def form_valid(self, form):
        """Change the js fiddle support of content and redirect to the view page """
        content = get_object_or_404(PublishableContent, pk=form.cleaned_data["pk"])
        content.js_support = form.cleaned_data["js_support"]
        content.save()
        return redirect(content.load_version().get_absolute_url())


class MoveChild(LoginRequiredMixin, SingleContentPostMixin, FormView):

    model = PublishableContent
    form_class = MoveElementForm
    versioned = False

    def get(self, request, *args, **kwargs):
        raise PermissionDenied

    def form_valid(self, form):
        content = self.get_object()
        versioned = content.load_version()
        base_container_slug = form.data["container_slug"]
        child_slug = form.data['child_slug']

        if base_container_slug == '':
            raise Http404(_(u"Le slug du container de base est vide."))

        if child_slug == '':
            raise Http404(_(u"Le slug du container enfant est vide."))

        if base_container_slug == versioned.slug:
            parent = versioned
        else:
            search_params = {}

            if 'first_level_slug' in form.data and form.data['first_level_slug'] != '':
                search_params['parent_container_slug'] = form.data['first_level_slug']
                search_params['container_slug'] = base_container_slug
            else:
                search_params['container_slug'] = base_container_slug
            parent = search_container_or_404(versioned, search_params)

        try:
            child = parent.children_dict[child_slug]
            if form.data['moving_method'] == MoveElementForm.MOVE_UP:
                parent.move_child_up(child_slug)
            elif form.data['moving_method'] == MoveElementForm.MOVE_DOWN:
                parent.move_child_down(child_slug)
            elif form.data['moving_method'][0:len(MoveElementForm.MOVE_AFTER)] == MoveElementForm.MOVE_AFTER:
                target = form.data['moving_method'][len(MoveElementForm.MOVE_AFTER) + 1:]
                if not parent.has_child_with_path(target):
                    if "/" not in target:
                        target_parent = versioned
                    else:
                        target_parent = search_container_or_404(versioned, "/".join(target.split("/")[:-1]))

                        if target.split("/")[-1] not in target_parent.children_dict:
                            raise Http404(_(u"La cible n'est pas un enfant du parent."))
                    child = target_parent.children_dict[target.split("/")[-1]]
                    try_adopt_new_child(target_parent, parent.children_dict[child_slug])
                    # now, I will fix a bug that happens when the slug changes
                    # this one cost me so much of my hair
                    # and makes me think copy/past are killing kitty cat.
                    child_slug = target_parent.children[-1].slug
                    parent = target_parent
                parent.move_child_after(child_slug, target.split("/")[-1])
            elif form.data['moving_method'][0:len(MoveElementForm.MOVE_BEFORE)] == MoveElementForm.MOVE_BEFORE:
                target = form.data['moving_method'][len(MoveElementForm.MOVE_BEFORE) + 1:]
                if not parent.has_child_with_path(target):
                    if "/" not in target:
                        target_parent = versioned
                    else:
                        target_parent = search_container_or_404(versioned, "/".join(target.split("/")[:-1]))

                        if target.split("/")[-1] not in target_parent.children_dict:
                            raise Http404(_(u"La cible n'est pas un enfant du parent."))
                    child = target_parent.children_dict[target.split("/")[-1]]
                    try_adopt_new_child(target_parent, parent.children_dict[child_slug])
                    # now, I will fix a bug that happens when the slug changes
                    # this one cost me so much of my hair
                    child_slug = target_parent.children[-1].slug
                    parent = target_parent
                parent.move_child_before(child_slug, target.split("/")[-1])
            versioned.slug = content.slug  # we force not to change slug
            versioned.dump_json()

            parent.repo_update(parent.title,
                               parent.get_introduction(),
                               parent.get_conclusion(),
                               _(u"Déplacement de ") + child_slug, update_slug=False)
            content.sha_draft = versioned.sha_draft
            content.save(force_slug_update=False)  # we do not want the save routine to update the slug in case
            # of slug algorithm conflict (for pre-zep-12 or imported content)
            messages.info(self.request, _(u"L'élément a bien été déplacé."))
        except TooDeepContainerError:
            messages.error(self.request, _(u"Ce conteneur contient déjà trop d'enfants pour être"
                                           u" inclus dans un autre conteneur."))
        except KeyError:
            messages.warning(self.request, _(u"Vous n'avez pas complètement rempli le formulaire,"
                                             u"ou bien il est impossible de déplacer cet élément."))
        except ValueError as e:
            raise Http404(_(u"L'arbre spécifié n'est pas valide." + str(e)))
        except IndexError:
            messages.warning(self.request, _(u"L'élément se situe déjà à la place souhaitée."))
        except TypeError:
            messages.error(self.request, _(u"L'élément ne peut pas être déplacé à cet endroit."))
        if base_container_slug == versioned.slug:
            return redirect(reverse("content:view", args=[content.pk, content.slug]))
        else:
            return redirect(child.get_absolute_url())


class AddAuthorToContent(LoggedWithReadWriteHability, SingleContentFormViewMixin):
    only_draft_version = True
    must_be_author = True
    form_class = AuthorForm
    authorized_for_staff = True
    already_finished = False

    def form_valid(self, form):
        _type = self.object.type.lower()
        if _type == "tutorial":
            _type = _(u'du tutoriel')
        else:
            _type = _(u'de l\'article')
        bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
        for user in form.cleaned_data["users"]:
            if user not in self.object.authors.all() and user != self.request.user:
                self.object.authors.add(user)
                url_index = reverse("content:find-" + self.object.type.lower(), args=[user.pk])
                send_mp(
                    bot,
                    [user],
                    string_concat(_(u'Ajout à la rédaction '), _type),
                    self.versioned_object.title,
                    render_to_string("tutorialv2/messages/add_author_pm.md", {
                        'content': self.object,
                        'type': _type,
                        'url': self.object.get_absolute_url(),
                        'index': url_index,
                        'user': user.username
                    }),
                    True,
                    direct=False,
                )
                new_user = UserGallery()
                new_user.gallery = self.object.gallery
                new_user.user = user
                new_user.mode = GALLERY_WRITE
                new_user.save()
        self.object.save()
        if not self.already_finished:
            self.success_url = self.object.get_absolute_url()

        return super(AddAuthorToContent, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _(u"Les auteurs sélectionnés n'existent pas."))
        self.success_url = self.object.get_absolute_url()
        return super(AddAuthorToContent, self).form_valid(form)


class RemoveAuthorFromContent(AddAuthorToContent):

    @staticmethod
    def remove_author(content, user):
        """Remove an user from the authors and ensure that he is access to the content's gallery is also removed.
        The last author is not removed.

        :param content: the content
        :type content: zds.tutorialv2.models.models_database.PublishableContent
        :param user: the author
        :type user: User
        :return: ``True`` if the author was removed, ``False`` otherwise
        """
        if user in content.authors.all() and content.authors.count() > 1:
            gallery = UserGallery.objects.filter(user__pk=user.pk, gallery__pk=content.gallery.pk).first()

            if gallery:
                gallery.delete()

            content.authors.remove(user)
            return True

        return False

    def form_valid(self, form):

        current_user = False
        users = form.cleaned_data["users"]

        _type = _(u'cet article')
        if self.object.type == 'TUTORIAL':
            _type = _(u'ce tutoriel')

        for user in users:
            if RemoveAuthorFromContent.remove_author(self.object, user):
                if user.pk == self.request.user.pk:
                    current_user = True
            else:  # if user is incorrect or alone
                messages.error(self.request,
                               _(u'Vous êtes le seul auteur de {} ou le membre sélectionné '
                                 u'en a déjà quitté la rédaction.').format(_type))
                return redirect(self.object.get_absolute_url())

        self.object.save()

        authors_list = u''

        for index, user in enumerate(form.cleaned_data["users"]):
            if index > 0:
                if index == len(users) - 1:
                    authors_list += _(u' et ')
                else:
                    authors_list += _(u', ')
            authors_list += user.username

        if not current_user:  # if the removed author is not current user
            messages.success(
                self.request, _(u'Vous avez enlevé {} de la liste des auteurs de « {} ».').format(authors_list, _type))
            self.success_url = self.object.get_absolute_url()
        else:  # if current user is leaving the content's redaction, redirect him to a more suitable page
            messages.success(self.request, _(u'Vous avez bien quitté la rédaction de « {} ».').format(_type))
            self.success_url = reverse('content:find-' + self.object.type.lower(), args=[self.request.user.pk])
        self.already_finished = True  # this one is kind of tricky : because of inheritance we used to force redirection
        # to the content itself. This does not please me but I think it is better to do that like that instead of
        # super(FormView, self).form_valid(form). I find it so hard to understand.
        return super(RemoveAuthorFromContent, self).form_valid(form)


class ContentOfAuthor(ZdSPagingListView):
    type = 'ALL'
    context_object_name = 'contents'
    paginate_by = settings.ZDS_APP['content']['content_per_page']
    template_name = 'tutorialv2/index.html'
    model = PublishableContent

    authorized_filters = {
        'public': [lambda q: q.filter(sha_public__isnull=False), _(u'Publiés'), True, 'tick green'],
        'validation': [lambda q: q.filter(sha_validation__isnull=False), _(u'En validation'), False, 'tick'],
        'beta': [lambda q: q.filter(sha_beta__isnull=False), _(u'En bêta'), True, 'beta'],
        'redaction': [
            lambda q: q.filter(sha_validation__isnull=True, sha_public__isnull=True, sha_beta__isnull=True),
            _(u'Brouillons'), False, 'edit'],
    }
    sorts = {
        'creation': [lambda q: q.order_by('creation_date'), _(u"Par date de création")],
        'abc': [lambda q: q.order_by('title'), _(u"Par ordre alphabétique")],
        'modification': [lambda q: q.order_by('-update_date'), _(u"Par date de dernière modification")]
    }
    sort = ''
    filter = ''
    user = None

    def dispatch(self, request, *args, **kwargs):
        self.user = get_object_or_404(User, pk=int(self.kwargs["pk"]))
        if self.user != self.request.user and 'filter' in self.request.GET:
            filter_ = self.request.GET.get('filter').lower()
            if filter_ in self.authorized_filters:
                if not self.authorized_filters[filter_][2]:
                    raise PermissionDenied
            else:
                raise Http404(_(u"Le filtre n'est pas autorisé."))
        return super(ContentOfAuthor, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        if self.type in TYPE_CHOICES_DICT.keys():
            queryset = PublishableContent.objects.filter(authors__pk__in=[self.user.pk], type=self.type)
        else:
            raise Http404(_(u"Ce type de contenu est inconnu dans le système."))

        # prefetch:
        queryset = queryset\
            .prefetch_related('authors')\
            .prefetch_related('subcategory')\
            .select_related('licence')\
            .select_related('image')

        # Filter.
        if 'filter' in self.request.GET:
            self.filter = self.request.GET['filter'].lower()
            if self.filter not in self.authorized_filters:
                raise Http404(_(u"Le filtre n'est pas autorisé."))
        elif self.user != self.request.user:
            self.filter = 'public'
        if self.filter != '':
            queryset = self.authorized_filters[self.filter][0](queryset)

        # Sort.
        if 'sort' in self.request.GET and self.request.GET['sort'].lower() in self.sorts:
            self.sort = self.request.GET['sort']
        else:
            self.sort = 'abc'
        queryset = self.sorts[self.sort.lower()][0](queryset)
        return queryset

    def get_context_data(self, **kwargs):
        context = super(ContentOfAuthor, self).get_context_data(**kwargs)
        context['sorts'] = []
        context['filters'] = []
        context['sort'] = self.sort.lower()
        context['filter'] = self.filter.lower()

        context['usr'] = self.user
        for sort in self.sorts.keys():
            context['sorts'].append({'key': sort, 'text': self.sorts[sort][1]})
        for filter_ in self.authorized_filters.keys():
            authorized_filter = self.authorized_filters[filter_]
            if self.user != self.request.user and not authorized_filter[2]:
                continue
            context['filters'].append({'key': filter_, 'text': authorized_filter[1], 'icon': authorized_filter[3]})
        return context
