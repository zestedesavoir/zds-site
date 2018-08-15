import tempfile
from datetime import datetime
import time
import zipfile
import shutil
import os

from PIL import Image as ImagePIL
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect
from django.views.generic import CreateView, UpdateView, DeleteView, FormView, View
from django.shortcuts import redirect, get_object_or_404
from django.core.files import File
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.mixins import LoginRequiredMixin

from zds.gallery.forms import ArchiveImageForm, ImageForm, UpdateImageForm, \
    GalleryForm, UpdateGalleryForm, UserGalleryForm, ImageAsAvatarForm
from zds.gallery.models import UserGallery, Image, Gallery, GALLERY_WRITE
from zds.gallery.mixins import GalleryCreateMixin, GalleryMixin, GalleryUpdateOrDeleteMixin, ImageMixin,\
    NoMoreUserWithWriteIfLeave
from zds.member.decorator import LoggedWithReadWriteHability
from zds.utils import slugify
from zds.utils.paginator import ZdSPagingListView
from zds.tutorialv2.models.database import PublishableContent


class ListGallery(LoginRequiredMixin, ZdSPagingListView):
    """Display the gallery list with all their images"""

    object = UserGallery
    template_name = 'gallery/gallery/list.html'
    context_object_name = 'user_galleries'
    paginate_by = settings.ZDS_APP['gallery']['gallery_per_page']

    def get_queryset(self):
        return UserGallery.objects.filter(user=self.request.user).prefetch_related('gallery').all()

    def get_context_data(self, **kwargs):
        context = super(ListGallery, self).get_context_data(**kwargs)

        # fetch content linked to galleries:
        pk_list = [g.gallery.pk for g in context['user_galleries']]
        contents_linked = {}
        contents = PublishableContent.objects.prefetch_related('gallery').filter(gallery__pk__in=pk_list).all()

        for content in contents:
            contents_linked[content.gallery.pk] = content

        # link galleries to contents
        galleries = []
        for g in context['user_galleries']:
            content = None if g.gallery.pk not in contents_linked else contents_linked[g.gallery.pk]
            galleries.append((g, g.gallery, content))

        context['galleries'] = galleries

        return context


class NewGallery(GalleryCreateMixin, LoggedWithReadWriteHability, FormView):
    """Create a new gallery"""

    template_name = 'gallery/gallery/new.html'
    form_class = GalleryForm

    def form_valid(self, form):
        self.perform_create(form.cleaned_data['title'], self.request.user, form.cleaned_data['subtitle'])
        self.success_url = self.gallery.get_absolute_url()

        return super().form_valid(form)


class GalleryDetails(LoginRequiredMixin, GalleryMixin, ZdSPagingListView):
    """Gallery details"""

    object = Image
    template_name = 'gallery/gallery/details.html'
    context_object_name = 'images'
    paginate_by = settings.ZDS_APP['gallery']['images_per_page']

    def get(self, request, *args, **kwargs):
        try:
            self.get_gallery(kwargs.get('pk'), kwargs.get('slug'))
        except Gallery.DoesNotExist:
            raise Http404()

        if not self.has_access_to_gallery(request.user):
            raise PermissionDenied()

        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return self.gallery.get_images().order_by('title')

    def get_context_data(self, **kwargs):
        context = super(GalleryDetails, self).get_context_data(**kwargs)

        context['permissions'] = self.users_and_permissions[self.request.user.pk]
        context['form'] = UserGalleryForm(gallery=self.gallery)
        context['gallery'] = self.gallery
        context['content_linked'] = self.linked_content()
        context['current_user'] = self.request.user

        return context


class EditGallery(LoggedWithReadWriteHability, GalleryUpdateOrDeleteMixin, FormView):
    """Update gallery information"""

    template_name = 'gallery/gallery/edit.html'
    form_class = UpdateGalleryForm

    def dispatch(self, *args, **kwargs):
        try:
            self.get_gallery(pk=self.kwargs.get('pk'), slug=self.kwargs.get('slug'))
        except Gallery.DoesNotExist:
            raise Http404()

        if not self.has_access_to_gallery(self.request.user, True):
            raise PermissionDenied()

        if self.linked_content() is not None:
            raise PermissionDenied()

        return super().dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'instance': self.gallery})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['permissions'] = self.users_and_permissions[self.request.user.pk]
        context['gallery'] = self.gallery

        return context

    def form_valid(self, form):

        self.perform_update({
            'title': form.cleaned_data['title'],
            'subtitle': form.cleaned_data['subtitle'],
        })

        self.success_url = self.gallery.get_absolute_url()
        return super().form_valid(form)


class DeleteGalleries(LoggedWithReadWriteHability, GalleryUpdateOrDeleteMixin, View):

    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        if 'g_items' in request.POST:
            list_items = request.POST.getlist('g_items')

            # Don't delete gallery when it's link to a content
            free_galleries = []
            for g_pk in list_items:

                # check if the gallery is not linked to a content
                v2_content = PublishableContent.objects.filter(gallery__pk=g_pk).first()
                has_v2_content = v2_content is not None
                if has_v2_content:
                    gallery = Gallery.objects.get(pk=g_pk)

                    _type = _('au tutoriel')
                    if v2_content.is_article:
                        _type = _('à l\'article')
                    elif v2_content.is_opinion:
                        _type = _('à la tribune')

                    error_message = _('La galerie « {} » ne peut pas être supprimée car elle est liée {} « {} ».') \
                        .format(gallery.title, _type, v2_content.title)
                    messages.error(request, error_message)
                else:
                    free_galleries.append(g_pk)

            # Check that the user has the RW right on each gallery
            perms = UserGallery.objects.filter(gallery__pk__in=free_galleries, user=request.user, mode='W').count()
            if perms < len(free_galleries):
                raise PermissionDenied

            # Delete all
            UserGallery.objects.filter(gallery__pk__in=free_galleries).delete()
            Gallery.objects.filter(pk__in=free_galleries).delete()
            messages.success(request, _('Tout a été supprimé !'))

        elif 'delete' in request.POST:
            try:
                self.get_gallery(request.POST.get('gallery'))
            except Gallery.DoesNotExist:
                raise Http404()

            if not self.has_access_to_gallery(self.request.user, True) or self.linked_content() is not None:
                raise PermissionDenied()

            self.perform_delete()

        success_url = reverse('gallery-list')
        return HttpResponseRedirect(success_url)


class EditGalleryMembers(LoggedWithReadWriteHability, GalleryUpdateOrDeleteMixin, FormView):
    """Update gallery members"""

    form_class = UserGalleryForm
    http_method_names = ['post']

    def dispatch(self, *args, **kwargs):
        try:
            self.get_gallery(pk=self.kwargs.get('pk'), slug=self.kwargs.get('slug'))
        except Gallery.DoesNotExist:
            raise Http404()

        if self.linked_content() is not None:
            raise PermissionDenied()

        return super().dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'gallery': self.gallery})
        return kwargs

    def form_invalid(self, form):
        messages.error(self.request, _('Impossible de mettre à jour la liste des utilisateurs'))
        return redirect(self.gallery.get_absolute_url())

    def form_valid(self, form):
        action = form.cleaned_data['action']
        user = get_object_or_404(User, username=form.cleaned_data['user'])
        can_write = form.cleaned_data['mode'] == GALLERY_WRITE
        has_deleted = False

        modify_self = user.pk == self.request.user.pk

        if modify_self and action != 'leave':
            raise PermissionDenied()
        elif not self.has_access_to_gallery(self.request.user, not modify_self):
            raise PermissionDenied()

        if action == 'add':
            if user.pk not in self.users_and_permissions:
                self.perform_update_user(user, can_write, allow_modify=False)
            else:
                messages.error(self.request, _('Impossible d\'ajouter un utilisateur qui l\'est déjà'))
        elif action == 'edit':
            if user.pk in self.users_and_permissions:
                self.perform_update_user(user, can_write, allow_modify=True)
            else:
                messages.error(self.request, _('Impossible de modifier un utilisateur non ajouté'))
        elif action == 'leave':
            if user.pk in self.users_and_permissions:
                try:
                    has_deleted = self.perform_leave(user)
                    if has_deleted:
                        messages.info(self.request, _('La galerie a été supprimée par manque d\'utilisateur'))
                    elif modify_self:
                        messages.info(self.request, _('Vous avez bien quitté la galerie'))
                except NoMoreUserWithWriteIfLeave:
                    modify_self = False
                    messages.error(
                        self.request,
                        _('Vous ne pouvez pas quitter la galerie, '
                          'car plus aucun autre utilisateur n\'a les droits d\'écriture'))
            else:
                messages.error(self.request, _('Impossible de supprimer un utilisateur non ajouté'))

        if not has_deleted and not modify_self:
            self.success_url = self.gallery.get_absolute_url()
        else:
            self.success_url = reverse('gallery-list')

        return super().form_valid(form)


class ImageFromGalleryViewMixin(GalleryMixin, View):
    """Mixin that ensure the access to the gallery and fill context data properly"""

    must_write = False  # if True, check for user write access

    def dispatch(self, request, *args, **kwargs):
        try:
            self.get_gallery(pk=self.kwargs.get('pk_gallery'), slug=self.kwargs.get('slug'))
        except Gallery.DoesNotExist:
            raise Http404()

        if not self.has_access_to_gallery(request.user, self.must_write):
            raise PermissionDenied()

        return super().dispatch(request, *args, **kwargs)


class ImageFromGalleryContextViewMixin(ImageFromGalleryViewMixin):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['gallery'] = self.gallery
        context['permissions'] = self.users_and_permissions[self.request.user.pk]
        context['content_linked'] = self.linked_content()

        return context


class NewImage(ImageFromGalleryContextViewMixin, LoggedWithReadWriteHability, CreateView):
    """Creates a new image."""

    form_class = ImageForm
    template_name = 'gallery/image/new.html'
    must_write = True  # only allowed users can insert images

    def form_valid(self, form):

        context = self.get_context_data(**self.kwargs)

        img = Image()
        img.gallery = context['gallery']
        img.title = form.cleaned_data['title']

        if form.cleaned_data['legend'] and form.cleaned_data['legend'] != '':
            img.legend = form.cleaned_data['legend']
        else:
            img.legend = img.title

        img.physical = self.request.FILES['physical']
        img.pubdate = datetime.now()
        img.save()

        return redirect(reverse('gallery-image-edit', args=[img.gallery.pk, img.pk]))


class EditImage(ImageFromGalleryContextViewMixin, ImageMixin, LoggedWithReadWriteHability, UpdateView):
    """Edit or view an existing image."""

    model = Image
    form_class = UpdateImageForm
    template_name = 'gallery/image/edit.html'

    def get_object(self, queryset=None):
        try:
            return self.get_image(self.kwargs.get('pk'))
        except Image.DoesNotExist:
            raise Http404()

    def get_context_data(self, **kwargs):
        context = super(EditImage, self).get_context_data(**kwargs)

        context['as_avatar_form'] = ImageAsAvatarForm()
        return context

    def form_valid(self, form):
        if not self.has_access_to_gallery(self.request.user, True):
            raise PermissionDenied()

        img = self.object

        if img.gallery != self.gallery:
            raise PermissionDenied

        can_change = True

        if 'physical' in self.request.FILES:  # the user request to change the image
            if self.request.FILES['physical'].size > settings.ZDS_APP['gallery']['image_max_size']:
                messages.error(
                    self.request,
                    _('Votre image est beaucoup trop lourde, réduisez sa taille à moins de {:.0f} '
                      '<abbr title="kibioctet">Kio</abbr> avant de l\'envoyer.').format(
                        settings.ZDS_APP['gallery']['image_max_size'] / 1024))

                can_change = False
            else:
                img.physical = self.request.FILES['physical']
                img.slug = slugify(self.request.FILES['physical'])

        if can_change:
            img.title = form.cleaned_data['title']
            img.legend = form.cleaned_data['legend']
            img.update = datetime.now()
            img.save()

        return redirect(reverse('gallery-image-edit', args=[img.gallery.pk, img.pk]))


class DeleteImages(ImageFromGalleryViewMixin, ImageMixin, LoggedWithReadWriteHability, DeleteView):
    """Delete a given image"""

    model = Image
    http_method_names = ['post', 'delete']
    must_write = True

    def delete(self, request, *args, **kwargs):

        if 'delete_multi' in request.POST:
            list_items = request.POST.getlist('g_items')
            Image.objects.filter(pk__in=list_items, gallery=self.gallery).delete()
        elif 'delete' in request.POST:
            try:
                self.get_image(self.request.POST.get('image')).delete()
            except Image.DoesNotExist:
                raise Http404()

        return redirect(self.gallery.get_absolute_url())


class ImportImages(ImageFromGalleryContextViewMixin, LoggedWithReadWriteHability, FormView):
    """Create images from zip archive."""

    form_class = ArchiveImageForm
    http_method_names = ['get', 'post', 'put']
    template_name = 'gallery/image/import.html'
    must_write = True  # only allowed user can import new images

    def form_valid(self, form):
        archive = self.request.FILES['file']
        temp = os.path.join(tempfile.gettempdir(), str(time.time()))

        if not os.path.exists(temp):
            os.makedirs(temp)
        zfile = zipfile.ZipFile(archive, 'a')

        for i in zfile.namelist():
            filename = os.path.split(i)[1]

            ph_temp = os.path.abspath(os.path.join(temp, os.path.basename(i)))

            if not filename.strip():  # don't deal with directory
                continue

            # create file for image
            f_im = open(ph_temp, 'wb')
            f_im.write(zfile.read(i))
            f_im.close()
            (title, ext) = os.path.splitext(os.path.basename(i))

            # if size is too large, don't save
            if os.stat(ph_temp).st_size > settings.ZDS_APP['gallery']['image_max_size']:
                messages.error(
                    self.request, _('Votre image "{}" est beaucoup trop lourde, réduisez sa taille à moins de {:.0f}'
                                    "Kio avant de l'envoyer.").format(
                                        title, settings.ZDS_APP['gallery']['image_max_size'] / 1024))
                continue

            # if it's not an image, pass
            try:
                ImagePIL.open(ph_temp)
            except OSError:
                continue

            # create picture in database:
            f_im = File(open(ph_temp, 'rb'))
            f_im.name = title + ext

            pic = Image()
            pic.gallery = self.gallery
            pic.title = title
            pic.legend = ''
            pic.pubdate = datetime.now()
            pic.physical = f_im
            pic.save()
            f_im.close()

            if os.path.exists(ph_temp):
                os.remove(ph_temp)

        zfile.close()

        if os.path.exists(temp):
            shutil.rmtree(temp)

        self.success_url = self.gallery.get_absolute_url()
        return super().form_valid(form)
