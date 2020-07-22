import json
import logging
import os
import re
import shutil
import tempfile
import time
import zipfile
from collections import OrderedDict
from datetime import datetime

from PIL import Image as ImagePIL
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count, Q
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.text import format_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView, DeleteView, RedirectView
from easy_thumbnails.files import get_thumbnailer
from git import BadName, BadObject, GitCommandError, objects
from uuslug import slugify

from zds import json_handler
from zds.forum.models import Forum, mark_read, Topic
from zds.gallery.models import Gallery, UserGallery, Image, GALLERY_WRITE
from zds.member.decorator import LoggedWithReadWriteHability, LoginRequiredMixin, PermissionRequiredMixin
from zds.member.models import Profile
from zds.notification.models import TopicAnswerSubscription, NewPublicationSubscription
from zds.tutorialv2.forms import ContentForm, JsFiddleActivationForm, AskValidationForm, AcceptValidationForm, \
    RejectValidationForm, RevokeValidationForm, WarnTypoForm, ImportContentForm, ImportNewContentForm, ContainerForm, \
    ExtractForm, BetaForm, MoveElementForm, AuthorForm, RemoveAuthorForm, CancelValidationForm, PublicationForm, \
    UnpublicationForm, ContributionForm, RemoveContributionForm, SearchSuggestionForm, RemoveSuggestionForm, \
    EditContentLicenseForm, EditContentTagsForm, ToggleHelpForm
from zds.tutorialv2.mixins import SingleContentDetailViewMixin, SingleContentFormViewMixin, SingleContentViewMixin, \
    SingleContentDownloadViewMixin, SingleContentPostMixin, FormWithPreview
from zds.tutorialv2.models import TYPE_CHOICES_DICT
from zds.tutorialv2.models.database import PublishableContent, Validation, ContentContribution, ContentSuggestion
from zds.tutorialv2.models.versioned import Container, Extract
from zds.tutorialv2.utils import search_container_or_404, get_target_tagged_tree, search_extract_or_404, \
    try_adopt_new_child, TooDeepContainerError, BadManifestError, get_content_from_json, init_new_repo, \
    default_slug_pool, BadArchiveError, InvalidSlugError
from zds.utils.forums import send_post, lock_topic, create_topic, unlock_topic
from zds.utils.models import HelpWriting, get_hat_from_settings
from zds.utils.mps import send_mp, send_message_mp
from zds.utils.paginator import ZdSPagingListView, make_pagination

logger = logging.getLogger(__name__)


class RedirectOldBetaTuto(RedirectView):
    """
    allows to redirect /tutoriels/beta/old_pk/slug to /contenus/beta/new_pk/slug
    """
    permanent = True

    def get_redirect_url(self, **kwargs):
        tutorial = PublishableContent.objects.filter(type='TUTORIAL', old_pk=kwargs['pk']).first()
        if tutorial is None or tutorial.sha_beta is None or tutorial.sha_beta == '':
            raise Http404('Aucun contenu en bêta trouvé avec cet ancien identifiant.')
        return tutorial.get_absolute_url_beta()


class CreateContent(LoggedWithReadWriteHability, FormWithPreview):
    """
    Handle content creation. Since v22 a licence must be explicitly selected
    instead of defaulting to "All rights reserved". Users can however
    set a default licence in their profile.
    """
    template_name = 'tutorialv2/create/content.html'
    model = PublishableContent
    form_class = ContentForm
    content = None
    created_content_type = 'TUTORIAL'

    def get_form(self, form_class=ContentForm):
        form = super(CreateContent, self).get_form(form_class)
        form.initial['type'] = self.created_content_type
        return form

    def get_context_data(self, **kwargs):
        context = super(CreateContent, self).get_context_data(**kwargs)
        context['editorial_line_link'] = settings.ZDS_APP['content']['editorial_line_link']
        context['site_name'] = settings.ZDS_APP['site']['literal_name']
        return context

    def form_valid(self, form):

        # create the object:
        self.content = PublishableContent()
        self.content.title = form.cleaned_data['title']
        self.content.description = form.cleaned_data['description']
        self.content.type = form.cleaned_data['type']
        self.content.licence = self.request.user.profile.licence  # Use the preferred license of the user if it exists
        self.content.source = form.cleaned_data['source']
        self.content.creation_date = datetime.now()

        # Creating the gallery
        gal = Gallery()
        gal.title = form.cleaned_data['title']
        gal.slug = slugify(form.cleaned_data['title'])
        gal.pubdate = datetime.now()
        gal.save()

        self.content.gallery = gal
        self.content.save()
        # create image:
        if 'image' in self.request.FILES:
            img = Image()
            img.physical = self.request.FILES['image']
            img.gallery = gal
            img.title = self.request.FILES['image']
            img.slug = slugify(self.request.FILES['image'].name)
            img.pubdate = datetime.now()
            img.save()
            self.content.image = img

        self.content.save()

        # We need to save the content before changing its author list since it's a many-to-many relationship
        self.content.authors.add(self.request.user)

        self.content.ensure_author_gallery()
        self.content.save(force_slug_update=False)
        # Add subcategories on tutorial
        for subcat in form.cleaned_data['subcategory']:
            self.content.subcategory.add(subcat)

        self.content.save(force_slug_update=False)

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
            .order_by('-date_proposition') \
            .first()

        form_js = JsFiddleActivationForm(initial={'js_support': self.object.js_support})

        context['formAskValidation'] = AskValidationForm(
            content=self.versioned_object, initial={'source': self.object.source, 'version': self.sha})

        if validation:
            context['formValid'] = AcceptValidationForm(validation, initial={'source': self.object.source})
            context['formReject'] = RejectValidationForm(validation)
            context['formCancel'] = CancelValidationForm(validation)

        if self.versioned_object.sha_public:
            context['formRevokeValidation'] = RevokeValidationForm(
                self.versioned_object, initial={'version': self.versioned_object.sha_public})
            context['formUnpublication'] = UnpublicationForm(
                self.versioned_object, initial={'version': self.versioned_object.sha_public})

        if self.versioned_object.is_beta:
            context['formWarnTypo'] = WarnTypoForm(self.versioned_object, self.versioned_object, public=False)

        context['validation'] = validation
        context['formJs'] = form_js

        context['form_edit_license'] = EditContentLicenseForm(
            self.versioned_object,
            initial={'license': self.versioned_object.licence})

        initial_tags_field = ', '.join(self.object.tags.values_list('title', flat=True))
        context['form_edit_tags'] = EditContentTagsForm(self.versioned_object, initial={'tags': initial_tags_field})

        if self.versioned_object.requires_validation:
            context['formPublication'] = PublicationForm(self.versioned_object, initial={'source': self.object.source})
        else:
            context['formPublication'] = None

    def get_context_data(self, **kwargs):
        context = super(DisplayContent, self).get_context_data(**kwargs)

        # check whether this tuto support js fiddle
        if self.object.js_support:
            is_js = 'js'
        else:
            is_js = ''
        context['is_js'] = is_js

        self.get_forms(context)

        context['gallery'] = self.object.gallery
        context['public_content_object'] = self.public_content_object
        if self.object.type.lower() != 'opinion':
            context['formAddReviewer'] = ContributionForm(content=self.object)
            context['contributions'] = ContentContribution\
                .objects\
                .filter(content=self.object)\
                .order_by('contribution_role__position')
            context['content_suggestions'] = ContentSuggestion \
                .objects \
                .filter(publication=self.object)
            excluded_for_search = [str(x.suggestion.pk) for x in context['content_suggestions']]
            excluded_for_search.append(str(self.object.pk))
            context['formAddSuggestion'] = SearchSuggestionForm(content=self.object,
                                                                initial={'excluded_pk': ','.join(excluded_for_search)})

        return context


class DisplayBetaContent(DisplayContent):
    """View to get the beta version of a content"""

    sha = None

    def get_object(self, queryset=None):
        """rewritten to ensure that the version is set to beta, raise Http404 if there is no such version"""
        obj = super(DisplayBetaContent, self).get_object(queryset)

        if not obj.sha_beta:
            raise Http404("Aucune bêta n'existe pour ce contenu.")
        else:
            self.sha = obj.sha_beta

        # make the slug always right in URLs resolution:
        if 'slug' in self.kwargs:
            self.kwargs['slug'] = obj.slug

        return obj

    def get_context_data(self, **kwargs):
        context = super(DisplayBetaContent, self).get_context_data(**kwargs)
        context['pm_link'] = self.object.get_absolute_contact_url()
        return context


class EditContent(LoggedWithReadWriteHability, SingleContentFormViewMixin, FormWithPreview):
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
        initial['source'] = versioned.source
        initial['subcategory'] = self.object.subcategory.all()
        initial['last_hash'] = versioned.compute_hash()

        return initial

    def get_context_data(self, **kwargs):
        context = super(EditContent, self).get_context_data(**kwargs)
        if 'preview' not in self.request.POST:
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
            messages.error(self.request, _('Une nouvelle version a été postée avant que vous ne validiez.'))
            return self.form_invalid(form)

        # Forbid removing all categories of a validated content
        if publishable.in_public() and not form.cleaned_data['subcategory']:
            messages.error(self.request,
                           _('Vous devez choisir au moins une catégorie, car ce contenu est déjà publié.'))
            return self.form_invalid(form)

        # first, update DB (in order to get a new slug if needed)
        title_is_changed = publishable.title != form.cleaned_data['title']
        publishable.title = form.cleaned_data['title']
        publishable.description = form.cleaned_data['description']
        publishable.source = form.cleaned_data['source']

        publishable.update_date = datetime.now()

        # update gallery and image:
        gal = Gallery.objects.filter(pk=publishable.gallery.pk)
        gal.update(title=publishable.title)
        gal.update(slug=slugify(publishable.title))
        gal.update(update=datetime.now())

        if 'image' in self.request.FILES:
            img = Image()
            img.physical = self.request.FILES['image']
            img.gallery = publishable.gallery
            img.title = self.request.FILES['image']
            img.slug = slugify(self.request.FILES['image'].name)
            img.pubdate = datetime.now()
            img.save()
            publishable.image = img

        publishable.save(force_slug_update=title_is_changed)
        logger.debug('content %s updated, slug is %s', publishable.pk, publishable.slug)
        # now, update the versioned information
        versioned.description = form.cleaned_data['description']

        sha = versioned.repo_update_top_container(form.cleaned_data['title'],
                                                  publishable.slug,
                                                  form.cleaned_data['introduction'],
                                                  form.cleaned_data['conclusion'],
                                                  form.cleaned_data['msg_commit'])
        logger.debug('slug consistency after repo update repo=%s db=%s', versioned.slug, publishable.slug)
        # update relationships :
        publishable.sha_draft = sha

        publishable.subcategory.clear()
        for subcat in form.cleaned_data['subcategory']:
            publishable.subcategory.add(subcat)

        publishable.save(force_slug_update=False)

        self.success_url = reverse('content:view', args=[publishable.pk, publishable.slug])
        return super().form_valid(form)


class EditContentLicense(LoginRequiredMixin, SingleContentFormViewMixin):
    modal_form = True
    model = PublishableContent
    form_class = EditContentLicenseForm
    success_message_license = _('La licence de la publication a bien été changée.')
    success_message_profile_update = _('Votre licence préférée a bien été mise à jour.')

    def get_form_kwargs(self):
        kwargs = super(EditContentLicense, self).get_form_kwargs()
        kwargs['content'] = self.versioned_object
        return kwargs

    def form_valid(self, form):
        publishable = self.object

        # Update license in database
        publishable.licence = form.cleaned_data['license']
        publishable.update_date = datetime.now()
        publishable.save(force_slug_update=False)

        # Update license in repository
        self.versioned_object.licence = form.cleaned_data['license']
        sha = self.versioned_object.repo_update_top_container(
            publishable.title,
            publishable.slug,
            self.versioned_object.get_introduction(),
            self.versioned_object.get_conclusion(),
            'Nouvelle licence ({})'.format(form.cleaned_data['license'])
        )

        # Update relationships in database
        publishable.sha_draft = sha
        publishable.save(force_slug_update=False)

        messages.success(self.request, EditContentLicense.success_message_license)

        # Update the preferred license of the user
        if form.cleaned_data['update_preferred_license']:
            profile = get_object_or_404(Profile, user=self.request.user)
            profile.licence = form.cleaned_data['license']
            profile.save()
            messages.success(self.request, EditContentLicense.success_message_profile_update)

        return redirect(form.previous_page_url)


class EditContentTags(LoggedWithReadWriteHability, SingleContentFormViewMixin):
    modal_form = True
    model = PublishableContent
    form_class = EditContentTagsForm
    success_message = _('Les tags ont bien été modifiés.')

    def get_form_kwargs(self):
        kwargs = super(EditContentTags, self).get_form_kwargs()
        kwargs['content'] = self.versioned_object
        return kwargs

    def get_initial(self):
        initial = super(EditContentTags, self).get_initial()
        initial['tags'] = ', '.join(self.object.tags.values_list('title', flat=True))
        return initial

    def form_valid(self, form):
        self.object.tags.clear()
        self.object.add_tags(form.cleaned_data['tags'].split(','))
        self.object.save(force_slug_update=False)
        messages.success(self.request, EditContentTags.success_message)
        return redirect(form.previous_page_url)


class DeleteContent(LoginRequiredMixin, SingleContentViewMixin, DeleteView):
    model = PublishableContent
    template_name = None
    http_method_names = ['delete', 'post']
    object = None
    authorized_for_staff = False  # deletion is creator's privilege

    @method_decorator(transaction.atomic)
    def dispatch(self, *args, **kwargs):
        return super(DeleteContent, self).dispatch(*args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """rewrite delete() function to ensure repository deletion"""

        self.object = self.get_object()
        object_type = self.object.type.lower()

        _type = _('ce tutoriel')
        if self.object.is_article:
            _type = _('cet article')
        elif self.object.is_opinion:
            _type = _('ce billet')

        if self.object.authors.count() > 1:  # if more than one author, just remove author from list
            RemoveAuthorFromContent.remove_author(self.object, self.request.user)
            messages.success(self.request, _('Vous avez quitté la rédaction de {}.').format(_type))

        else:
            validation = Validation.objects.filter(content=self.object).order_by('-date_proposition').first()

            if validation and validation.status == 'PENDING_V':  # if the validation have a validator, warn him by PM
                if 'text' not in self.request.POST or len(self.request.POST['text'].strip()) < 3:
                    messages.error(self.request, _('Merci de fournir une raison à la suppression.'))
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
                    if not validation.content.validation_private_message:
                        validation.content.validation_private_message = send_mp(
                            bot,
                            [validation.validator],
                            _('Demande de validation annulée').format(),
                            self.object.title,
                            msg,
                            send_by_mail=False,
                            leave=True,
                            hat=get_hat_from_settings('validation'),
                            automatically_read=validation.validator
                        )
                        validation.content.save(force_slug_update=False)
                    else:
                        send_message_mp(
                            bot,
                            validation.content.validation_private_message,
                            msg,
                            hat=get_hat_from_settings('validation'),
                            no_notification_for=[self.request.user]
                        )
            if self.object.beta_topic is not None:
                beta_topic = self.object.beta_topic
                beta_topic.is_locked = True
                beta_topic.add_tags(['Supprimé'])
                beta_topic.save()
                post = beta_topic.first_post()
                post.update_content(
                    _('[[a]]\n'
                      '| Malheureusement, {} qui était en bêta a été supprimé par son auteur.\n\n').format(_type) +
                    post.text)

                post.save()

            self.object.delete()

            messages.success(self.request, _('Vous avez bien supprimé {}.').format(_type))

        return redirect(reverse(object_type + ':find-' + object_type, args=[request.user.username]))


class DownloadContent(LoginRequiredMixin, SingleContentDownloadViewMixin):
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
        if git_tree.trees:  # then, recursively add dirs :
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
        response = open(zip_path, 'rb').read()
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
            manifest = str(zip_archive.read('manifest.json'), 'utf-8')
        except KeyError:
            raise BadArchiveError(_('Cette archive ne contient pas de fichier manifest.json.'))
        except UnicodeDecodeError:
            raise BadArchiveError(_("L'encodage du manifest.json n'est pas de l'UTF-8."))

        # is the manifest ok ?
        try:
            json_ = json_handler.loads(manifest)
        except ValueError:
            raise BadArchiveError(
                _('Une erreur est survenue durant la lecture du manifest, '
                  "vérifiez qu'il s'agit de JSON correctement formaté."))
        try:
            versioned = get_content_from_json(json_, None, '',
                                              max_title_len=PublishableContent._meta.get_field('title').max_length)
        except BadManifestError as e:
            raise BadArchiveError(e.message)
        except InvalidSlugError as e:
            e1 = _('Le slug "{}" est invalide').format(e)
            e2 = ''
            if e.had_source:
                e2 = _(' (slug généré à partir de "{}")').format(e.source)
            raise BadArchiveError(_('{}{} !').format(e1, e2))
        except Exception as e:
            raise BadArchiveError(_("Une erreur est survenue lors de la lecture de l'archive : {}.").format(e))

        # is there everything in the archive ?
        for f in UpdateContentWithArchive.walk_content(versioned):
            try:
                zip_archive.getinfo(f)
            except KeyError:
                raise BadArchiveError(_("Le fichier '{}' n'existe pas dans l'archive.").format(f))

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
                        introduction = str(zip_file.read(child.introduction), 'utf-8')
                    except UnicodeDecodeError:
                        raise BadArchiveError(
                            _("Le fichier « {} » n'est pas encodé en UTF-8".format(child.introduction)))
                if child.conclusion:
                    try:
                        conclusion = str(zip_file.read(child.conclusion), 'utf-8')
                    except UnicodeDecodeError:
                        raise BadArchiveError(
                            _("Le fichier « {} » n'est pas encodé en UTF-8".format(child.conclusion)))

                copy_to.repo_add_container(child.title, introduction, conclusion, do_commit=False, slug=child.slug)
                UpdateContentWithArchive.update_from_new_version_in_zip(copy_to.children[-1], child, zip_file)

            elif isinstance(child, Extract):
                try:
                    text = str(zip_file.read(child.text), 'utf-8')
                except UnicodeDecodeError:
                    raise BadArchiveError(
                        _("Le fichier « {} » n'est pas encodé en UTF-8".format(child.text)))

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

            if not image_basename.strip():  # don't deal with directory
                continue

            temp_image_path = os.path.abspath(os.path.join(temp, image_basename))

            # create a temporary file for the image
            f_im = open(temp_image_path, 'wb')
            f_im.write(zip_file.read(image_path))
            f_im.close()

            # if it's not an image, pass
            try:
                ImagePIL.open(temp_image_path)
            except OSError:
                continue

            # if size is too large, pass
            if os.stat(temp_image_path).st_size > settings.ZDS_APP['gallery']['image_max_size']:
                messages.error(
                    request, _('Votre image "{}" est beaucoup trop lourde, réduisez sa taille à moins de {:.0f}'
                               "Kio avant de l'envoyer.").format(
                                   image_path, settings.ZDS_APP['gallery']['image_max_size'] / 1024))
                continue

            # create picture in database:
            pic = Image()
            pic.gallery = gallery
            pic.title = image_basename
            pic.slug = slugify(image_basename)
            pic.physical = get_thumbnailer(open(temp_image_path, 'rb'), relative_name=temp_image_path)
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
        image_regex = re.compile(r'((?P<start>!\[.*?\]\()' + settings.ZDS_APP['content']['import_image_prefix'] +
                                 r':(?P<path>.*?)(?P<end>\)))')

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
                zfile = zipfile.ZipFile(self.request.FILES['archive'], 'r')
            except zipfile.BadZipfile:
                messages.error(self.request, _("Cette archive n'est pas au format ZIP."))
                return super(UpdateContentWithArchive, self).form_invalid(form)

            try:
                new_version = UpdateContentWithArchive.extract_content_from_zip(zfile)
            except BadArchiveError as e:
                messages.error(self.request, e.message)
                return super(UpdateContentWithArchive, self).form_invalid(form)
            else:

                # Warn the user if the license has been changed
                manifest = json_handler.loads(str(zfile.read('manifest.json'), 'utf-8'))
                if new_version.licence \
                   and 'licence' in manifest \
                   and manifest['licence'] != new_version.licence.code:
                    messages.info(
                        self.request, _('la licence « {} » a été appliquée.').format(new_version.licence.code))

                # first, update DB object (in order to get a new slug if needed)
                self.object.title = new_version.title
                self.object.description = new_version.description
                self.object.licence = new_version.licence
                self.object.type = new_version.type  # change of type is then allowed !!
                self.object.save()

                new_version.slug = self.object.slug  # new slug if any !!

                # ok, then, let's do the import. First, remove everything in the repository
                while True:
                    if versioned.children:
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
                    introduction = str(zfile.read(new_version.introduction), 'utf-8')
                if new_version.conclusion:
                    conclusion = str(zfile.read(new_version.conclusion), 'utf-8')

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

                if not commit_message:
                    commit_message = _("Importation d'une archive contenant « {} ».").format(new_version.title)

                sha = versioned.commit_changes(commit_message)

                # now, use the images from the archive if provided. To work, this HAVE TO happen after commiting files !
                if 'image_archive' in self.request.FILES:
                    try:
                        zfile = zipfile.ZipFile(self.request.FILES['image_archive'], 'r')
                    except zipfile.BadZipfile:
                        messages.error(self.request, _("L'archive contenant les images n'est pas au format ZIP."))
                        return self.form_invalid(form)

                    UpdateContentWithArchive.use_images_from_archive(
                        self.request,
                        zfile,
                        versioned,
                        self.object.gallery)

                    commit_message = _("Utilisation des images de l'archive pour « {} »").format(new_version.title)
                    sha = versioned.commit_changes(commit_message)  # another commit

                # of course, need to update sha
                self.object.sha_draft = sha
                self.object.update_date = datetime.now()
                self.object.save(force_slug_update=False)

                self.success_url = reverse('content:view', args=[versioned.pk, versioned.slug])

        return super(UpdateContentWithArchive, self).form_valid(form)


class CreateContentFromArchive(LoggedWithReadWriteHability, FormView):
    """Create a content using an archive"""

    form_class = ImportNewContentForm
    template_name = 'tutorialv2/import/content-new.html'
    object = None

    def form_valid(self, form):

        if self.request.FILES['archive']:
            try:
                zfile = zipfile.ZipFile(self.request.FILES['archive'], 'r')
            except zipfile.BadZipfile:
                messages.error(self.request, _("Cette archive n'est pas au format ZIP."))
                return self.form_invalid(form)

            try:
                new_content = UpdateContentWithArchive.extract_content_from_zip(zfile)
            except BadArchiveError as e:
                messages.error(self.request, e.message)
                return super(CreateContentFromArchive, self).form_invalid(form)
            except KeyError as e:
                messages.error(self.request, _(e.message + " n'est pas correctement renseigné."))
                return super(CreateContentFromArchive, self).form_invalid(form)
            else:

                # Warn the user if the license has been changed
                manifest = json_handler.loads(str(zfile.read('manifest.json'), 'utf-8'))
                if new_content.licence \
                   and 'licence' in manifest \
                   and manifest['licence'] != new_content.licence.code:
                    messages.info(self.request,
                                  _('la licence « {} » a été appliquée.'.format(new_content.licence.code)))

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
                self.object.gallery = gal
                self.object.save(force_slug_update=False)

                # Add subcategories on tutorial
                for subcat in form.cleaned_data['subcategory']:
                    self.object.subcategory.add(subcat)

                # We need to save the tutorial before changing its author list since it's a many-to-many relationship
                self.object.authors.add(self.request.user)
                self.object.save(force_slug_update=False)
                self.object.ensure_author_gallery()
                # ok, now we can import
                introduction = ''
                conclusion = ''

                if new_content.introduction:
                    introduction = str(zfile.read(new_content.introduction), 'utf-8')
                if new_content.conclusion:
                    conclusion = str(zfile.read(new_content.conclusion), 'utf-8')

                commit_message = _('Création de « {} »').format(new_content.title)
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

                if not commit_message:
                    commit_message = _("Importation d'une archive contenant « {} »").format(new_content.title)
                versioned.slug = self.object.slug  # force slug to ensure path resolution
                sha = versioned.repo_update(versioned.title, versioned.get_introduction(),
                                            versioned.get_conclusion(), commit_message, update_slug=True)

                # This HAVE TO happen after commiting files (if not, content are None)
                if 'image_archive' in self.request.FILES:
                    try:
                        zfile = zipfile.ZipFile(self.request.FILES['image_archive'], 'r')
                    except zipfile.BadZipfile:
                        messages.error(self.request, _("L'archive contenant les images n'est pas au format ZIP."))
                        return self.form_invalid(form)

                    UpdateContentWithArchive.use_images_from_archive(
                        self.request,
                        zfile,
                        versioned,
                        self.object.gallery)

                    commit_message = _("Utilisation des images de l'archive pour « {} »").format(new_content.title)
                    sha = versioned.commit_changes(commit_message)  # another commit

                # of course, need to update sha
                self.object.sha_draft = sha
                self.object.update_date = datetime.now()
                self.object.save(force_slug_update=False)

                self.success_url = reverse('content:view', args=[versioned.pk, versioned.slug])

        return super(CreateContentFromArchive, self).form_valid(form)


class CreateContainer(LoggedWithReadWriteHability, SingleContentFormViewMixin, FormWithPreview):
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
            messages.error(self.request, _('Vous ne pouvez plus ajouter de conteneur à « {} ».').format(parent.title))
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
        self.object.save(force_slug_update=False)

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
                if position == 0:
                    context['previous'] = container.parent
                if position > 0:
                    previous_chapter = chapters[position - 1]
                    if previous_chapter.parent == container.parent:
                        context['previous'] = previous_chapter
                    else:
                        context['previous'] = container.parent
                if position < len(chapters) - 1:
                    next_chapter = chapters[position + 1]
                    if next_chapter.parent == container.parent:
                        context['next'] = next_chapter
                    else:
                        context['next'] = next_chapter.parent

        # check whether this tuto support js fiddle
        if self.object.js_support:
            is_js = 'js'
        else:
            is_js = ''
        context['is_js'] = is_js

        return context


class DisplayBetaContainer(DisplayContainer):
    """View to get the beta version of a container"""

    sha = None

    def get_object(self, queryset=None):
        """rewritten to ensure that the version is set to beta, raise Http404 if there is no such version"""
        obj = super(DisplayBetaContainer, self).get_object(queryset)

        if not obj.sha_beta:
            raise Http404("Aucune bêta n'existe pour ce contenu.")
        else:
            self.sha = obj.sha_beta

        # make the slug always right in URLs resolution:
        if 'slug' in self.kwargs:
            self.kwargs['slug'] = obj.slug

        return obj

    def get_context_data(self, **kwargs):
        context = super(DisplayBetaContainer, self).get_context_data(**kwargs)
        context['pm_link'] = self.object.get_absolute_contact_url()
        return context


class EditContainer(LoggedWithReadWriteHability, SingleContentFormViewMixin, FormWithPreview):
    template_name = 'tutorialv2/edit/container.html'
    form_class = ContainerForm
    content = None

    def get_context_data(self, **kwargs):
        context = super(EditContainer, self).get_context_data(**kwargs)

        if 'preview' not in self.request.POST:
            container = search_container_or_404(self.versioned_object, self.kwargs)
            context['container'] = container
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

    def form_valid(self, form, *args, **kwargs):
        container = search_container_or_404(self.versioned_object, self.kwargs)

        # check if content has changed:
        current_hash = container.compute_hash()
        if current_hash != form.cleaned_data['last_hash']:
            data = form.data.copy()
            data['last_hash'] = current_hash
            data['introduction'] = container.get_introduction()
            data['conclusion'] = container.get_conclusion()
            form.data = data
            messages.error(self.request, _('Une nouvelle version a été postée avant que vous ne validiez.'))
            return self.form_invalid(form)

        sha = container.repo_update(form.cleaned_data['title'],
                                    form.cleaned_data['introduction'],
                                    form.cleaned_data['conclusion'],
                                    form.cleaned_data['msg_commit'],
                                    update_slug=self.object.public_version is None)

        # then save
        self.object.sha_draft = sha
        self.object.update_date = datetime.now()
        self.object.save(force_slug_update=False)

        self.success_url = container.get_absolute_url()

        return super(EditContainer, self).form_valid(form)


class CreateExtract(LoggedWithReadWriteHability, SingleContentFormViewMixin, FormWithPreview):
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
            messages.error(self.request, _('Vous ne pouvez plus ajouter de section à « {} ».').format(parent.title))
            return redirect(parent.get_absolute_url())

        return super(CreateExtract, self).render_to_response(context, **response_kwargs)

    def form_valid(self, form):
        parent = search_container_or_404(self.versioned_object, self.kwargs)

        sha = parent.repo_add_extract(form.cleaned_data['title'],
                                      form.cleaned_data['text'],
                                      form.cleaned_data['msg_commit'])

        # then save
        self.object.sha_draft = sha
        self.object.update_date = datetime.now()
        self.object.save(force_slug_update=False)

        self.success_url = parent.children[-1].get_absolute_url()

        return super(CreateExtract, self).form_valid(form)


class EditExtract(LoggedWithReadWriteHability, SingleContentFormViewMixin, FormWithPreview):
    template_name = 'tutorialv2/edit/extract.html'
    form_class = ExtractForm
    content = None

    def get_context_data(self, **kwargs):
        context = super(EditExtract, self).get_context_data(**kwargs)
        context['gallery'] = self.object.gallery

        extract = search_extract_or_404(self.versioned_object, self.kwargs)
        context['extract'] = extract

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
            messages.error(self.request, _('Une nouvelle version a été postée avant que vous ne validiez.'))
            return self.form_invalid(form)

        sha = extract.repo_update(form.cleaned_data['title'],
                                  form.cleaned_data['text'],
                                  form.cleaned_data['msg_commit'])

        # then save
        self.object.update(sha_draft=sha, update_date=datetime.now())

        self.success_url = extract.get_absolute_url()
        if self.request.is_ajax():
            return JsonResponse({'result': 'ok', 'last_hash': extract.compute_hash(),
                                 'new_url': extract.get_edit_url()})
        return super(EditExtract, self).form_valid(form)


class DeleteContainerOrExtract(LoggedWithReadWriteHability, SingleContentViewMixin, DeleteView):
    model = PublishableContent
    template_name = None
    http_method_names = ['delete', 'post']
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
                raise Http404('Impossible de récupérer le contenu pour le supprimer.')

        sha = to_delete.repo_delete()

        # then save
        self.object.update(sha_draft=sha, update_date=datetime.now())

        return redirect(parent.get_absolute_url())


class DisplayHistory(LoggedWithReadWriteHability, SingleContentDetailViewMixin):
    """
    Display the whole modification history.
    This class has no reason to be adapted to any content type.
    """

    model = PublishableContent
    template_name = 'tutorialv2/view/history.html'

    def get_context_data(self, **kwargs):
        context = super(DisplayHistory, self).get_context_data(**kwargs)

        repo = self.versioned_object.repository
        commits = list(objects.commit.Commit.iter_items(repo, 'HEAD'))

        # Pagination of commits
        make_pagination(
            context,
            self.request,
            commits,
            settings.ZDS_APP['content']['commits_per_page'],
            context_list_name='commits')

        # Git empty tree is 4b825dc642cb6eb9a060e54bf8d69288fbee4904, see
        # http://stackoverflow.com/questions/9765453/gits-semi-secret-empty-tree
        context['empty_sha'] = '4b825dc642cb6eb9a060e54bf8d69288fbee4904'

        return context


class DisplayDiff(LoggedWithReadWriteHability, SingleContentDetailViewMixin):
    """
    Display the difference between two versions of a content.
    The left version is given in a GET query parameter named from, the right one with to.
    This class has no reason to be adapted to any content type.
    """

    model = PublishableContent
    template_name = 'tutorialv2/view/diff.html'
    only_draft_version = False

    def get_context_data(self, **kwargs):
        context = super(DisplayDiff, self).get_context_data(**kwargs)

        if 'from' not in self.request.GET:
            raise Http404("Paramètre GET 'from' manquant.")
        if 'to' not in self.request.GET:
            raise Http404("Paramètre GET 'to' manquant.")

        # open git repo and find diff between two versions
        repo = self.versioned_object.repository
        try:
            # repo.commit raises BadObject or BadName if invalid SHA
            commit_from = repo.commit(self.request.GET['from'])
            commit_to = repo.commit(self.request.GET['to'])
            # commit_to.diff raises GitErrorCommand if 00..00 SHA for instance
            tdiff = commit_to.diff(commit_from, R=True)
        except (GitCommandError, BadName, BadObject, ValueError) as git_error:
            logger.warn(git_error)
            raise Http404('En traitant le contenu {} git a lancé une erreur de type {}:{}'.format(
                self.object.title,
                type(git_error),
                str(git_error)
            ))

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
    - if 'set', it will active (of update) the beta
    - if 'inactive', it will inactive the beta on the tutorial
    """

    model = PublishableContent
    form_class = BetaForm
    authorized_for_staff = True
    only_draft_version = False

    action = None

    def _get_all_tags(self):
        return list(self.object.tags.all())

    def _create_beta_topic(self, msg, beta_version, _type, tags):
        topic_title = beta_version.title
        _tags = '[beta][{}]'.format(_type)
        i = 0
        max_len = Topic._meta.get_field('title').max_length

        while i < len(tags) and len(topic_title) + len(_tags) + len(tags[i].title) + 2 < max_len:
            _tags += '[{}]'.format(tags[i])
            i += 1
        forum = get_object_or_404(Forum, pk=settings.ZDS_APP['forum']['beta_forum_id'])
        topic = create_topic(request=self.request,
                             author=self.request.user,
                             forum=forum,
                             title=topic_title,
                             subtitle='{}'.format(beta_version.description),
                             text=msg,
                             related_publishable_content=self.object)
        topic.save()
        # make all authors follow the topic:
        for author in self.object.authors.all():
            TopicAnswerSubscription.objects.get_or_create_active(author, topic)
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
        if _type == 'tutorial':
            _type = _('tutoriel')
        elif _type == 'opinion':
            raise PermissionDenied

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
                    if not self.object.validation_private_message:
                        self.object.validation_private_message = send_mp(
                            bot,
                            self.object.authors.all(),
                            self.object.validation_message_title,
                            beta_version.title,
                            msg_pm,
                            send_by_mail=False,
                            leave=True,
                            hat=get_hat_from_settings('validation'))
                        self.object.save(force_slug_update=False)
                    else:
                        send_message_mp(bot,
                                        self.object.validation_private_message,
                                        msg,
                                        hat=get_hat_from_settings('validation'))

                # When the anti-spam triggers (because the author of the
                # message posted themselves within the last 15 minutes),
                # it is likely that we want to avoid to generate a duplicated
                # post that couldn't be deleted. We hence avoid to add another
                # message to the topic.

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
                        topic = send_post(self.request, topic, self.request.user, msg_post)
                    elif not topic.antispam():
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
                    TopicAnswerSubscription.objects.get_or_create_active(author, topic)
                    mark_read(topic, author)

            # finally set the tags on the topic
            if topic:
                topic.tags.clear()
                for tag in all_tags:
                    topic.tags.add(tag)
                topic.save()

        self.object.save(force_slug_update=False)  # we should prefer .update but it needs a uge refactoring

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
        authors = list(Profile.objects.contactable_members()
                       .filter(user__in=self.object.authors.all()))
        authors = list([author.user for author in authors])

        # check if the warn is done on a public or beta version :
        is_public = False

        if form.content.is_public:
            is_public = True
        elif not form.content.is_beta:
            raise Http404("Le contenu n'est ni public, ni en bêta.")

        if not authors:
            if self.object.authors.count() > 1:
                messages.error(self.request, _('Les auteurs sont malheureusement injoignables.'))
            else:
                messages.error(self.request, _("L'auteur est malheureusement injoignable."))

        elif user in authors:  # author try to PM himself
            messages.error(self.request, _("Impossible d'envoyer la proposition de correction : vous êtes auteur."))

        else:  # send correction
            text = '\n'.join(['> ' + line for line in form.cleaned_data['text'].split('\n')])

            _type = _('l\'article')
            if form.content.is_tutorial:
                _type = _('le tutoriel')
            if form.content.is_opinion:
                _type = _('le billet')

            pm_title = _('J\'ai trouvé une faute dans {} « {} ».').format(_type, form.content.title)

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
            send_mp(user, authors, pm_title, '', msg, leave=False)

            messages.success(self.request, _('Merci pour votre proposition de correction.'))

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
            .order_by('-update_date') \
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

        context['helps'] = list(helps.all())
        context['total_contents_number'] = queryset.count()
        return context


class ActivateJSFiddleInContent(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    """Handles changes a validator or staff member can do on the js fiddle support of the provided content
    Only these users can do it"""

    permissions = ['tutorialv2.change_publishablecontent']
    form_class = JsFiddleActivationForm
    http_method_names = ['post']

    def form_valid(self, form):
        """Change the js fiddle support of content and redirect to the view page"""

        content = get_object_or_404(PublishableContent, pk=form.cleaned_data['pk'])
        # forbidden for content without a validation before publication
        if not content.load_version().requires_validation():
            raise PermissionDenied
        content.update(js_support=form.cleaned_data['js_support'])
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
        base_container_slug = form.data['container_slug']
        child_slug = form.data['child_slug']

        if not base_container_slug:
            raise Http404('Le slug du container de base est vide.')

        if not child_slug:
            raise Http404('Le slug du container enfant est vide.')

        if base_container_slug == versioned.slug:
            parent = versioned
        else:
            search_params = {}

            if 'first_level_slug' in form.data and form.data['first_level_slug']:
                search_params['parent_container_slug'] = form.data['first_level_slug']
                search_params['container_slug'] = base_container_slug
            else:
                search_params['container_slug'] = base_container_slug
            parent = search_container_or_404(versioned, search_params)

        try:
            child = parent.children_dict[child_slug]
            if form.data['moving_method'] == MoveElementForm.MOVE_UP:
                parent.move_child_up(child_slug)
                logger.debug('{} was moved up in tutorial id:{}'.format(child_slug, content.pk))
            elif form.data['moving_method'] == MoveElementForm.MOVE_DOWN:
                parent.move_child_down(child_slug)
                logger.debug('{} was moved down in tutorial id:{}'.format(child_slug, content.pk))
            elif form.data['moving_method'][0:len(MoveElementForm.MOVE_AFTER)] == MoveElementForm.MOVE_AFTER:
                target = form.data['moving_method'][len(MoveElementForm.MOVE_AFTER) + 1:]
                if not parent.has_child_with_path(target):
                    if '/' not in target:
                        target_parent = versioned
                    else:
                        target_parent = search_container_or_404(versioned, '/'.join(target.split('/')[:-1]))

                        if target.split('/')[-1] not in target_parent.children_dict:
                            raise Http404("La cible n'est pas un enfant du parent.")
                    child = target_parent.children_dict[target.split('/')[-1]]
                    try_adopt_new_child(target_parent, parent.children_dict[child_slug])
                    # now, I will fix a bug that happens when the slug changes
                    # this one cost me so much of my hair
                    # and makes me think copy/past are killing kitty cat.
                    child_slug = target_parent.children[-1].slug
                    parent = target_parent
                parent.move_child_after(child_slug, target.split('/')[-1])
                logger.debug('{} was moved after {} in tutorial id:{}'.format(child_slug, target, content.pk))
            elif form.data['moving_method'][0:len(MoveElementForm.MOVE_BEFORE)] == MoveElementForm.MOVE_BEFORE:
                target = form.data['moving_method'][len(MoveElementForm.MOVE_BEFORE) + 1:]
                if not parent.has_child_with_path(target):
                    if '/' not in target:
                        target_parent = versioned
                    else:
                        target_parent = search_container_or_404(versioned, '/'.join(target.split('/')[:-1]))

                        if target.split('/')[-1] not in target_parent.children_dict:
                            raise Http404("La cible n'est pas un enfant du parent.")
                    child = target_parent.children_dict[target.split('/')[-1]]
                    try_adopt_new_child(target_parent, parent.children_dict[child_slug])
                    # now, I will fix a bug that happens when the slug changes
                    # this one cost me so much of my hair
                    child_slug = target_parent.children[-1].slug
                    parent = target_parent
                parent.move_child_before(child_slug, target.split('/')[-1])
                logger.debug('{} was moved before {} in tutorial id:{}'.format(child_slug, target, content.pk))
            versioned.slug = content.slug  # we force not to change slug
            versioned.dump_json()
            parent.repo_update(parent.title,
                               parent.get_introduction(),
                               parent.get_conclusion(),
                               _('Déplacement de ') + child_slug, update_slug=False)
            content.sha_draft = versioned.sha_draft
            content.save(force_slug_update=False)  # we do not want the save routine to update the slug in case
            # of slug algorithm conflict (for pre-zep-12 or imported content)
            messages.info(self.request, _("L'élément a bien été déplacé."))
        except TooDeepContainerError:
            messages.error(self.request, _("Ce conteneur contient déjà trop d'enfants pour être"
                                           ' inclus dans un autre conteneur.'))
        except KeyError:
            messages.warning(self.request, _("Vous n'avez pas complètement rempli le formulaire,"
                                             'ou bien il est impossible de déplacer cet élément.'))
        except ValueError as e:
            raise Http404("L'arbre spécifié n'est pas valide." + str(e))
        except IndexError:
            messages.warning(self.request, _("L'élément se situe déjà à la place souhaitée."))
            logger.debug("L'élément {} se situe déjà à la place souhaitée".format(child_slug))
        except TypeError:
            messages.error(self.request, _("L'élément ne peut pas être déplacé à cet endroit."))
        if base_container_slug == versioned.slug:
            return redirect(reverse('content:view', args=[content.pk, content.slug]))
        else:
            return redirect(child.get_absolute_url())


class AddContributorToContent(LoggedWithReadWriteHability, SingleContentFormViewMixin):
    only_draft_version = True
    must_be_author = True
    form_class = ContributionForm
    authorized_for_staff = True

    def get_form_kwargs(self):
        kwargs = super(AddContributorToContent, self).get_form_kwargs()
        kwargs.update({'content': self.object})
        return kwargs

    def get(self, request, *args, **kwargs):
        content = self.get_object()
        url = 'content:find-{}'.format('tutorial' if content.is_tutorial() else content.type.lower())
        return redirect(url, self.request.user)

    def form_valid(self, form):

        _type = _("à l'article")

        if self.object.is_tutorial:
            _type = _('au tutoriel')
        elif self.object.is_opinion:
            raise PermissionDenied

        bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
        all_authors_pk = [author.pk for author in self.object.authors.all()]
        user = form.cleaned_data['user']
        if user.pk in all_authors_pk:
            messages.error(self.request,
                           _('Un auteur ne peut pas être désigné comme contributeur'))
            return redirect(self.object.get_absolute_url())
        else:
            contribution_role = form.cleaned_data.get('contribution_role')
            comment = form.cleaned_data.get('comment')
            if ContentContribution.objects.filter(user=user,
                                                  contribution_role=contribution_role,
                                                  content=self.object).exists():
                messages.error(self.request,
                               _('Ce membre fait déjà partie des '
                                 'contributeurs {} avec pour rôle "{}"'.format(_type, contribution_role.title)))
                return redirect(self.object.get_absolute_url())

            contribution = ContentContribution(user=user,
                                               contribution_role=contribution_role,
                                               comment=comment,
                                               content=self.object)
            contribution.save()
            url_index = reverse(self.object.type.lower() + ':find-' + self.object.type.lower(), args=[user.pk])
            send_mp(
                bot,
                [user],
                format_lazy('{} {}', _('Contribution'), _type),
                self.versioned_object.title,
                render_to_string('tutorialv2/messages/add_contribution_pm.md', {
                    'content': self.object,
                    'type': _type,
                    'url': self.object.get_absolute_url(),
                    'index': url_index,
                    'user': user.username,
                    'role': contribution.contribution_role.title
                }),
                send_by_mail=True,
                direct=False,
                leave=True,
            )
            self.success_url = self.object.get_absolute_url()

            return super(AddContributorToContent, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, form.errors)
        self.success_url = self.object.get_absolute_url()
        return super(AddContributorToContent, self).form_valid(form)


class RemoveContributorFromContent(LoggedWithReadWriteHability, SingleContentFormViewMixin):

    form_class = RemoveContributionForm
    only_draft_version = True
    must_be_author = True
    authorized_for_staff = True

    def form_valid(self, form):
        _type = _('cet article')
        if self.object.is_tutorial:
            _type = _('ce tutoriel')
        elif self.object.is_opinion:
            raise PermissionDenied

        contribution = get_object_or_404(ContentContribution, pk=form.cleaned_data['pk_contribution'])
        user = contribution.user
        contribution.delete()

        messages.success(
            self.request, _('Vous avez enlevé {} de la liste des contributeurs de {}.').format(user.username, _type))
        self.success_url = self.object.get_absolute_url()

        return super(RemoveContributorFromContent, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _("Les contributeurs sélectionnés n'existent pas."))
        self.success_url = self.object.get_absolute_url()
        return super(RemoveContributorFromContent, self).form_valid(form)


class AddAuthorToContent(LoggedWithReadWriteHability, SingleContentFormViewMixin):
    only_draft_version = True
    must_be_author = True
    form_class = AuthorForm
    authorized_for_staff = True

    def get(self, request, *args, **kwargs):
        content = self.get_object()
        url = 'content:find-{}'.format('tutorial' if content.is_tutorial() else content.type.lower())
        return redirect(url, self.request.user)

    def form_valid(self, form):

        _type = _("de l'article")

        if self.object.is_tutorial:
            _type = _('du tutoriel')
        elif self.object.is_opinion:
            _type = _('du billet')

        bot = get_object_or_404(User, username=settings.ZDS_APP['member']['bot_account'])
        all_authors_pk = [author.pk for author in self.object.authors.all()]
        for user in form.cleaned_data['users']:
            if user.pk not in all_authors_pk:
                self.object.authors.add(user)
                if self.object.validation_private_message:
                    self.object.validation_private_message.add_participant(user)
                all_authors_pk.append(user.pk)
                if user != self.request.user:
                    url_index = reverse(self.object.type.lower() + ':find-' + self.object.type.lower(), args=[user.pk])
                    send_mp(
                        bot,
                        [user],
                        format_lazy('{}{}', _('Ajout à la rédaction '), _type),
                        self.versioned_object.title,
                        render_to_string('tutorialv2/messages/add_author_pm.md', {
                            'content': self.object,
                            'type': _type,
                            'url': self.object.get_absolute_url(),
                            'index': url_index,
                            'user': user.username
                        }),
                        send_by_mail=True,
                        direct=False,
                        hat=get_hat_from_settings('validation'),
                    )
                UserGallery(gallery=self.object.gallery, user=user, mode=GALLERY_WRITE).save()
        self.object.save(force_slug_update=False)
        self.success_url = self.object.get_absolute_url()

        return super(AddAuthorToContent, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _("Les auteurs sélectionnés n'existent pas."))
        self.success_url = self.object.get_absolute_url()
        return super(AddAuthorToContent, self).form_valid(form)


class RemoveAuthorFromContent(LoggedWithReadWriteHability, SingleContentFormViewMixin):

    form_class = RemoveAuthorForm
    only_draft_version = True
    must_be_author = True
    authorized_for_staff = True

    @staticmethod
    def remove_author(content, user):
        """Remove a user from the authors and ensure that he is access to the content's gallery is also removed.
        The last author is not removed.

        :param content: the content
        :type content: zds.tutorialv2.models.database.PublishableContent
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
        users = form.cleaned_data['users']

        _type = _('cet article')
        if self.object.is_tutorial:
            _type = _('ce tutoriel')
        elif self.object.is_opinion:
            _type = _('ce billet')

        for user in users:
            if RemoveAuthorFromContent.remove_author(self.object, user):
                if user.pk == self.request.user.pk:
                    current_user = True
            else:  # if user is incorrect or alone
                messages.error(self.request,
                               _('Vous êtes le seul auteur de {} ou le membre sélectionné '
                                 'en a déjà quitté la rédaction.').format(_type))
                return redirect(self.object.get_absolute_url())

        self.object.save(force_slug_update=False)

        authors_list = ''

        for index, user in enumerate(form.cleaned_data['users']):
            if index > 0:
                if index == len(users) - 1:
                    authors_list += _(' et ')
                else:
                    authors_list += _(', ')
            authors_list += user.username

        if not current_user:  # if the removed author is not current user
            messages.success(
                self.request, _('Vous avez enlevé {} de la liste des auteurs de {}.').format(authors_list, _type))
            self.success_url = self.object.get_absolute_url()
        else:  # if current user is leaving the content's redaction, redirect him to a more suitable page
            messages.success(self.request, _('Vous avez bien quitté la rédaction de {}.').format(_type))
            self.success_url = reverse(
                self.object.type.lower() + ':find-' + self.object.type.lower(), args=[self.request.user.username]
            )
        return super(RemoveAuthorFromContent, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _("Les auteurs sélectionnés n'existent pas."))
        self.success_url = self.object.get_absolute_url()
        return super(RemoveAuthorFromContent, self).form_valid(form)


class ChangeHelp(LoggedWithReadWriteHability, SingleContentFormViewMixin):
    form_class = ToggleHelpForm

    def form_valid(self, form):
        """
        change help needing state, assume this is ajax request
        :param form: the data
        :return: json answer
        """
        if self.object.is_opinion:
            return HttpResponse(json.dumps({'errors': str(_("Impossible de demander de l'aide pour un billet"))}),
                                status=400, content_type='application/json')
        data = form.cleaned_data
        if data['activated']:
            self.object.helps.add(data['help_wanted'])
        else:
            self.object.helps.remove(data['help_wanted'])
        self.object.save(force_slug_update=False)
        if self.request.is_ajax():
            return HttpResponse(json.dumps({'result': 'ok', 'help_wanted': data['activated']}),
                                content_type='application/json')
        self.success_url = self.object.get_absolute_url()
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.is_ajax():
            return HttpResponse(json.dumps({'errors': form.errors}), status=400, content_type='application/json')
        return super().form_invalid(form)


class ContentOfContributors(ZdSPagingListView):
    type = 'ALL'
    context_object_name = 'contribution_contents'
    paginate_by = settings.ZDS_APP['content']['content_per_page']
    template_name = 'tutorialv2/contributions.html'
    model = PublishableContent

    sorts = OrderedDict([
        ('creation', [lambda q: q.order_by('content__creation_date'), _('Par date de création')]),
        ('abc', [lambda q: q.order_by('content__title'), _('Par ordre alphabétique')]),
        ('modification', [lambda q: q.order_by('-content__update_date'), _('Par date de dernière modification')])
    ])
    sort = ''
    filter = ''
    user = None

    def dispatch(self, request, *args, **kwargs):
        self.user = get_object_or_404(User, username=self.kwargs['username'])
        return super(ContentOfContributors, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        if self.type == 'ALL':
            queryset = ContentContribution.objects.filter(user__pk=self.user.pk, content__sha_public__isnull=False)
        elif self.type in list(TYPE_CHOICES_DICT.keys()):
            queryset = ContentContribution.objects.filter(user__pk=self.user.pk,
                                                          content__sha_public__isnull=False,
                                                          content__type=self.type)
        else:
            raise Http404('Ce type de contenu est inconnu dans le système.')

        # Sort.
        if 'sort' in self.request.GET and self.request.GET['sort'].lower() in self.sorts:
            self.sort = self.request.GET['sort']
        elif not self.sort:
            self.sort = 'abc'
        queryset = self.sorts[self.sort.lower()][0](queryset)
        return queryset

    def get_context_data(self, **kwargs):
        context = super(ContentOfContributors, self).get_context_data(**kwargs)
        context['sorts'] = []
        context['sort'] = self.sort.lower()
        context['subscriber_count'] = NewPublicationSubscription.objects.get_subscriptions(self.user).count()
        context['type'] = self.type.lower()
        contents = list(self.object_list.values_list('content', flat=True).distinct())

        queryset = PublishableContent.objects.filter(pk__in=contents)
        # prefetch:
        queryset = queryset\
            .prefetch_related('authors')\
            .prefetch_related('subcategory')\
            .select_related('licence')\
            .select_related('image')

        context['contribution_tutorials'] = queryset.filter(type='TUTORIAL').all()
        context['contribution_articles'] = queryset.filter(type='ARTICLE').all()

        context['usr'] = self.user
        for sort in list(self.sorts.keys()):
            context['sorts'].append({'key': sort, 'text': self.sorts[sort][1]})
        return context


class ContentOfAuthor(ZdSPagingListView):
    type = 'ALL'
    context_object_name = 'contents'
    paginate_by = settings.ZDS_APP['content']['content_per_page']
    template_name = 'tutorialv2/index.html'
    model = PublishableContent

    authorized_filters = OrderedDict([
        ('public', [lambda p, t: p.get_user_public_contents_queryset(t), _('Publiés'), True, 'tick green']),
        ('validation', [lambda p, t: p.get_user_validate_contents_queryset(t), _('En validation'), False, 'tick']),
        ('beta', [lambda p, t: p.get_user_beta_contents_queryset(t), _('En bêta'), True, 'beta']),
        ('redaction', [lambda p, t: p.get_user_draft_contents_queryset(t), _('Brouillons'), False, 'edit']),
    ])
    sorts = OrderedDict([
        ('creation', [lambda q: q.order_by('creation_date'), _('Par date de création')]),
        ('abc', [lambda q: q.order_by('title'), _('Par ordre alphabétique')]),
        ('modification', [lambda q: q.order_by('-update_date'), _('Par date de dernière modification')])
    ])
    sort = ''
    filter = ''
    user = None

    def dispatch(self, request, *args, **kwargs):
        self.user = get_object_or_404(User, username=self.kwargs['username'])
        if self.user != self.request.user and 'filter' in self.request.GET:
            filter_ = self.request.GET.get('filter').lower()
            if filter_ in self.authorized_filters:
                if not self.authorized_filters[filter_][2]:
                    raise PermissionDenied
            else:
                raise Http404("Le filtre n'est pas autorisé.")
        return super(ContentOfAuthor, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        profile = self.user.profile
        if self.type not in list(TYPE_CHOICES_DICT.keys()):
            raise Http404('Ce type de contenu est inconnu dans le système.')
        _type = self.type
        if self.type == 'ALL':
            _type = None

        # Filter.
        if 'filter' in self.request.GET:
            self.filter = self.request.GET['filter'].lower()
            if self.filter not in self.authorized_filters:
                raise Http404("Le filtre n'est pas autorisé.")
        elif self.user != self.request.user:
            self.filter = 'public'

        if self.filter == '':
            queryset = profile.get_user_contents_queryset(_type=_type)
        else:
            queryset = self.authorized_filters[self.filter][0](profile, _type)
        # prefetch:
        queryset = queryset\
            .prefetch_related('authors')\
            .prefetch_related('subcategory')\
            .select_related('licence')\
            .select_related('image')

        # Sort.
        if 'sort' in self.request.GET and self.request.GET['sort'].lower() in self.sorts:
            self.sort = self.request.GET['sort']
        elif not self.sort:
            self.sort = 'abc'
        queryset = self.sorts[self.sort.lower()][0](queryset)

        return queryset

    def get_context_data(self, **kwargs):
        context = super(ContentOfAuthor, self).get_context_data(**kwargs)
        context['sorts'] = []
        context['filters'] = []
        context['sort'] = self.sort.lower()
        context['filter'] = self.filter.lower()
        context['subscriber_count'] = NewPublicationSubscription.objects.get_subscriptions(self.user).count()
        context['type'] = self.type.lower()

        if self.type == 'ALL':
            contents = list(context['contents'])
            context['tutorials'] = [content for content in contents if content.type == 'TUTORIAL']
            context['articles'] = [content for content in contents if content.type == 'ARTICLE']
            context['opinions'] = [content for content in contents if content.type == 'OPINION']

        context['usr'] = self.user
        for sort in list(self.sorts.keys()):
            context['sorts'].append({'key': sort, 'text': self.sorts[sort][1]})
        for filter_ in list(self.authorized_filters.keys()):
            authorized_filter = self.authorized_filters[filter_]
            if self.user != self.request.user and not authorized_filter[2]:
                continue
            context['filters'].append({'key': filter_, 'text': authorized_filter[1], 'icon': authorized_filter[3]})
        return context


class RedirectOldContentOfAuthor(RedirectView):
    """
    allows to redirect the old lists of users' tutorials/articles/opinions (with
    pks) to the new ones (with usernames and different root).
    """
    permanent = True
    type = None

    def get_redirect_url(self, **kwargs):
        user = User.objects.filter(pk=int(kwargs['pk'])).first()
        route = None

        if self.type == 'TUTORIAL':
            route = 'tutorial:find-tutorial'
        elif self.type == 'ARTICLE':
            route = 'article:find-article'
        elif self.type == 'OPINION':
            route = 'opinion:find-opinion'

        if not route:
            raise Http404('Ce type de contenu est inconnu dans le système')

        return reverse(route, args=[user.username])


class AddSuggestion(LoggedWithReadWriteHability, SingleContentFormViewMixin):
    only_draft_version = True
    authorized_for_staff = True

    def post(self, request, *args, **kwargs):
        publication = get_object_or_404(PublishableContent, pk=kwargs['pk'])

        _type = _('cet article')
        if publication.is_tutorial:
            _type = _('ce tutoriel')
        elif self.object.is_opinion:
            raise PermissionDenied

        if 'options' in request.POST:
            options = request.POST.getlist('options')
            for option in options:
                suggestion = get_object_or_404(PublishableContent, pk=option)
                if ContentSuggestion.objects.filter(publication=publication, suggestion=suggestion).exists():
                    messages.error(self.request, _(
                        'Le contenu "{}" fait déjà partie des suggestions de {}'.format(suggestion.title, _type)))
                elif suggestion.pk == publication.pk:
                    messages.error(self.request, _(
                        'Vous ne pouvez pas ajouter {} en tant que suggestion pour lui même.'.format(_type)))
                elif suggestion.is_opinion and suggestion.sha_picked != suggestion.sha_public:
                    messages.error(self.request, _(
                        'Vous ne pouvez pas suggerer pour {} un billet qui n\'a pas été mis en avant.'.format(_type)))
                elif not suggestion.sha_public:
                    messages.error(self.request, _(
                        'Vous ne pouvez pas suggerer pour {} un contenu qui n\'a pas été publié.'.format(_type)))
                else:
                    obj_suggestion = ContentSuggestion(publication=publication, suggestion=suggestion)
                    obj_suggestion.save()
                    messages.info(self.request, _(
                        'Le contenu "{}" a été ajouté dans les suggestions de {}'.format(suggestion.title, _type)))

        if self.object.public_version:
            return redirect(self.object.get_absolute_url_online())
        else:
            return redirect(self.object.get_absolute_url())


class RemoveSuggestion(LoggedWithReadWriteHability, SingleContentFormViewMixin):

    form_class = RemoveSuggestionForm
    only_draft_version = True
    authorized_for_staff = True

    def form_valid(self, form):
        _type = _('cet article')
        if self.object.is_tutorial:
            _type = _('ce tutoriel')
        elif self.object.is_opinion:
            raise PermissionDenied

        content_suggestion = get_object_or_404(ContentSuggestion, pk=form.cleaned_data['pk_suggestion'])
        content_suggestion.delete()

        messages.success(
            self.request,
            _('Vous avez enlevé "{}" de la liste des suggestions de {}.').format(content_suggestion.suggestion.title,
                                                                                 _type))

        if self.object.public_version:
            self.success_url = self.object.get_absolute_url_online()
        else:
            self.success_url = self.object.get_absolute_url()

        return super(RemoveSuggestion, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, str(_("Les suggestions sélectionnées n'existent pas.")))
        if self.object.public_version:
            self.success_url = self.object.get_absolute_url_online()
        else:
            self.success_url = self.object.get_absolute_url()
        return super(RemoveSuggestion, self).form_valid(form)
