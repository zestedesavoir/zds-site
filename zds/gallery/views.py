# -*- coding: utf-8 -*-

# The max size in bytes

from datetime import datetime
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import redirect, get_object_or_404

from zds.member.decorator import can_read_now, can_write_and_read_now
from zds.gallery.forms import ImageForm, GalleryForm, UserGalleryForm
from zds.gallery.models import UserGallery, Image, Gallery
from zds.utils import render_template, slugify

@can_read_now
@login_required
def gallery_list(request):
    '''
    Display the gallery list with all their images
    '''
    galleries = UserGallery.objects.all().filter(user=request.user)

    return render_template('gallery/gallery_list.html', {
        'galleries': galleries
    })

@can_read_now
@login_required
def gallery_details(request, gal_pk, gal_slug):
    '''
    Gallery details
    '''

    gal = get_object_or_404(Gallery, pk=gal_pk)
    gal_mode = get_object_or_404(UserGallery, gallery=gal, user=request.user)
    images = gal.get_images()

    return render_template('gallery/gallery_details.html', {
        'gallery': gal,
        'gallery_mode': gal_mode,
        'images': images
    })

@can_write_and_read_now
@login_required
def new_gallery(request):
    '''
    Creates a new gallery
    '''
    if request.method == 'POST':
        form = GalleryForm(request.POST)
        if form.is_valid():
            data = form.data
            # Creating the gallery
            gal = Gallery()
            gal.title = data['title']
            gal.subtitle = data['subtitle']
            gal.slug = slugify(data['title'])
            gal.pubdate = datetime.now()
            gal.save()

            # Attach user
            userg = UserGallery()
            userg.gallery = gal
            userg.mode = 'W'
            userg.user = request.user
            userg.save()

            return redirect(gal.get_absolute_url())

        else:
            # TODO: add errors to the form and return it
            raise Http404
    else:
        form = GalleryForm()
        return render_template('gallery/new_gallery.html', {
            'form': form
        })

@can_write_and_read_now
@login_required
def modify_gallery(request):
    '''Modify gallery instance'''

    if request.method != 'POST':
        raise Http404

    # Global actions

    if 'delete_multi' in request.POST:
        l = request.POST.getlist('items')

        perms = UserGallery.objects\
                .filter(gallery__pk__in=l, user=request.user, mode='W')\
                .count()

        # Check that the user has the RW right on each gallery
        if perms < len(l):
            raise Http404

        # Delete all the permissions on all the selected galleries
        UserGallery.objects.filter(gallery__pk__in=l).delete()
        # Delete all the images of the gallery (autodelete of file)
        Image.objects.filter(gallery__pk__in=l).delete()
        # Finally delete the selected galleries
        Gallery.objects.filter(pk__in=l).delete()

        return redirect(reverse('zds.gallery.views.gallery_list'))

    # Gallery-specific actions

    try:
        gal_pk = request.POST['gallery']
    except KeyError:
        raise Http404

    gal = get_object_or_404(Gallery, pk=gal_pk)
    gal_mode = get_object_or_404(UserGallery, gallery=gal, user=request.user)

    # Disallow actions to read-only members
    if gal_mode.mode != 'W':
        raise Http404

    if 'adduser' in request.POST:
        form = UserGalleryForm(request.POST)
        u = get_object_or_404(User, username=request.POST['user'])
        if form.is_valid():
            ug = UserGallery()
            ug.user = u
            ug.gallery = gal
            ug.mode = 'W'
            ug.save()


    return redirect(gal.get_absolute_url())

@can_write_and_read_now
@login_required
def del_image(request, gal_pk):
    gal = get_object_or_404(Gallery, pk=gal_pk)
    if request.method == 'POST':
        liste = request.POST.getlist('items')
        Image.objects.filter(pk__in=liste).delete()
        return redirect(gal.get_absolute_url())
    return redirect(gal.get_absolute_url())

@can_write_and_read_now
@login_required
def edit_image(request, gal_pk, img_pk):
    '''
    Creates a new image
    '''
    gal = get_object_or_404(Gallery, pk=gal_pk)
    img = get_object_or_404(Image, pk=img_pk)

    if request.method == 'POST':
        form = ImageForm(request.POST)
        if form.is_valid():
            img.title = request.POST['title']
            img.legend = request.POST['legend']
            img.update = datetime.now()

            img.save()

            # Redirect to the document list after POST
            return redirect(gal.get_absolute_url())
        else:
            # TODO: add errors to the form and return it
            raise Http404
    else:
        form = ImageForm()  # A empty, unbound form
        return render_template('gallery/edit_image.html', {
            'form': form,
            'gallery': gal,
            'image': img
        })

@can_write_and_read_now
@login_required
def modify_image(request):
    # We only handle secured POST actions
    if request.method != 'POST':
        raise Http404

    try:
        gal_pk = request.POST['gallery']
    except KeyError:
        raise Http404

    gal = get_object_or_404(Gallery, pk=gal_pk)
    gal_mode = get_object_or_404(UserGallery, gallery=gal, user=request.user)

    # Only allow RW users to modify images
    if gal_mode.mode != 'W':
        raise Http404

    if 'delete' in request.POST:
        img = get_object_or_404(Image, pk=request.POST['image'])
        img.delete()

    elif 'delete_multi' in request.POST:
        l = request.POST.getlist('items')
        Image.objects.filter(pk__in=l).delete()

    return redirect(gal.get_absolute_url())

@can_write_and_read_now
@login_required
def new_image(request, gal_pk):
    '''Creates a new image'''
    gal = get_object_or_404(Gallery, pk=gal_pk)

    if request.method == 'POST':
        form = ImageForm(request.POST, request.FILES)
        if form.is_valid() \
           and request.FILES['physical'].size < settings.IMAGE_MAX_SIZE:
            img = Image()
            img.physical = request.FILES['physical']
            img.gallery = gal
            img.title = request.POST['title']
            img.slug = slugify(request.FILES['physical'])
            img.legend = request.POST['legend']
            img.pubdate = datetime.now()

            img.save()

            # Redirect to the document list after POST
            return redirect(gal.get_absolute_url())
        else:
            # TODO: add errors to the form and return it
            raise Http404
    else:
        form = ImageForm()  # A empty, unbound form
        return render_template('gallery/new_image.html', {
            'form': form,
            'gallery': gal
        })
