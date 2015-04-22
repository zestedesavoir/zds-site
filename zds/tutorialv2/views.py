#!/usr/bin/python
# -*- coding: utf-8 -*-
from collections import OrderedDict
from datetime import datetime
from operator import attrgetter
from urllib import urlretrieve
from urlparse import urlparse, parse_qs
from django.template.loader import render_to_string
from zds.forum.models import Forum
from zds.tutorialv2.forms import BetaForm, MoveElementForm, RevokeValidationForm
from zds.tutorialv2.utils import try_adopt_new_child, TooDeepContainerError, get_target_tagged_tree
from zds.utils.forums import send_post, unlock_topic, lock_topic, create_topic
from zds.utils.models import Tag
from django.utils.decorators import method_decorator

try:
    import ujson as json_reader
except ImportError:
    try:
        import simplejson as json_reader
    except ImportError:
        import json as json_reader
import json
import json as json_writer
import shutil
import re
import zipfile
import os
import glob
import tempfile

from PIL import Image as ImagePIL
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.files import File
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Q, Count
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.encoding import smart_str
from django.views.decorators.http import require_POST
from git import Repo, BadObject

from zds.tutorialv2.forms import ContentForm, ContainerForm, ExtractForm, NoteForm, AskValidationForm, \
    AcceptValidationForm, RejectValidationForm, JsFiddleActivationForm, ImportContentForm, ImportNewContentForm
from models import PublishableContent, Container, Validation, ContentReaction, init_new_repo, get_content_from_json, \
    BadManifestError, Extract, default_slug_pool, PublishedContent
from utils import search_container_or_404, search_extract_or_404
from zds.gallery.models import Gallery, UserGallery, Image
from zds.member.decorator import can_write_and_read_now, LoginRequiredMixin, LoggedWithReadWriteHability
from zds.member.views import get_client_ip
from zds.utils import slugify
from zds.utils.models import Alert
from zds.utils.models import CommentLike, CommentDislike, SubCategory, HelpWriting, CategorySubCategory
from zds.utils.mps import send_mp
from zds.utils.templatetags.emarkdown import emarkdown
from zds.utils.tutorials import get_blob, export_tutorial_to_md
from django.utils.translation import ugettext as _
from django.views.generic import ListView, FormView, DeleteView, RedirectView
from zds.member.decorator import PermissionRequiredMixin
from zds.tutorialv2.mixins import SingleContentViewMixin, SingleContentPostMixin, SingleContentFormViewMixin, \
    SingleContentDetailViewMixin, SingleContentDownloadViewMixin, SingleOnlineContentDetailViewMixin, ContentTypeMixin
from git import GitCommandError
from zds.tutorialv2.utils import publish_content, FailureDuringPublication, unpublish_content
from django.utils.encoding import smart_text


class RedirectContentSEO(RedirectView):
    permanent = True

    def get_redirect_url(self, **kwargs):
        """Redirects the user to the new url"""
        obj = PublishableContent.objects.get(old_pk=kwargs["pk"])
        if obj is None or not obj.in_public():
            raise Http404

        obj = search_container_or_404(obj.load_version(public=True), kwargs)

        return obj.get_prod_path()


class ListContents(LoggedWithReadWriteHability, ListView):
    """
    Displays the list of offline contents (written by user)
    """
    context_object_name = 'contents'
    template_name = 'tutorialv2/index.html'

    def get_queryset(self):
        """
        Filter the content to obtain the list of content written by current user
        :return: list of articles
        """
        query_set = PublishableContent.objects.all().filter(authors__in=[self.request.user])
        # TODO: prefetch !tutorial.change_tutorial
        return query_set

    def get_context_data(self, **kwargs):
        """Separate articles and tutorials"""
        context = super(ListContents, self).get_context_data(**kwargs)
        context['articles'] = []
        context['tutorials'] = []
        for content in self.get_queryset():
            versioned = content.load_version()
            if content.type == 'ARTICLE':
                context['articles'].append(versioned)
            else:
                context['tutorials'].append(versioned)
        return context


class CreateContent(LoggedWithReadWriteHability, FormView):
    template_name = 'tutorialv2/create/content.html'
    model = PublishableContent
    form_class = ContentForm
    content = None

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
            img.slug = slugify(self.request.FILES["image"])
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
    online = False
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
            context["formValid"] = AcceptValidationForm(instance=validation, initial={"source": self.object.source})
            context["formReject"] = RejectValidationForm(instance=validation)

        if self.versioned_object.sha_public:
            context['formRevokeValidation'] = RevokeValidationForm(
                instance=self.versioned_object, initial={'version': self.versioned_object.sha_public})

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

        return context


class DisplayOnlineContent(SingleOnlineContentDetailViewMixin):
    """Base class that can show any online content"""

    model = PublishedContent
    template_name = 'tutorialv2/view/content_online.html'

    content_type = ""
    verbose_type_name = _(u'contenu')
    verbose_type_name_plural = _(u'contenus')

    def get_context_data(self, **kwargs):
        """Show the given tutorial if exists."""
        context = super(DisplayOnlineContent, self).get_context_data(**kwargs)

        # TODO: deal with messaging and stuff like this !!

        if self.request.user.has_perm("tutorial.change_tutorial"):
            context['formRevokeValidation'] = RevokeValidationForm(
                instance=self.versioned_object, initial={'version': self.versioned_object.sha_public})

        return context


class DisplayOnlineArticle(DisplayOnlineContent):
    """Displays the list of published articles"""

    content_type = "ARTICLE"
    verbose_type_name = _(u'article')
    verbose_type_name_plural = _(u'articles')


class DisplayOnlineTutorial(DisplayOnlineContent):
    """Displays the list of published tutorials"""

    content_type = "TUTORIAL"
    verbose_type_name = _(u'tutoriel')
    verbose_type_name_plural = _(u'tutoriels')


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

        return initial

    def form_valid(self, form):
        # TODO: tutorial <-> article
        versioned = self.versioned_object
        publishable = self.object

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
            img.slug = slugify(self.request.FILES["image"])
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

    def delete(self, request, *args, **kwargs):
        """rewrite delete() function to ensure repository deletion"""
        self.object = self.get_object()
        self.object.repo_delete()
        self.object.delete()

        return redirect(reverse('content:index'))


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

        :param zip_file: a `zipfile` object (with writing permissions)
        :param git_tree: Git tree (from `repository.commit(sha).tree`)
        """
        for blob in git_tree.blobs:  # first, add files :
            zip_file.writestr(blob.path, blob.data_stream.read())
        if len(git_tree.trees) is not 0:  # then, recursively add dirs :
            for subtree in git_tree.trees:
                insert_into_zip(zip_file, subtree)

    def get_contents(self):
        """
        :return: a zip file
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


class BadArchiveError(Exception):
    """ The exception that is raised when a bad archive is sent """
    message = u''

    def __init__(self, reason):
        self.message = reason


class UpdateContentWithArchive(LoggedWithReadWriteHability, SingleContentFormViewMixin):
    """Update a content using an archive"""

    template_name = 'tutorialv2/import/content.html'
    form_class = ImportContentForm

    @staticmethod
    def walk_container(container):
        """Iterator that yield each file in a Container

        :param container: the container
        :type container: Container
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
            raise BadArchiveError(_(u'Cette archive ne contient pas de fichier manifest.json'))

        # is the manifest ok ?
        json_ = json_reader.loads(manifest)
        try:
            versioned = get_content_from_json(json_, None, '')
        except BadManifestError as e:
            raise BadArchiveError(e.message)

        # is there everything in the archive ?
        for f in UpdateContentWithArchive.walk_content(versioned):
            try:
                zip_archive.getinfo(f)
            except KeyError:
                raise BadArchiveError(_(u'Le fichier "{}" n\'existe pas dans l\'archive').format(f))

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
                    introduction = unicode(zip_file.read(child.introduction), 'utf-8')
                if child.conclusion:
                    conclusion = unicode(zip_file.read(child.conclusion), 'utf-8')

                copy_to.repo_add_container(child.title, introduction, conclusion, do_commit=False)
                UpdateContentWithArchive.update_from_new_version_in_zip(copy_to.children[-1], child, zip_file)

            elif isinstance(child, Extract):
                text = unicode(zip_file.read(child.text), 'utf-8')
                copy_to.repo_add_extract(child.title, text, do_commit=False)

    def form_valid(self, form):
        versioned = self.versioned_object

        if self.request.FILES['archive']:
            zfile = zipfile.ZipFile(self.request.FILES['archive'], "r")
            # TODO catch exception here

            try:
                new_version = UpdateContentWithArchive.extract_content_from_zip(zfile)
            except BadArchiveError as e:
                messages.error(self.request, e.message)
                return super(UpdateContentWithArchive, self).form_invalid(form)
            else:
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
                UpdateContentWithArchive.update_from_new_version_in_zip(versioned, new_version, zfile)

                # and end up by a commit !!
                commit_message = form.cleaned_data['msg_commit']

                if commit_message == '':
                    commit_message = _(u'Importation d\'une archive contenant « {} »').format(new_version.title)

                sha = versioned.commit_changes(commit_message)

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
            zfile = zipfile.ZipFile(self.request.FILES['archive'], "r")

            try:
                new_content = UpdateContentWithArchive.extract_content_from_zip(zfile)
            except BadArchiveError as e:
                messages.error(self.request, e.message)
                return super(CreateContentFromArchive, self).form_invalid(form)
            else:
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
                UpdateContentWithArchive.update_from_new_version_in_zip(versioned, new_content, zfile)

                # and end up by a commit !!
                commit_message = form.cleaned_data['msg_commit']

                if commit_message == '':
                    commit_message = _(u'Importation d\'une archive contenant « {} »').format(new_content.title)

                sha = versioned.commit_changes(commit_message)

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
    authorized_for_staff = False

    def get_context_data(self, **kwargs):
        context = super(CreateContainer, self).get_context_data(**kwargs)

        context['container'] = search_container_or_404(self.versioned_object, self.kwargs)
        return context

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
    online = False
    sha = None
    must_be_author = False  # beta state does not need the author
    only_draft_version = False

    def get_context_data(self, **kwargs):
        """Show the given tutorial if exists."""
        context = super(DisplayContainer, self).get_context_data(**kwargs)
        context['container'] = search_container_or_404(context['content'], self.kwargs)
        context['containers_target'] = get_target_tagged_tree(context['container'], context['content'])

        # pagination: search for `previous` and `next`, if available
        if context['content'].type != 'ARTICLE' and not context['content'].has_extracts():
            chapters = context['content'].get_list_of_chapters()
            try:
                position = chapters.index(context['container'])
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

        return context


class DisplayOnlineContainer(SingleOnlineContentDetailViewMixin):
    """Base class that can show any content in any state"""

    template_name = 'tutorialv2/view/container_online.html'
    content_type = "TUTORIAL"  # obviously, an article cannot have container !

    def get_context_data(self, **kwargs):
        context = super(DisplayOnlineContainer, self).get_context_data(**kwargs)
        container = search_container_or_404(self.versioned_object, self.kwargs)

        context['container'] = container

        # pagination: search for `previous` and `next`, if available
        if not self.versioned_object.has_extracts():
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

        return context


class EditContainer(LoggedWithReadWriteHability, SingleContentFormViewMixin):
    template_name = 'tutorialv2/edit/container.html'
    form_class = ContainerForm
    content = None

    def get_context_data(self, **kwargs):
        context = super(EditContainer, self).get_context_data(**kwargs)
        form = kwargs.pop('form', None)
        context['container'] = form.initial['container']

        return context

    def get_initial(self):
        """rewrite function to pre-populate form"""
        initial = super(EditContainer, self).get_initial()
        container = search_container_or_404(self.versioned_object, self.kwargs)

        initial['title'] = container.title
        initial['introduction'] = container.get_introduction()
        initial['conclusion'] = container.get_conclusion()
        initial['container'] = container

        return initial

    def form_valid(self, form):
        container = search_container_or_404(self.versioned_object, self.kwargs)

        sha = container.repo_update(form.cleaned_data['title'],
                                    form.cleaned_data['introduction'],
                                    form.cleaned_data['conclusion'],
                                    form.cleaned_data['msg_commit'])

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
    authorized_for_staff = False

    def get_context_data(self, **kwargs):
        context = super(CreateExtract, self).get_context_data(**kwargs)
        context['container'] = search_container_or_404(self.versioned_object, self.kwargs)

        return context

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

        return context

    def get_initial(self):
        """rewrite function to pre-populate form"""
        initial = super(EditExtract, self).get_initial()
        extract = search_extract_or_404(self.versioned_object, self.kwargs)

        initial['title'] = extract.title
        initial['text'] = extract.get_text()
        initial['extract'] = extract

        return initial

    def form_valid(self, form):
        extract = search_extract_or_404(self.versioned_object, self.kwargs)

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
                raise Http404

        sha = to_delete.repo_delete()

        # then save
        self.object.sha_draft = sha
        self.object.update_date = datetime.now()
        self.object.save()

        return redirect(parent.get_absolute_url())


class DisplayHistory(LoggedWithReadWriteHability, SingleContentDetailViewMixin):
    """
    Display the whole modification history.
    This class has no reason to be adapted to any content type
    """

    model = PublishableContent
    template_name = "tutorialv2/view/history.html"

    def get_context_data(self, **kwargs):
        context = super(DisplayHistory, self).get_context_data(**kwargs)
        repo = self.versioned_object.repository
        logs = repo.head.reference.log()
        logs = sorted(logs, key=attrgetter("time"), reverse=True)
        context['logs'] = logs
        return context


class DisplayDiff(LoggedWithReadWriteHability, SingleContentDetailViewMixin):
    """
    Display the difference between two version of a content.
    Reference is always HEAD and compared version is a GET query parameter named sha
    this class has no reason to be adapted to any content type
    """

    model = PublishableContent
    template_name = "tutorialv2/view/diff.html"
    only_draft_version = False

    def get_context_data(self, **kwargs):
        context = super(DisplayDiff, self).get_context_data(**kwargs)

        # open git repo and find diff between displayed version and head
        repo = self.versioned_object.repository
        current_version_commit = repo.commit(self.sha)
        try:
            diff_with_head = current_version_commit.diff("HEAD~1")
            context['commit_msg'] = current_version_commit.message
            context["path_add"] = diff_with_head.iter_change_type("A")
            context["path_ren"] = diff_with_head.iter_change_type("R")
            context["path_del"] = diff_with_head.iter_change_type("D")
            context["path_maj"] = diff_with_head.iter_change_type("M")

        except GitCommandError:
            context['commit_msg'] = _(u"La création est le seul commit disponible")

            context["path_add"] = []
            context["path_ren"] = []
            context["path_del"] = []
            context["path_maj"] = []

        return context


class ManageBetaContent(LoggedWithReadWriteHability, SingleContentFormViewMixin):
    """
    Depending of the value of `self.action`, this class will behave differently;
    - if "set", it will active (of update) the beta
    - if "inactive", it will inactive the beta on the tutorial
    """

    model = PublishableContent
    form_class = BetaForm
    authorized_for_staff = False

    action = None

    @method_decorator(transaction.atomic)
    def dispatch(self, *args, **kwargs):
        super(ManageBetaContent, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        # check version:
        try:
            sha_beta = self.request.POST['version']
            beta_version = self.object.load_version(sha=sha_beta)
        except KeyError:
            raise Http404  # wrong POST data
        except BadObject:
            raise PermissionDenied  # version does not exists !

        # topic of the beta version:
        topic = self.object.beta_topic
        # perform actions:
        if self.action == 'inactive':
            self.object.sha_beta = None
            msg_post = render_to_string(
                'tutorialv2/messages/beta_desactivate.msg.html', {'content': beta_version}
            )
            send_post(topic, msg_post)
            lock_topic(topic)

        elif self.action == 'set':
            already_in_beta = self.object.in_beta()
            if already_in_beta and self.object.sha_beta == sha_beta:
                pass  # no need to perform additional actions
            else:
                self.object.sha_beta = sha_beta
                self.versioned_object.in_beta = True
                self.versioned_object.sha_beta = sha_beta

                msg = render_to_string(
                    'tutorialv2/messages/beta_activate_topic.msg.html',
                    {
                        'content': beta_version,
                        'url': settings.ZDS_APP['site']['url'] + self.versioned_object.get_absolute_url_beta()
                    }
                )

                if not topic:
                    # if first time putting the content in beta, send a message on the forum and a PM
                    forum = get_object_or_404(Forum, pk=settings.ZDS_APP['forum']['beta_forum_id'])

                    # find tags
                    # TODO: make a util's function of it
                    categories = self.object.subcategory.all()
                    names = [smart_text(category.title).lower() for category in categories]
                    existing_tags = Tag.objects.filter(title__in=names).all()
                    existing_tags_names =[tag.title for tag in existing_tags]
                    unexisting_tags = list(set(names) - set(existing_tags_names) )
                    all_tags = []
                    for tag in unexisting_tags:
                        new_tag = Tag()
                        new_tag.title = tag
                        new_tag.save()
                        all_tags.append(new_tag)
                    all_tags += existing_tags

                    create_topic(author=self.request.user,
                                 forum=forum,
                                 title=_(u"[beta][tutoriel]{0}").format(beta_version.title),
                                 subtitle=u"{}".format(beta_version.description),
                                 text=msg,
                                 related_publishable_content=self.object)

                    bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
                    msg_pm = render_to_string(
                        'tutorialv2/messages/beta_activate_pm.msg.html',
                        {
                            'content': beta_version,
                            'url': settings.ZDS_APP['site']['url'] + topic.get_absolute_url()
                        }
                    )
                    send_mp(bot,
                            self.object.authors.all(),
                            _(u"Tutoriel en beta : {0}").format(beta_version.title),
                            "",
                            msg_pm,
                            False)
                else:
                    categories = self.object.subcategory.all()
                    names = [smart_text(category.title).lower() for category in categories]
                    existing_tags = Tag.objects.filter(title__in=names).all()
                    existing_tags_names =[tag.title for tag in existing_tags]
                    unexisting_tags = list(set(names) - set(existing_tags_names) )
                    all_tags = []
                    for tag in unexisting_tags:
                        new_tag = Tag()
                        new_tag.title = tag
                        new_tag.save()
                        all_tags.append(new_tag)
                    all_tags += existing_tags
                    if not already_in_beta:
                        unlock_topic(topic)
                        msg_post = render_to_string(
                            'tutorialv2/messages/beta_reactivate.msg.html',
                            {
                                'content': beta_version,
                                'url': settings.ZDS_APP['site']['url'] + self.versioned_object.get_absolute_url_beta()
                            }
                        )
                    else:
                        msg_post = render_to_string(
                            'tutorialv2/messages/beta_update.msg.html',
                            {
                                'content': beta_version,
                                'url': settings.ZDS_APP['site']['url'] + self.versioned_object.get_absolute_url_beta()
                            }
                        )
                    send_post(topic, msg_post)

        self.object.save()
        topic = self.object.beta_topic
        topic.tags.add(all_tags)
        topic.save()
        self.success_url = self.versioned_object.get_absolute_url(version=sha_beta)
        return super(ManageBetaContent, self).form_valid(form)


class ListOnlineContents(ContentTypeMixin, ListView):
    """Displays the list of published contents"""

    context_object_name = 'public_contents'
    paginate_by = settings.ZDS_APP['content']['content_per_page']
    template_name = 'tutorialv2/index_online.html'
    tag = None

    def top_categories(self):
        """Get all the categories and their related subcategories associated with existing contents.
        The result is sorted by alphabetic order."""

        # TODO: since this is gonna be reused, it should go in zds/utils/tutorialsv2.py (and in topbar.py)

        subcategories_contents = PublishedContent.objects\
            .filter(content_type=self.content_type)\
            .values('content__subcategory').all()

        categories_from_subcategories = CategorySubCategory.objects\
            .filter(is_main=True)\
            .filter(subcategory__in=subcategories_contents)\
            .order_by('category__position', 'subcategory__title')\
            .select_related('subcategory', 'category')\
            .values('category__title', 'subcategory__title', 'subcategory__slug')\
            .all()

        categories = OrderedDict()

        for csc in categories_from_subcategories:
            key = csc['category__title']

            if key in categories:
                categories[key].append((csc['subcategory__title'], csc['subcategory__slug']))
            else:
                categories[key] = [(csc['subcategory__title'], csc['subcategory__slug'])]

        return categories

    def get_queryset(self):
        """Filter the contents to obtain the list of given type.
        If tag parameter is provided, only contents which have this category will be listed.

        :return: list of contents with the good type
        :rtype: list of PublishedContent
        """

        query_set = PublishedContent.objects\
            .prefetch_related("content")\
            .prefetch_related("content__subcategory")\
            .prefetch_related("content__authors")\
            .filter(content_type=self.content_type)

        if 'tag' in self.request.GET:
            self.tag = get_object_or_404(SubCategory, slug=self.request.GET.get('tag'))
            query_set = query_set.filter(content__subcategory__in=[self.tag])

        return query_set.order_by('-publication_date')

    def get_context_data(self, **kwargs):
        context = super(ListOnlineContents, self).get_context_data(**kwargs)

        context['tag'] = self.tag
        context['top_categories'] = self.top_categories()

        return context


class ListArticles(ListOnlineContents):
    """Displays the list of published articles"""

    content_type = "ARTICLE"


class ListTutorials(ListOnlineContents):
    """Displays the list of published tutorials"""

    content_type = "TUTORIAL"


class TutorialWithHelp(ListTutorials):
    """List all tutorial that needs help, i.e registered as needing at least one HelpWriting or is in beta
    for more documentation, have a look to ZEP 03 specification (fr)"""
    context_object_name = 'tutorials'
    template_name = 'tutorialv2/view/help.html'

    def get_queryset(self):
        """get only tutorial that need help and handle filtering if asked"""
        query_set = PublishableContent.objects \
            .annotate(total=Count('helps'), shasize=Count('sha_beta')) \
            .filter((Q(sha_beta__isnull=False) & Q(shasize__gt=0)) | Q(total__gt=0)) \
            .all()
        try:
            type_filter = self.request.GET.get('type')
            query_set = query_set.filter(helps_title__in=[type_filter])
        except KeyError:
            # if no filter, no need to change
            pass
        return query_set

    def get_context_data(self, **kwargs):
        """Add all HelpWriting objects registered to the context so that the template can use it"""
        context = super(TutorialWithHelp, self).get_context_data(**kwargs)
        context['helps'] = HelpWriting.objects.all()
        return context


# TODO ArticleWithHelp


# Staff actions.


class ValidationListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """List the validations, with possibilities of filters"""

    permissions = ["tutorial.change_tutorial"]
    context_object_name = "validations"
    template_name = "tutorialv2/validation/index.html"

    def get_queryset(self):

        # TODO: many filter at the same time ?
        # TODO: paginate ?

        queryset = Validation.objects\
            .prefetch_related("validator")\
            .prefetch_related("content")\
            .prefetch_related("content__authors")\
            .filter(Q(status="PENDING") | Q(status="PENDING_V"))

        # filtering by type
        try:
            type_ = self.request.GET["type"]
            if type_ == "orphan":
                queryset = queryset.filter(
                    validator__isnull=True,
                    status="PENDING")
            if type_ == "reserved":
                queryset = queryset.filter(
                    validator__isnull=True,
                    status="PENDING_V")
            if type_ == "article":
                queryset = queryset.filter(
                    content__type="ARTICLE")
            if type_ == "tuto":
                queryset = queryset.filter(
                    content__type="TUTORIAL")
            else:
                raise KeyError()
        except KeyError:
            pass

        # filtering by category
        try:
            category = get_object_or_404(SubCategory, pk=self.request.GET["subcategory"])
            queryset = queryset.filter(content__subcategory__in=[category])
        except KeyError:
            pass

        return queryset.order_by("date_proposition").all()

    def get_context_data(self, **kwargs):
        context = super(ValidationListView, self).get_context_data(**kwargs)

        if 'subcategory' in self.request.GET:
            context['category'] = get_object_or_404(SubCategory, pk=self.request.GET["subcategory"])
            # TODO : two times the same request, here

        return context


class ActivateJSFiddleInContent(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """Handles changes a validator or staff member can do on the js fiddle support of the provided content
    Only those members can do it"""

    permissions = ["tutorial.change_tutorial"]
    form_class = JsFiddleActivationForm
    http_method_names = ["post"]

    def form_valid(self, form):
        """Change the js fiddle support of content and redirect to the view page """
        content = get_object_or_404(PublishableContent, pk=form.data["pk"])
        content.js_support = "js_support" in form.cleaned_data and form.data["js_support"] == u"True"
        content.save()
        return redirect(content.load_version().get_absolute_url())


class AskValidationForContent(LoggedWithReadWriteHability, SingleContentFormViewMixin):
    """User ask validation for his tutorial. Staff member can also to that"""

    prefetch_all = False
    form_class = AskValidationForm

    def get_form_kwargs(self):
        kwargs = super(AskValidationForContent, self).get_form_kwargs()
        kwargs['content'] = self.versioned_object
        return kwargs

    def form_valid(self, form):
        old_validation = Validation.objects.filter(content__pk=self.object.pk, status__in=['PENDING_V']).first()

        if old_validation:
            old_validator = old_validation.validator
            Validation.objects.filter(content__pk=self.object.pk, status__in=['PENDING', 'PENDING_V']).delete()
        else:
            old_validator = None

        # create a "validation" object
        validation = Validation()
        validation.content = self.object
        validation.date_proposition = datetime.now()
        validation.comment_authors = form.cleaned_data['text']
        validation.version = form.cleaned_data['version']
        validation.save()

        # warn the former validator that an update has been made, if any
        if old_validator:
            validation.validator = old_validator
            # TODO: why not let the validator be the same using PENDING_V ?

            bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
            msg = render_to_string(
                'tutorialv2/messages/validation_change.msg.html',
                {
                    'content': self.versioned_object,
                    'url': self.versioned_object.get_absolute_url() + '?version=' + form.cleaned_data['version'],
                    'url_history': reverse('content:history', args=[self.object.pk, self.object.slug])
                })

            send_mp(
                bot,
                [old_validator],
                _(u"Validation : mise à jour de « {} »").format(self.versioned_object.title),
                _(u"Une nouvelle version a été envoyée en validation"),
                msg,
                False,
            )

        # update the content with the source and the version of the validation
        self.object.source = form.cleaned_data["source"]
        self.object.sha_validation = validation.version
        self.object.save()

        messages.success(self.request, _(u"Votre demande de validation a été envoyée à l'équipe."))

        self.success_url = self.versioned_object.get_absolute_url(version=self.sha)
        return super(AskValidationForContent, self).form_valid(form)


# User actions on tutorial.


class ReserveValidation(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """Reserve or remove the reservation on a content"""

    permissions = ["tutorial.change_tutorial"]

    def post(self, request, *args, **kwargs):
        validation = get_object_or_404(Validation, pk=kwargs["pk"])
        if validation.validator:
            validation.validator = None
            validation.date_reserve = None
            validation.status = "PENDING"
            validation.save()
            messages.info(request, _(u"Ce contenu n'est plus réservé"))
            return redirect(reverse("content:list-validation"))
        else:
            validation.validator = request.user
            validation.date_reserve = datetime.now()
            validation.status = "PENDING_V"
            validation.save()
            messages.info(request, _(u"Ce contenu a bien été réservé par {0}").format(request.user.username))

            return redirect(
                reverse("content:view", args=[validation.content.pk, validation.content.slug]) +
                "?version=" + validation.version
            )


class HistoryOfValidationDisplay(LoginRequiredMixin, PermissionRequiredMixin, SingleContentDetailViewMixin):

    model = PublishableContent
    permissions = ["tutorial.change_tutorial"]
    template_name = "tutorialv2/validation/history.html"

    def get_context_data(self, **kwargs):
        context = super(HistoryOfValidationDisplay, self).get_context_data()

        context["validations"] = Validation.objects\
            .prefetch_related("validator")\
            .filter(content__pk=self.object.pk)\
            .order_by("date_proposition").all()

        return context


class RejectValidation(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """Reject the publication"""

    permissions = ["tutorial.change_tutorial"]
    form_class = RejectValidationForm

    def get_form_kwargs(self):
        kwargs = super(RejectValidation, self).get_form_kwargs()
        kwargs['instance'] = Validation.objects.filter(pk=self.kwargs['pk']).last()
        return kwargs

    def form_valid(self, form):

        user = self.request.user

        validation = Validation.objects.filter(pk=self.kwargs['pk']).last()

        if not validation:
            raise PermissionDenied

        if validation.validator != user:
            raise PermissionDenied

        if validation.status != 'PENDING_V':
            raise PermissionDenied

        # reject validation:
        validation.comment_validator = form.cleaned_data['text']
        validation.status = "REJECT"
        validation.date_validation = datetime.now()
        validation.save()

        validation.content.sha_validation = None
        validation.content.save()

        # send PM
        versioned = validation.content.load_version(sha=validation.version)
        msg = render_to_string(
            'tutorialv2/messages/validation_reject.msg.html',
            {
                'content': versioned,
                'url': versioned.get_absolute_url() + '?version=' + validation.version,
                'validator': validation.validator,
                'message_reject': '\n'.join(['> ' + a for a in form.cleaned_data['text'].split('\n')])
            })

        bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
        send_mp(
            bot,
            validation.content.authors.all(),
            _(u"Rejet de « {} »").format(validation.content.title),
            _(u"Désolé"),
            msg,
            True,
            direct=False
        )

        messages.info(self.request, _(u'Le contenu a bien été refusé'))
        self.success_url = reverse('content:list-validation')
        return super(RejectValidation, self).form_valid(form)


class AcceptValidation(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """Publish the content"""

    permissions = ["tutorial.change_tutorial"]
    form_class = AcceptValidationForm

    def get_form_kwargs(self):
        kwargs = super(AcceptValidation, self).get_form_kwargs()
        kwargs['instance'] = Validation.objects.filter(pk=self.kwargs['pk']).last()
        return kwargs

    def form_valid(self, form):

        user = self.request.user
        validation = form.validation

        if not validation:
            raise PermissionDenied

        if validation.validator != user:
            raise PermissionDenied

        # get database representation and validated version
        db_object = validation.content
        versioned = db_object.load_version(sha=validation.version)
        self.success_url = versioned.get_absolute_url(version=validation.version)

        try:
            published = publish_content(db_object, versioned, is_major_update=form.cleaned_data['is_major'])
        except FailureDuringPublication as e:
            messages.error(self.request, e.message)
        else:
            # save in database
            is_update = db_object.sha_public and db_object.sha_public != ''
            db_object.sha_public = validation.version
            db_object.source = form.cleaned_data['source']
            db_object.sha_validation = None

            if form.cleaned_data['is_major']:
                db_object.pubdate = datetime.now()

            db_object.save()

            # save validation object
            validation.comment_validator = form.cleaned_data['text']
            validation.status = "ACCEPT"
            validation.date_validation = datetime.now()
            validation.save()

            # TODO: deal with other kind of publications (HTML, PDF, archive, ...)

            if is_update:
                msg = render_to_string(
                    'tutorialv2/messages/validation_accept_update.html',
                    {
                        'content': versioned,
                        'url': published.get_absolute_url_online(),
                        'validator': validation.validator
                    })
            else:
                msg = render_to_string(
                    'tutorialv2/messages/validation_accept_content.msg.html',
                    {
                        'content': versioned,
                        'url': published.get_absolute_url_online(),
                        'validator': validation.validator
                    })

            bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
            send_mp(
                bot,
                db_object.authors.all(),
                _(u"Publication de « {} »").format(versioned.title),
                _(u"Merci !"),
                msg,
                True,
                direct=False
            )

            messages.success(self.request, _(u'Le contenu a bien été validé.'))
            self.success_url = published.get_absolute_url_online()

        return super(AcceptValidation, self).form_valid(form)


class RevokeValidation(LoginRequiredMixin, PermissionRequiredMixin, SingleContentFormViewMixin):
    """Unpublish a content and reverse the situation back to a pending validation"""

    permissions = ["tutorial.change_tutorial"]
    form_class = RevokeValidationForm

    def get_form_kwargs(self):
        kwargs = super(RevokeValidation, self).get_form_kwargs()
        kwargs['instance'] = self.versioned_object
        return kwargs

    def form_valid(self, form):

        versioned = self.versioned_object

        if form.cleaned_data['version'] != self.object.sha_public:
            raise PermissionDenied

        validation = Validation.objects.filter(
            content=self.object,
            version=self.object.sha_public).latest("date_proposition")

        if not validation:
            raise PermissionDenied

        unpublish_content(self.object)

        validation.status = "PENDING"
        validation.date_validation = None
        validation.save()

        self.object.sha_public = None
        self.object.sha_validation = validation.version
        self.object.pubdate = None
        self.object.save()

        # send PM
        msg = render_to_string(
            'tutorialv2/messages/validation_revoke.msg.html',
            {
                'content': versioned,
                'url': versioned.get_absolute_url() + '?version=' + validation.version,
                'admin': self.request.user,
                'message_reject': '\n'.join(['> ' + a for a in form.cleaned_data['text'].split('\n')])
            })

        bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
        send_mp(
            bot,
            validation.content.authors.all(),
            _(u"Dépublication de « {} »").format(validation.content.title),
            _(u"Désolé ..."),
            msg,
            True,
            direct=False
        )

        messages.success(self.request, _(u"Le tutoriel a bien été dépublié."))
        self.success_url = self.versioned_object.get_absolute_url() + "?version=" + validation.version

        return super(RevokeValidation, self).form_valid(form)


class MoveChild(LoginRequiredMixin, SingleContentPostMixin, FormView):

    model = PublishableContent
    permissions = ["tutorial.change_tutorial"]
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
            raise Http404

        if child_slug == '':
            raise Http404

        if base_container_slug == versioned.slug:
            parent = versioned
        else:
            search_params = {}

            if form.data['first_level_slug'] != '':
                search_params['parent_container_slug'] = form.data['first_level_slug']
                search_params['container_slug'] = base_container_slug
            else:
                search_params['container_slug'] = base_container_slug
            parent = search_container_or_404(versioned, search_params)

        try:
            child = parent.children_dict[child_slug]
            if form.data['moving_method'] == MoveElementForm.MOVE_UP:
                parent.move_child_up(child_slug)
            if form.data['moving_method'] == MoveElementForm.MOVE_DOWN:
                parent.move_child_down(child_slug)
            if form.data['moving_method'][0:len(MoveElementForm.MOVE_AFTER)] == MoveElementForm.MOVE_AFTER:
                target = form.data['moving_method'][len(MoveElementForm.MOVE_AFTER) + 1:]
                if not parent.has_child_with_path(target):
                    if "/" not in target:
                        target_parent = versioned
                    else:
                        target_parent = search_container_or_404(versioned, "/".join(target.split("/")[:-1]))

                        if target.split("/")[-1] not in target_parent.children_dict:
                            raise Http404
                    child = target_parent.children_dict[target.split("/")[-1]]
                    try_adopt_new_child(target_parent, parent.children_dict[child_slug])
                    parent = target_parent
                parent.move_child_after(child_slug, target.split("/")[-1])
            if form.data['moving_method'][0:len(MoveElementForm.MOVE_BEFORE)] == MoveElementForm.MOVE_BEFORE:
                target = form.data['moving_method'][len(MoveElementForm.MOVE_BEFORE) + 1:]
                if not parent.has_child_with_path(target):
                    if "/" not in target:
                        target_parent = versioned
                    else:
                        target_parent = search_container_or_404(versioned, "/".join(target.split("/")[:-1]))

                        if target.split("/")[-1] not in target_parent.children_dict:
                            raise Http404
                    child = target_parent.children_dict[target.split("/")[-1]]
                    try_adopt_new_child(target_parent, parent.children_dict[child_slug])

                    parent = target_parent
                parent.move_child_before(child_slug, target.split("/")[-1])

            versioned.dump_json()
            parent.repo_update(parent.title,
                               parent.get_introduction(),
                               parent.get_conclusion(),
                               _(u"Déplacement de ") + child_slug)
            content.sha_draft = versioned.sha_draft
            content.save()
            messages.info(self.request, _(u"L'élément a bien été déplacé."))
        except TooDeepContainerError:
            messages.error(self.request, _(u'Cette section contient déjà trop de sous-section pour devenir'
                                           u' la sous-section d\'une autre section.'))
        except ValueError:
            raise Http404
        except IndexError:
            messages.warning(self.request, _(u"L'élément est déjà à la place souhaitée."))
        except TypeError:
            messages.error(self.request, _(u"L'élément ne peut pas être déplacé à cet endroit"))

        if base_container_slug == versioned.slug:
            return redirect(reverse("content:view", args=[content.pk, content.slug]))
        else:
            return redirect(child.get_absolute_url())


@can_write_and_read_now
@login_required
@require_POST
@permission_required("tutorial.change_tutorial", raise_exception=True)
def reject_tutorial(request):
    """Staff reject tutorial of an author."""

    # Retrieve current tutorial;

    try:
        tutorial_pk = request.POST["tutorial"]
    except KeyError:
        raise Http404
    tutorial = get_object_or_404(PublishableContent, pk=tutorial_pk)
    validation = Validation.objects.filter(
        tutorial__pk=tutorial_pk,
        version=tutorial.sha_validation).latest("date_proposition")

    if request.user == validation.validator:
        validation.comment_validator = request.POST["text"]
        validation.status = "REJECT"
        validation.date_validation = datetime.now()
        validation.save()

        # Remove sha_validation because we rejected this version of the tutorial.

        tutorial.sha_validation = None
        tutorial.pubdate = None
        tutorial.save()
        messages.info(request, _(u"Le tutoriel a bien été refusé."))
        comment_reject = '\n'.join(['> ' + line for line in validation.comment_validator.split('\n')])
        # send feedback
        msg = (
            _(u'Désolé, le zeste **{0}** n\'a malheureusement '
              u'pas passé l’étape de validation. Mais ne désespère pas, '
              u'certaines corrections peuvent surement être faite pour '
              u'l’améliorer et repasser la validation plus tard. '
              u'Voici le message que [{1}]({2}), ton validateur t\'a laissé:\n\n`{3}`\n\n'
              u'N\'hésite pas a lui envoyer un petit message pour discuter '
              u'de la décision ou demander plus de détail si tout cela te '
              u'semble injuste ou manque de clarté.')
            .format(tutorial.title,
                    validation.validator.username,
                    settings.ZDS_APP['site']['url'] + validation.validator.profile.get_absolute_url(),
                    comment_reject))
        bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
        send_mp(
            bot,
            tutorial.authors.all(),
            _(u"Refus de Validation : {0}").format(tutorial.title),
            "",
            msg,
            True,
            direct=False,
        )
        return redirect(tutorial.get_absolute_url() + "?version=" + validation.version)
    else:
        messages.error(request,
                       _(u"Vous devez avoir réservé ce tutoriel "
                         u"pour pouvoir le refuser."))
        return redirect(tutorial.get_absolute_url() + "?version=" + validation.version)


@can_write_and_read_now
@login_required
@require_POST
@permission_required("tutorial.change_tutorial", raise_exception=True)
def valid_tutorial(request):
    """Staff valid tutorial of an author."""

    # Retrieve current tutorial;

    try:
        tutorial_pk = request.POST["tutorial"]
    except KeyError:
        raise Http404
    tutorial = get_object_or_404(PublishableContent, pk=tutorial_pk)
    validation = Validation.objects.filter(
        tutorial__pk=tutorial_pk,
        version=tutorial.sha_validation).latest("date_proposition")

    if request.user == validation.validator:
        (output, err) = mep(tutorial, tutorial.sha_validation)
        messages.info(request, output)
        messages.error(request, err)
        validation.comment_validator = request.POST["text"]
        validation.status = "ACCEPT"
        validation.date_validation = datetime.now()
        validation.save()

        # Update sha_public with the sha of validation. We don't update sha_draft.
        # So, the user can continue to edit his tutorial in offline.

        if request.POST.get('is_major', False) or tutorial.sha_public is None or tutorial.sha_public == '':
            tutorial.pubdate = datetime.now()
        tutorial.sha_public = validation.version
        tutorial.source = request.POST["source"]
        tutorial.sha_validation = None
        tutorial.save()
        messages.success(request, _(u"Le tutoriel a bien été validé."))

        # send feedback

        msg = (
            _(u'Félicitations ! Le zeste [{0}]({1}) '
              u'a été publié par [{2}]({3}) ! Les lecteurs du monde entier '
              u'peuvent venir l\'éplucher et réagir a son sujet. '
              u'Je te conseille de rester a leur écoute afin '
              u'd\'apporter des corrections/compléments.'
              u'Un Tutoriel vivant et a jour est bien plus lu '
              u'qu\'un sujet abandonné !')
            .format(tutorial.title,
                    settings.ZDS_APP['site']['url'] + tutorial.get_absolute_url_online(),
                    validation.validator.username,
                    settings.ZDS_APP['site']['url'] + validation.validator.profile.get_absolute_url(), ))
        bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
        send_mp(
            bot,
            tutorial.authors.all(),
            _(u"Publication : {0}").format(tutorial.title),
            "",
            msg,
            True,
            direct=False,
        )
        return redirect(tutorial.get_absolute_url() + "?version=" + validation.version)
    else:
        messages.error(request,
                       _(u"Vous devez avoir réservé ce tutoriel "
                         u"pour pouvoir le valider."))
        return redirect(tutorial.get_absolute_url() + "?version=" + validation.version)


@can_write_and_read_now
@login_required
@permission_required("tutorial.change_tutorial", raise_exception=True)
@require_POST
def invalid_tutorial(request, tutorial_pk):
    """Staff invalid tutorial of an author."""

    # Retrieve current tutorial

    tutorial = get_object_or_404(PublishableContent, pk=tutorial_pk)
    un_mep(tutorial)
    validation = Validation.objects.filter(
        tutorial__pk=tutorial_pk,
        version=tutorial.sha_public).latest("date_proposition")
    validation.status = "PENDING"
    validation.date_validation = None
    validation.save()

    # Only update sha_validation because contributors can contribute on
    # rereading version.

    tutorial.sha_public = None
    tutorial.sha_validation = validation.version
    tutorial.pubdate = None
    tutorial.save()
    messages.success(request, _(u"Le tutoriel a bien été dépublié."))
    return redirect(tutorial.get_absolute_url() + "?version=" + validation.version)


def find_tuto(request, pk_user):
    try:
        type = request.GET["type"]
    except KeyError:
        type = None
    display_user = get_object_or_404(User, pk=pk_user)
    if type == "beta":
        tutorials = PublishableContent.objects.all().filter(
            authors__in=[display_user],
            sha_beta__isnull=False).exclude(sha_beta="").order_by("-pubdate")

        tuto_versions = []
        for tutorial in tutorials:
            mandata = tutorial.load_json_for_public(sha=tutorial.sha_beta)
            tutorial.load_dic(mandata, sha=tutorial.sha_beta)
            tuto_versions.append(mandata)

        return render(request, "tutorial/member/beta.html",
                      {"tutorials": tuto_versions, "usr": display_user})
    else:
        tutorials = PublishableContent.objects.all().filter(
            authors__in=[display_user],
            sha_public__isnull=False).exclude(sha_public="").order_by("-pubdate")

        tuto_versions = []
        for tutorial in tutorials:
            mandata = tutorial.load_json_for_public()
            tutorial.load_dic(mandata)
            tuto_versions.append(mandata)

        return render(request, "tutorial/member/online.html", {"tutorials": tuto_versions,
                                                               "usr": display_user})


def upload_images(images, tutorial):
    mapping = OrderedDict()

    # download images

    zfile = zipfile.ZipFile(images, "a")
    os.makedirs(os.path.abspath(os.path.join(tutorial.get_repo_path(), "images")))
    for i in zfile.namelist():
        ph_temp = os.path.abspath(os.path.join(tutorial.get_repo_path(), i))
        try:
            data = zfile.read(i)
            fp = open(ph_temp, "wb")
            fp.write(data)
            fp.close()
            f = File(open(ph_temp, "rb"))
            f.name = os.path.basename(i)
            pic = Image()
            pic.gallery = tutorial.gallery
            pic.title = os.path.basename(i)
            pic.pubdate = datetime.now()
            pic.physical = f
            pic.save()
            mapping[i] = pic.physical.url
            f.close()
        except IOError:
            try:
                os.makedirs(ph_temp)
            except OSError:
                pass
    zfile.close()
    return mapping


def replace_real_url(md_text, dict):
    for (dt_old, dt_new) in dict.iteritems():
        md_text = md_text.replace(dt_old, dt_new)
    return md_text


def insert_into_zip(zip_file, git_tree):
    """recursively add files from a git_tree to a zip archive"""
    for blob in git_tree.blobs:  # first, add files :
        zip_file.writestr(blob.path, blob.data_stream.read())
    if len(git_tree.trees) is not 0:  # then, recursively add dirs :
        for subtree in git_tree.trees:
            insert_into_zip(zip_file, subtree)


def download(request):
    """Download a tutorial."""
    tutorial = get_object_or_404(PublishableContent, pk=request.GET["tutoriel"])

    repo_path = os.path.join(settings.ZDS_APP['tutorial']['repo_path'], tutorial.get_phy_slug())
    repo = Repo(repo_path)
    sha = tutorial.sha_draft
    if 'online' in request.GET and tutorial.in_public():
        sha = tutorial.sha_public
    elif request.user not in tutorial.authors.all():
        if not request.user.has_perm('tutorial.change_tutorial'):
            raise PermissionDenied  # Only authors can download draft version
    zip_path = os.path.join(tempfile.gettempdir(), tutorial.slug + '.zip')
    zip_file = zipfile.ZipFile(zip_path, 'w')
    insert_into_zip(zip_file, repo.commit(sha).tree)
    zip_file.close()
    response = HttpResponse(open(zip_path, "rb").read(), content_type="application/zip")
    response["Content-Disposition"] = "attachment; filename={0}.zip".format(tutorial.slug)
    os.remove(zip_path)
    return response


@permission_required("tutorial.change_tutorial", raise_exception=True)
def download_markdown(request):
    """Download a markdown tutorial."""

    tutorial = get_object_or_404(PublishableContent, pk=request.GET["tutoriel"])
    phy_path = os.path.join(
        tutorial.get_prod_path(),
        tutorial.slug +
        ".md")
    response = HttpResponse(
        open(phy_path, "rb").read(),
        content_type="application/txt")
    response["Content-Disposition"] = \
        "attachment; filename={0}.md".format(tutorial.slug)
    return response


def download_html(request):
    """Download a pdf tutorial."""

    tutorial = get_object_or_404(PublishableContent, pk=request.GET["tutoriel"])
    phy_path = os.path.join(
        tutorial.get_prod_path(),
        tutorial.slug +
        ".html")
    if not os.path.isfile(phy_path):
        raise Http404
    response = HttpResponse(
        open(phy_path, "rb").read(),
        content_type="text/html")
    response["Content-Disposition"] = \
        "attachment; filename={0}.html".format(tutorial.slug)
    return response


def download_pdf(request):
    """Download a pdf tutorial."""

    tutorial = get_object_or_404(PublishableContent, pk=request.GET["tutoriel"])
    phy_path = os.path.join(
        tutorial.get_prod_path(),
        tutorial.slug +
        ".pdf")
    if not os.path.isfile(phy_path):
        raise Http404
    response = HttpResponse(
        open(phy_path, "rb").read(),
        content_type="application/pdf")
    response["Content-Disposition"] = \
        "attachment; filename={0}.pdf".format(tutorial.slug)
    return response


def download_epub(request):
    """Download an epub tutorial."""

    tutorial = get_object_or_404(PublishableContent, pk=request.GET["tutoriel"])
    phy_path = os.path.join(
        tutorial.get_prod_path(),
        tutorial.slug +
        ".epub")
    if not os.path.isfile(phy_path):
        raise Http404
    response = HttpResponse(
        open(phy_path, "rb").read(),
        content_type="application/epub")
    response["Content-Disposition"] = \
        "attachment; filename={0}.epub".format(tutorial.slug)
    return response


def get_url_images(md_text, pt):
    """find images urls in markdown text and download this."""

    regex = ur"(!\[.*?\]\()(.+?)(\))"
    unknow_path = os.path.join(settings.SITE_ROOT, "fixtures", "noir_black.png")

    # if text is empty don't download

    if md_text is not None:
        imgs = re.findall(regex, md_text)
        for img in imgs:
            real_url = img[1]
            # decompose images
            parse_object = urlparse(real_url)
            if parse_object.query != '':
                resp = parse_qs(urlparse(img[1]).query, keep_blank_values=True)
                real_url = resp["u"][0]
                parse_object = urlparse(real_url)

            # if link is http type
            if parse_object.scheme in ["http", "https", "ftp"] or \
               parse_object.netloc[:3] == "www" or \
               parse_object.path[:3] == "www":
                (filepath, filename) = os.path.split(parse_object.path)
                if not os.path.isdir(os.path.join(pt, "images")):
                    os.makedirs(os.path.join(pt, "images"))

                # download image
                down_path = os.path.abspath(os.path.join(pt, "images", filename))
                try:
                    urlretrieve(real_url, down_path)
                    try:
                        ext = filename.split(".")[-1]
                        im = ImagePIL.open(down_path)
                        # if image is gif, convert to png
                        if ext == "gif":
                            im.save(os.path.join(pt, "images", filename.split(".")[0] + ".png"))
                    except IOError:
                        ext = filename.split(".")[-1]
                        im = ImagePIL.open(unknow_path)
                        if ext == "gif":
                            im.save(os.path.join(pt, "images", filename.split(".")[0] + ".png"))
                        else:
                            im.save(os.path.join(pt, "images", filename))
                except IOError:
                    pass
            else:
                # relative link
                srcfile = settings.SITE_ROOT + real_url
                if os.path.isfile(srcfile):
                    dstroot = pt + real_url
                    dstdir = os.path.dirname(dstroot)
                    if not os.path.exists(dstdir):
                        os.makedirs(dstdir)
                    shutil.copy(srcfile, dstroot)

                    try:
                        ext = dstroot.split(".")[-1]
                        im = ImagePIL.open(dstroot)
                        # if image is gif, convert to png
                        if ext == "gif":
                            im.save(os.path.join(dstroot.split(".")[0] + ".png"))
                    except IOError:
                        ext = dstroot.split(".")[-1]
                        im = ImagePIL.open(unknow_path)
                        if ext == "gif":
                            im.save(os.path.join(dstroot.split(".")[0] + ".png"))
                        else:
                            im.save(os.path.join(dstroot))


def sub_urlimg(g):
    start = g.group("start")
    url = g.group("url")
    parse_object = urlparse(url)
    if parse_object.query != '':
        resp = parse_qs(urlparse(url).query, keep_blank_values=True)
        parse_object = urlparse(resp["u"][0])
    (filepath, filename) = os.path.split(parse_object.path)
    if filename != '':
        mark = g.group("mark")
        ext = filename.split(".")[-1]
        if ext == "gif":
            if parse_object.scheme in ("http", "https") or \
               parse_object.netloc[:3] == "www" or \
               parse_object.path[:3] == "www":
                url = os.path.join("images", filename.split(".")[0] + ".png")
            else:
                url = (url.split(".")[0])[1:] + ".png"
        else:
            if parse_object.scheme in ("http", "https") or \
               parse_object.netloc[:3] == "www" or \
               parse_object.path[:3] == "www":
                url = os.path.join("images", filename)
            else:
                url = url[1:]
        end = g.group("end")
        return start + mark + url + end
    else:
        return start


def markdown_to_out(md_text):
    return re.sub(ur"(?P<start>)(?P<mark>!\[.*?\]\()(?P<url>.+?)(?P<end>\))", sub_urlimg,
                  md_text)


def mep(tutorial, sha):
    (output, err) = (None, None)
    repo = Repo(tutorial.get_path())
    manifest = get_blob(repo.commit(sha).tree, "manifest.json")
    tutorial_version = json_reader.loads(manifest)

    prod_path = tutorial.get_prod_path(sha)

    pattern = os.path.join(settings.ZDS_APP['tutorial']['repo_public_path'], str(tutorial.pk) + '_*')
    del_paths = glob.glob(pattern)
    for del_path in del_paths:
        if os.path.isdir(del_path):
            try:
                shutil.rmtree(del_path)
            except OSError:
                shutil.rmtree(u"\\\\?\{0}".format(del_path))
                # WARNING: this can throw another OSError
    shutil.copytree(tutorial.get_path(), prod_path)
    repo.head.reset(commit=sha, index=True, working_tree=True)

    # collect md files

    fichiers = []
    fichiers.append(tutorial_version["introduction"])
    fichiers.append(tutorial_version["conclusion"])
    if "parts" in tutorial_version:
        for part in tutorial_version["parts"]:
            fichiers.append(part["introduction"])
            fichiers.append(part["conclusion"])
            if "chapters" in part:
                for chapter in part["chapters"]:
                    fichiers.append(chapter["introduction"])
                    fichiers.append(chapter["conclusion"])
                    if "extracts" in chapter:
                        for extract in chapter["extracts"]:
                            fichiers.append(extract["text"])
    if "chapter" in tutorial_version:
        chapter = tutorial_version["chapter"]
        if "extracts" in tutorial_version["chapter"]:
            for extract in chapter["extracts"]:
                fichiers.append(extract["text"])

    # convert markdown file to html file

    for fichier in fichiers:
        md_file_contenu = get_blob(repo.commit(sha).tree, fichier)

        # download images

        get_url_images(md_file_contenu, prod_path)

        # convert to out format
        out_file = open(os.path.join(prod_path, fichier), "w")
        if md_file_contenu is not None:
            out_file.write(markdown_to_out(md_file_contenu.encode("utf-8")))
        out_file.close()
        target = os.path.join(prod_path, fichier + ".html")
        os.chdir(os.path.dirname(target))
        try:
            html_file = open(target, "w")
        except IOError:

            # handle limit of 255 on windows

            target = u"\\\\?\{0}".format(target)
            html_file = open(target, "w")
        if tutorial.js_support:
            is_js = "js"
        else:
            is_js = ""
        if md_file_contenu is not None:
            html_file.write(emarkdown(md_file_contenu, is_js))
        html_file.close()

    # load markdown out

    contenu = export_tutorial_to_md(tutorial, sha).lstrip()
    out_file = open(os.path.join(prod_path, tutorial.slug + ".md"), "w")
    out_file.write(smart_str(contenu))
    out_file.close()

    # define whether to log pandoc's errors

    pandoc_debug_str = ""
    if settings.PANDOC_LOG_STATE:
        pandoc_debug_str = " 2>&1 | tee -a " + settings.PANDOC_LOG

    # load pandoc

    os.chdir(prod_path)
    os.system(settings.PANDOC_LOC +
              "pandoc --latex-engine=xelatex -s -S --toc " +
              os.path.join(prod_path, tutorial.slug) +
              ".md -o " + os.path.join(prod_path, tutorial.slug) + ".html" + pandoc_debug_str)
    os.system(settings.PANDOC_LOC + "pandoc " + settings.PANDOC_PDF_PARAM + " " +
              os.path.join(prod_path, tutorial.slug) + ".md " +
              "-o " + os.path.join(prod_path, tutorial.slug) +
              ".pdf" + pandoc_debug_str)
    os.system(settings.PANDOC_LOC + "pandoc -s -S --toc " +
              os.path.join(prod_path, tutorial.slug) +
              ".md -o " + os.path.join(prod_path, tutorial.slug) + ".epub" + pandoc_debug_str)
    os.chdir(settings.SITE_ROOT)
    return (output, err)


def un_mep(tutorial):
    del_paths = glob.glob(os.path.join(settings.ZDS_APP['tutorial']['repo_public_path'],
                                       str(tutorial.pk) + '_*'))
    for del_path in del_paths:
        if os.path.isdir(del_path):
            try:
                shutil.rmtree(del_path)
            except OSError:
                shutil.rmtree(u"\\\\?\{0}".format(del_path))
                # WARNING: this can throw another OSError


@can_write_and_read_now
@login_required
def answer(request):
    """Adds an answer from a user to an tutorial."""

    try:
        tutorial_pk = request.GET["tutorial"]
    except KeyError:
        raise Http404

    # Retrieve current tutorial.

    tutorial = get_object_or_404(PublishableContent, pk=tutorial_pk)

    # Making sure reactioning is allowed

    if tutorial.is_locked:
        raise PermissionDenied

    # Check that the user isn't spamming

    if tutorial.antispam(request.user):
        raise PermissionDenied

    # Retrieve 3 last notes of the current tutorial.

    notes = ContentReaction.objects.filter(tutorial=tutorial).order_by("-pubdate")[:3]

    # If there is a last notes for the tutorial, we save his pk. Otherwise, we
    # save 0.

    last_note_pk = 0
    if tutorial.last_note:
        last_note_pk = tutorial.last_note.pk

    # Retrieve lasts notes of the current tutorial.
    notes = ContentReaction.objects.filter(tutorial=tutorial) \
        .prefetch_related() \
        .order_by("-pubdate")[:settings.ZDS_APP['forum']['posts_per_page']]

    # User would like preview his post or post a new note on the tutorial.

    if request.method == "POST":
        data = request.POST
        newnote = last_note_pk != int(data["last_note"])

        # Using the « preview button », the « more » button or new note

        if "preview" in data or newnote:
            form = NoteForm(tutorial, request.user,
                            initial={"text": data["text"]})
            if request.is_ajax():
                return HttpResponse(json.dumps({"text": emarkdown(data["text"])}),
                                    content_type='application/json')
            else:
                return render(request, "tutorial/comment/new.html", {
                    "tutorial": tutorial,
                    "last_note_pk": last_note_pk,
                    "newnote": newnote,
                    "notes": notes,
                    "form": form,
                })
        else:

            # Saving the message

            form = NoteForm(tutorial, request.user, request.POST)
            if form.is_valid():
                data = form.data
                note = ContentReaction()
                note.related_content = tutorial
                note.author = request.user
                note.text = data["text"]
                note.text_html = emarkdown(data["text"])
                note.pubdate = datetime.now()
                note.position = tutorial.get_note_count() + 1
                note.ip_address = get_client_ip(request)
                note.save()
                tutorial.last_note = note
                tutorial.save()
                return redirect(note.get_absolute_url())
            else:
                return render(request, "tutorial/comment/new.html", {
                    "tutorial": tutorial,
                    "last_note_pk": last_note_pk,
                    "newnote": newnote,
                    "notes": notes,
                    "form": form,
                })
    else:

        # Actions from the editor render to answer.html.
        text = ""

        # Using the quote button

        if "cite" in request.GET:
            note_cite_pk = request.GET["cite"]
            note_cite = ContentReaction.objects.get(pk=note_cite_pk)
            if not note_cite.is_visible:
                raise PermissionDenied

            for line in note_cite.text.splitlines():
                text = text + "> " + line + "\n"

            text = u'{0}Source:[{1}]({2}{3})'.format(
                text,
                note_cite.author.username,
                settings.ZDS_APP['site']['url'],
                note_cite.get_absolute_url())

        form = NoteForm(tutorial, request.user, initial={"text": text})
        return render(request, "tutorial/comment/new.html", {
            "tutorial": tutorial,
            "notes": notes,
            "last_note_pk": last_note_pk,
            "form": form,
        })


@can_write_and_read_now
@login_required
@require_POST
@transaction.atomic
def solve_alert(request):
    # only staff can move topic

    if not request.user.has_perm("tutorial.change_note"):
        raise PermissionDenied

    alert = get_object_or_404(Alert, pk=request.POST["alert_pk"])
    note = ContentReaction.objects.get(pk=alert.comment.id)

    if "text" in request.POST and request.POST["text"] != "":
        bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
        msg = \
            (_(u'Bonjour {0},'
               u'Vous recevez ce message car vous avez signalé le message de *{1}*, '
               u'dans le tutoriel [{2}]({3}). Votre alerte a été traitée par **{4}** '
               u'et il vous a laissé le message suivant :'
               u'\n\n> {5}\n\nToute l\'équipe de la modération vous remercie !').format(
                alert.author.username,
                note.author.username,
                note.tutorial.title,
                settings.ZDS_APP['site']['url'] + note.get_absolute_url(),
                request.user.username,
                request.POST["text"], ))
        send_mp(
            bot,
            [alert.author],
            _(u"Résolution d'alerte : {0}").format(note.tutorial.title),
            "",
            msg,
            False,
        )
    alert.delete()
    messages.success(request, _(u"L'alerte a bien été résolue."))
    return redirect(note.get_absolute_url())


@can_write_and_read_now
@login_required
def edit_note(request):
    """Edit the given user's note."""

    try:
        note_pk = request.GET["message"]
    except KeyError:
        raise Http404
    note = get_object_or_404(ContentReaction, pk=note_pk)
    g_tutorial = None
    if note.position >= 1:
        g_tutorial = get_object_or_404(PublishableContent, pk=note.related_content.pk)

    # Making sure the user is allowed to do that. Author of the note must to be
    # the user logged.

    if note.author != request.user \
            and not request.user.has_perm("tutorial.change_note") \
            and "signal_message" not in request.POST:
        raise PermissionDenied
    if note.author != request.user and request.method == "GET" \
            and request.user.has_perm("tutorial.change_note"):
        messages.add_message(request, messages.WARNING,
                             _(u'Vous éditez ce message en tant que '
                               u'modérateur (auteur : {}). Soyez encore plus '
                               u'prudent lors de l\'édition de '
                               u'celui-ci !').format(note.author.username))
        note.alerts.all().delete()
    if request.method == "POST":
        if "delete_message" in request.POST:
            if note.author == request.user \
                    or request.user.has_perm("tutorial.change_note"):
                note.alerts.all().delete()
                note.is_visible = False
                if request.user.has_perm("tutorial.change_note"):
                    note.text_hidden = request.POST["text_hidden"]
                note.editor = request.user
        if "show_message" in request.POST:
            if request.user.has_perm("tutorial.change_note"):
                note.is_visible = True
                note.text_hidden = ""
        if "signal_message" in request.POST:
            alert = Alert()
            alert.author = request.user
            alert.comment = note
            alert.scope = Alert.TUTORIAL
            alert.text = request.POST["signal_text"]
            alert.pubdate = datetime.now()
            alert.save()

        # Using the preview button
        if "preview" in request.POST:
            form = NoteForm(g_tutorial, request.user,
                            initial={"text": request.POST["text"]})
            form.helper.form_action = reverse("zds.tutorial.views.edit_note") + "?message=" + str(note_pk)
            if request.is_ajax():
                return HttpResponse(json.dumps({"text": emarkdown(request.POST["text"])}),
                                    content_type='application/json')
            else:
                return render(request,
                              "tutorial/comment/edit.html",
                              {"note": note, "tutorial": g_tutorial, "form": form})
        if "delete_message" not in request.POST and "signal_message" \
                not in request.POST and "show_message" not in request.POST:

            # The user just sent data, handle them

            if request.POST["text"].strip() != "":
                note.text = request.POST["text"]
                note.text_html = emarkdown(request.POST["text"])
                note.update = datetime.now()
                note.editor = request.user
        note.save()
        return redirect(note.get_absolute_url())
    else:
        form = NoteForm(g_tutorial, request.user, initial={"text": note.text})
        form.helper.form_action = reverse("zds.tutorial.views.edit_note") + "?message=" + str(note_pk)
        return render(request, "tutorial/comment/edit.html", {"note": note, "tutorial": g_tutorial, "form": form})


@can_write_and_read_now
@login_required
def like_note(request):
    """Like a note."""
    try:
        note_pk = request.GET["message"]
    except KeyError:
        raise Http404
    resp = {}
    note = get_object_or_404(ContentReaction, pk=note_pk)

    user = request.user
    if note.author.pk != request.user.pk:

        # Making sure the user is allowed to do that

        if CommentLike.objects.filter(user__pk=user.pk,
                                      comments__pk=note_pk).count() == 0:
            like = CommentLike()
            like.user = user
            like.comments = note
            note.like = note.like + 1
            note.save()
            like.save()
            if CommentDislike.objects.filter(user__pk=user.pk,
                                             comments__pk=note_pk).count() > 0:
                CommentDislike.objects.filter(
                    user__pk=user.pk,
                    comments__pk=note_pk).all().delete()
                note.dislike = note.dislike - 1
                note.save()
        else:
            CommentLike.objects.filter(user__pk=user.pk,
                                       comments__pk=note_pk).all().delete()
            note.like = note.like - 1
            note.save()
    resp["upvotes"] = note.like
    resp["downvotes"] = note.dislike
    if request.is_ajax():
        return HttpResponse(json_writer.dumps(resp))
    else:
        return redirect(note.get_absolute_url())


@can_write_and_read_now
@login_required
def dislike_note(request):
    """Dislike a note."""

    try:
        note_pk = request.GET["message"]
    except KeyError:
        raise Http404
    resp = {}
    note = get_object_or_404(ContentReaction, pk=note_pk)
    user = request.user
    if note.author.pk != request.user.pk:

        # Making sure the user is allowed to do that

        if CommentDislike.objects.filter(user__pk=user.pk,
                                         comments__pk=note_pk).count() == 0:
            dislike = CommentDislike()
            dislike.user = user
            dislike.comments = note
            note.dislike = note.dislike + 1
            note.save()
            dislike.save()
            if CommentLike.objects.filter(user__pk=user.pk,
                                          comments__pk=note_pk).count() > 0:
                CommentLike.objects.filter(user__pk=user.pk,
                                           comments__pk=note_pk).all().delete()
                note.like = note.like - 1
                note.save()
        else:
            CommentDislike.objects.filter(user__pk=user.pk,
                                          comments__pk=note_pk).all().delete()
            note.dislike = note.dislike - 1
            note.save()
    resp["upvotes"] = note.like
    resp["downvotes"] = note.dislike
    if request.is_ajax():
        return HttpResponse(json_writer.dumps(resp))
    else:
        return redirect(note.get_absolute_url())
