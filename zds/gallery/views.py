#!/usr/bin/python
# -*- coding: utf-8 -*-

import tempfile

from datetime import datetime
import time

from PIL import Image as ImagePIL
from django.conf import settings
from django.contrib import messages
from django.http import Http404, HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, get_object_or_404, render
from zds.gallery.forms import ArchiveImageForm, ImageForm, UpdateImageForm, \
    GalleryForm, UpdateGalleryForm, UserGalleryForm, ImageAsAvatarForm
from zds.gallery.models import UserGallery, Image, Gallery
from zds.member.decorator import can_write_and_read_now
from zds.utils import slugify
from zds.utils.paginator import ZdSPagingListView
from django.core.exceptions import ObjectDoesNotExist

from django.core.files import File
import zipfile
import shutil
import os
from django.utils.translation import ugettext_lazy as _

from django.views.generic import CreateView, UpdateView, DeleteView, FormView
from django.utils.decorators import method_decorator
from zds.tutorialv2.models.models_database import PublishableContent


class ListGallery(ZdSPagingListView):
    """Display the gallery list with all their images"""

    object = UserGallery
    template_name = 'gallery/gallery/list.html'
    context_object_name = 'user_galleries'
    paginate_by = settings.ZDS_APP['gallery']['gallery_per_page']

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ListGallery, self).dispatch(*args, **kwargs)

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


class NewGallery(CreateView):
    """Create a new gallery"""

    template_name = 'gallery/gallery/new.html'
    form_class = GalleryForm

    @method_decorator(login_required)
    @method_decorator(can_write_and_read_now)
    def dispatch(self, *args, **kwargs):
        return super(NewGallery, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        gallery = Gallery()
        gallery.title = form.cleaned_data['title']
        gallery.subtitle = form.cleaned_data['subtitle']
        gallery.slug = slugify(form.cleaned_data['title'])
        gallery.pubdate = datetime.now()
        gallery.save()

        # Attach user :
        userg = UserGallery()
        userg.gallery = gallery
        userg.mode = 'W'
        userg.user = self.request.user
        userg.save()

        return HttpResponseRedirect(gallery.get_absolute_url())


def ensure_user_access(gallery, user, can_write=False):
    """
    :param gallery: the gallery
    :param user: user who want to access the gallery
    :param can_write: check if the user has the writing access to the gallery
    :return: the gallery of the user
    :rtype: UserGallery
    :raise PermissionDenied: if the user has not access or no write permission (if applicable)
    """

    try:
        user_gallery = UserGallery.objects.get(gallery=gallery, user=user)

        if user_gallery:
            if can_write and not user_gallery.can_write():
                raise PermissionDenied
        else:
            raise PermissionDenied
    except ObjectDoesNotExist:  # the user_gallery does not exists
        raise PermissionDenied

    return user_gallery


class GalleryDetails(ZdSPagingListView):
    """Gallery details"""
    object = UserGallery
    template_name = 'gallery/gallery/details.html'
    context_object_name = 'images'
    paginate_by = settings.ZDS_APP['gallery']['images_per_page']

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(GalleryDetails, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        self.pkey = self.kwargs.pop('pk', None)
        self.slug = self.kwargs.pop('slug', None)
        self.gallery = get_object_or_404(Gallery, pk=self.pkey, slug=self.slug)
        self.user_access = ensure_user_access(self.gallery, self.request.user, can_write=True)
        return self.gallery.get_images().order_by('title')

    def get_context_data(self, **kwargs):
        context = super(GalleryDetails, self).get_context_data(**kwargs)
        context['gallery_mode'] = self.user_access
        context['form'] = UserGalleryForm
        context['gallery'] = self.gallery
        return context


class EditGallery(UpdateView):
    """Update gallery information"""

    model = Gallery
    template_name = 'gallery/gallery/edit.html'
    form_class = UpdateGalleryForm

    @method_decorator(login_required)
    @method_decorator(can_write_and_read_now)
    def dispatch(self, *args, **kwargs):
        return super(EditGallery, self).dispatch(*args, **kwargs)

    def get_object(self, queryset=None):

        pkey = self.kwargs.pop('pk', None)
        slug = self.kwargs.pop('slug', None)
        gallery = get_object_or_404(Gallery, pk=pkey, slug=slug)

        ensure_user_access(gallery, self.request.user, can_write=True)

        return gallery

    def form_valid(self, form):

        self.object.slug = slugify(form.cleaned_data['title'])
        return super(EditGallery, self).form_valid(form)


@can_write_and_read_now
@require_POST
@login_required
def modify_gallery(request):
    """Modify gallery instance: delete galleries or add user to them"""

    # Global actions

    if 'delete_multi' in request.POST:
        list_items = request.POST.getlist('g_items')

        # Don't delete gallery when it's link to tutorial
        free_galleries = []
        for g_pk in list_items:

            # check if the gallery is not linked to a content
            v2_content = PublishableContent.objects.filter(gallery__pk=g_pk).first()
            has_v2_content = v2_content is not None
            if has_v2_content:
                gallery = Gallery.objects.get(pk=g_pk)

                _type = _(u'au tutoriel')
                if v2_content.is_article:
                    _type = _(u'à l\'article')
                elif v2_content.is_opinion:
                    _type = _(u'à la tribune')

                error_message = _(u'La galerie « {} » ne peut pas être supprimée car elle est liée {} « {} ».')\
                    .format(gallery.title, _type, v2_content.title)
                messages.error(request, error_message)
            else:
                free_galleries.append(g_pk)

        perms = UserGallery.objects.filter(gallery__pk__in=free_galleries, user=request.user, mode='W').count()

        # Check that the user has the RW right on each gallery

        if perms < len(free_galleries):
            raise PermissionDenied

        # Delete all the permissions on all the selected galleries

        UserGallery.objects.filter(gallery__pk__in=free_galleries).delete()

        # Delete all the images of the gallery (autodelete of file)

        Image.objects.filter(gallery__pk__in=free_galleries).delete()

        # Finally delete the selected galleries

        Gallery.objects.filter(pk__in=free_galleries).delete()
        return redirect(reverse('gallery-list'))

    elif 'adduser' in request.POST:
        # Gallery-specific actions

        try:
            gal_pk = request.POST['gallery']
        except KeyError:
            raise Http404
        gallery = get_object_or_404(Gallery, pk=gal_pk)

        # Disallow actions to read-only members

        try:
            gal_mode = UserGallery.objects.get(gallery=gallery,
                                               user=request.user)
            if gal_mode.mode != 'W':
                raise PermissionDenied
        except:
            raise PermissionDenied
        form = UserGalleryForm(request.POST)
        if form.is_valid():
            user = get_object_or_404(User, username=request.POST['user'])

            # If a user is already in a user gallery, we don't add him.

            galleries = UserGallery.objects.filter(gallery=gallery,
                                                   user=user).all()
            if galleries.count() > 0:
                return redirect(gallery.get_absolute_url())
            if user.profile.is_private():
                return redirect(gallery.get_absolute_url())
            user_gal = UserGallery()
            user_gal.user = user
            user_gal.gallery = gallery
            user_gal.mode = request.POST['mode']
            user_gal.save()
        else:
            return render(request, 'gallery/gallery/details.html', {
                'gallery': gallery,
                'gallery_mode': gal_mode,
                'images': gallery.get_images(),
                'form': form,
            })
        return redirect(gallery.get_absolute_url())


class GalleryMixin(object):
    """Mixin that ensure the access to the gallery and fill context data properly"""

    can_write = False  # if `True`, check for user write access

    def get_context_data(self, **kwargs):
        context = super(GalleryMixin, self).get_context_data(**kwargs)
        pk_gallery = self.kwargs.pop('pk_gallery', None)

        gallery = get_object_or_404(Gallery, pk=pk_gallery)

        user_gallery = ensure_user_access(gallery, self.request.user, can_write=self.can_write)

        context['gallery'] = gallery
        context['gallery_mode'] = user_gallery

        return context


class NewImage(GalleryMixin, CreateView):
    """Creates a new image."""

    form_class = ImageForm
    template_name = 'gallery/image/new.html'
    can_write = True  # only allowed users can insert images

    @method_decorator(login_required)
    @method_decorator(can_write_and_read_now)
    def dispatch(self, *args, **kwargs):
        return super(NewImage, self).dispatch(*args, **kwargs)

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


class EditImage(GalleryMixin, UpdateView):
    """Edit or view an existing image."""

    model = Image
    form_class = UpdateImageForm
    template_name = 'gallery/image/edit.html'

    @method_decorator(login_required)
    @method_decorator(can_write_and_read_now)
    def dispatch(self, *args, **kwargs):
        return super(EditImage, self).dispatch(*args, **kwargs)

    def get_object(self, queryset=None):
        pkey = self.kwargs.pop('pk', None)
        return get_object_or_404(Image, pk=pkey)

    def get_context_data(self, **kwargs):
        context = super(EditImage, self).get_context_data(**kwargs)

        context['as_avatar_form'] = ImageAsAvatarForm()

        return context

    def form_valid(self, form):
        self.can_write = True  # only allowed users can change images
        context = self.get_context_data(**self.kwargs)
        img = self.object
        gallery = context['gallery']

        if img.gallery != gallery:
            raise PermissionDenied

        can_change = True

        if 'physical' in self.request.FILES:  # the user request to change the image
            if self.request.FILES['physical'].size > settings.ZDS_APP['gallery']['image_max_size']:
                messages.error(
                    self.request,
                    _(u'Votre image est beaucoup trop lourde, réduisez sa taille à moins de {:.0f} '
                      u'<abbr title="kibioctet">Kio</abbr> avant de l\'envoyer.').format(
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


class DeleteImages(DeleteView):
    """Delete a given image"""

    model = Image
    http_method_names = ['post', 'delete']

    @method_decorator(login_required)
    @method_decorator(can_write_and_read_now)
    def dispatch(self, *args, **kwargs):
        return super(DeleteImages, self).dispatch(*args, **kwargs)

    def delete(self, request, *args, **kwargs):

        pk_gallery = self.request.POST['gallery']
        gallery = get_object_or_404(Gallery, pk=pk_gallery)
        ensure_user_access(gallery, request.user, can_write=True)

        if 'delete_multi' in request.POST:
            list_items = request.POST.getlist('g_items')
            Image.objects.filter(pk__in=list_items, gallery=gallery).delete()
        elif 'delete' in request.POST:
            pkey = self.request.POST['image']
            img = get_object_or_404(Image, pk=pkey)

            if img.gallery != gallery:
                raise PermissionDenied

            img.delete()

        return redirect(gallery.get_absolute_url())


class ImportImages(GalleryMixin, FormView):
    """Create images from zip archive."""

    form_class = ArchiveImageForm
    http_method_names = ['get', 'post', 'put']
    template_name = 'gallery/image/import.html'
    can_write = True  # only allowed user can import new images

    @method_decorator(login_required)
    @method_decorator(can_write_and_read_now)
    def dispatch(self, *args, **kwargs):
        return super(ImportImages, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        context = self.get_context_data()
        gallery = context['gallery']

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
                    self.request, _(u'Votre image "{}" est beaucoup trop lourde, réduisez sa taille à moins de {:.0f}'
                                    u"Kio avant de l'envoyer.").format(
                                        title, settings.ZDS_APP['gallery']['image_max_size'] / 1024))
                continue

            # if it's not an image, pass
            try:
                ImagePIL.open(ph_temp)
            except IOError:
                continue

            # create picture in database:
            f_im = File(open(ph_temp, 'rb'))
            f_im.name = title + ext

            pic = Image()
            pic.gallery = gallery
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

        return redirect(gallery.get_absolute_url())
