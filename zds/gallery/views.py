#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime
from PIL import Image as ImagePIL
from django.conf import settings
from django.contrib import messages
from django.http import Http404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, get_object_or_404
from zds.gallery.forms import ArchiveImageForm, ImageForm, UpdateImageForm, \
    GalleryForm, UserGalleryForm, ImageAsAvatarForm
from zds.gallery.models import UserGallery, Image, Gallery
from zds.member.decorator import can_write_and_read_now
from zds.utils import render_template
from zds.utils import slugify
from django.core.exceptions import ObjectDoesNotExist

from django.core.files import File
from zds.tutorial.models import PubliableContent
import zipfile
import shutil
import os
from django.db import transaction


@login_required
def gallery_list(request):
    """Display the gallery list with all their images."""

    galleries = UserGallery.objects.all().filter(user=request.user)
    return render_template("gallery/gallery/list.html",
                           {"galleries": galleries})


@login_required
def gallery_details(request, gal_pk, gal_slug):
    """Gallery details."""

    gal = get_object_or_404(Gallery, pk=gal_pk)
    try:
        gal_mode = UserGallery.objects.get(gallery=gal, user=request.user)
    except:
        raise PermissionDenied
    images = gal.get_images()
    form = UserGalleryForm()

    return render_template("gallery/gallery/details.html", {
        "gallery": gal,
        "gallery_mode": gal_mode,
        "images": images,
        "form": form,
    })


@can_write_and_read_now
@login_required
def new_gallery(request):
    """Creates a new gallery."""

    if request.method == "POST":
        form = GalleryForm(request.POST)
        if form.is_valid():
            data = form.data

            # Creating the gallery

            gal = Gallery()
            gal.title = data["title"]
            gal.subtitle = data["subtitle"]
            gal.slug = slugify(data["title"])
            gal.pubdate = datetime.now()
            gal.save()

            # Attach user

            userg = UserGallery()
            userg.gallery = gal
            userg.mode = "W"
            userg.user = request.user
            userg.save()
            return redirect(gal.get_absolute_url())
        else:
            return render_template("gallery/gallery/new.html", {"form": form})
    else:
        form = GalleryForm()
        return render_template("gallery/gallery/new.html", {"form": form})


@can_write_and_read_now
@require_POST
@login_required
def modify_gallery(request):
    """Modify gallery instance."""

    # Global actions

    if "delete_multi" in request.POST:
        l = request.POST.getlist("items")

        # Don't delete gallery when it's link to tutorial
        free_galleries = []
        for g_pk in l:
            if PubliableContent.objects.filter(gallery__pk=g_pk).exists():
                gallery = Gallery.objects.get(pk=g_pk)
                messages.error(
                    request,
                    "La galerie '{}' ne peut pas être supprimée car elle est liée à un tutoriel existant".format(
                        gallery.title))
            else:
                free_galleries.append(g_pk)

        perms = UserGallery.objects.filter(gallery__pk__in=free_galleries,
                                           user=request.user, mode="W").count()

        # Check that the user has the RW right on each gallery

        if perms < len(free_galleries):
            raise PermissionDenied

        # Delete all the permissions on all the selected galleries

        UserGallery.objects.filter(gallery__pk__in=free_galleries).delete()

        # Delete all the images of the gallery (autodelete of file)

        Image.objects.filter(gallery__pk__in=free_galleries).delete()

        # Finally delete the selected galleries

        Gallery.objects.filter(pk__in=free_galleries).delete()
        return redirect(reverse("zds.gallery.views.gallery_list"))
    elif "adduser" in request.POST:

        # Gallery-specific actions

        try:
            gal_pk = request.POST["gallery"]
        except KeyError:
            raise Http404
        gallery = get_object_or_404(Gallery, pk=gal_pk)

        # Disallow actions to read-only members

        try:
            gal_mode = UserGallery.objects.get(gallery=gallery,
                                               user=request.user)
            if gal_mode.mode != "W":
                raise PermissionDenied
        except:
            raise PermissionDenied
        form = UserGalleryForm(request.POST)
        if form.is_valid():
            user = get_object_or_404(User, username=request.POST["user"])

            # If a user is already in a user gallery, we don't add him.

            galleries = UserGallery.objects.filter(gallery=gallery,
                                                   user=user).all()
            if galleries.count() > 0:
                return redirect(gallery.get_absolute_url())
            ug = UserGallery()
            ug.user = user
            ug.gallery = gallery
            ug.mode = request.POST["mode"]
            ug.save()
        else:
            return render_template("gallery/gallery/details.html", {
                "gallery": gallery,
                "gallery_mode": gal_mode,
                "images": gallery.get_images(),
                "form": form,
            })
    return redirect(gallery.get_absolute_url())


@login_required
@can_write_and_read_now
def edit_image(request, gal_pk, img_pk):
    """Edit or view an existing image."""

    gal = get_object_or_404(Gallery, pk=gal_pk)
    img = get_object_or_404(Image, pk=img_pk)

    # Check if user can edit image
    try:
        gal_mode = UserGallery.objects.get(user=request.user, gallery=gal)
        assert gal_mode is not None
        if not gal_mode.is_write() and request.method != "GET":
            raise PermissionDenied
    except (AssertionError, ObjectDoesNotExist):
        raise PermissionDenied

    # Check if the image belongs to the gallery
    if img.gallery != gal:
        raise PermissionDenied

    if request.method == "POST":
        form = UpdateImageForm(request.POST, request.FILES)
        if form.is_valid():
            if "physical" in request.FILES:
                if request.FILES["physical"].size > settings.ZDS_APP['gallery']['image_max_size']:
                    messages.error(request, u"Votre image est beaucoup trop lourde, "
                                            u"réduisez sa taille à moins de {} "
                                            u"<abbr title=\"kibioctet\">Kio</abbr> "
                                            u"avant de l'envoyer".format(
                                                str(settings.ZDS_APP['gallery']['image_max_size'] / 1024)))
                else:
                    img.title = request.POST["title"]
                    img.legend = request.POST["legend"]
                    img.physical = request.FILES["physical"]
                    img.slug = slugify(request.FILES["physical"])
                    img.update = datetime.now()
                    img.save()
                    # Redirect to the newly uploaded image edit page after POST
                    return redirect(reverse("zds.gallery.views.edit_image", args=[gal.pk, img.pk]))
            else:
                img.title = request.POST["title"]
                img.legend = request.POST["legend"]
                img.update = datetime.now()
                img.save()
                # Redirect to the newly uploaded image edit page after POST
                return redirect(reverse("zds.gallery.views.edit_image", args=[gal.pk, img.pk]))

    else:
        form = UpdateImageForm(initial={
            "title": img.title,
            "legend": img.legend,
            "physical": img.physical,
            "new_image": False,
        })

    as_avatar_form = ImageAsAvatarForm()
    return render_template(
        "gallery/image/edit.html", {
            "form": form,
            "gallery_mode": gal_mode,
            "as_avatar_form": as_avatar_form,
            "gallery": gal,
            "image": img
        })


@can_write_and_read_now
@login_required
@require_POST
def delete_image(request):

    try:
        gal_pk = request.POST["gallery"]
    except KeyError:
        raise Http404
    gal = get_object_or_404(Gallery, pk=gal_pk)
    try:
        gal_mode = UserGallery.objects.get(gallery=gal, user=request.user)
        assert gal_mode is not None

        # Only allow RW users to modify images
        if not gal_mode.is_write():
            raise PermissionDenied
    except:
        raise PermissionDenied
    if "delete" in request.POST:
        try:
            img = Image.objects.get(pk=request.POST["image"], gallery=gal)
            img.delete()
        except:
            pass
    elif "delete_multi" in request.POST:
        l = request.POST.getlist("items")
        Image.objects.filter(pk__in=l, gallery=gal).delete()
    return redirect(gal.get_absolute_url())


@can_write_and_read_now
@login_required
def new_image(request, gal_pk):
    """Creates a new image."""

    gal = get_object_or_404(Gallery, pk=gal_pk)

    # check if the user can upload new image in this gallery
    try:
        gal_mode = UserGallery.objects.get(gallery=gal, user=request.user)
        assert gal_mode is not None
        if not gal_mode.is_write():
            raise PermissionDenied
    except:
        raise PermissionDenied

    if request.method == "POST":
        form = ImageForm(request.POST, request.FILES)
        if form.is_valid():
            img = Image()
            img.physical = request.FILES["physical"]
            img.gallery = gal
            img.title = request.POST["title"]
            img.slug = slugify(request.FILES["physical"])
            img.legend = request.POST["legend"]
            img.pubdate = datetime.now()
            img.save()

            # Redirect to the newly uploaded image edit page after POST
            return redirect(reverse("zds.gallery.views.edit_image",
                                    args=[gal.pk, img.pk]))
        else:
            return render_template("gallery/image/new.html", {"form": form,
                                                              "gallery_mode": gal_mode,
                                                              "gallery": gal})
    else:
        form = ImageForm(initial={"new_image": True})  # A empty, unbound form
        return render_template("gallery/image/new.html", {"form": form,
                                                          "gallery_mode": gal_mode,
                                                          "gallery": gal})


@can_write_and_read_now
@login_required
@transaction.atomic
def import_image(request, gal_pk):
    """Create images from zip archive."""

    gal = get_object_or_404(Gallery, pk=gal_pk)

    try:
        gal_mode = UserGallery.objects.get(gallery=gal, user=request.user)
        assert gal_mode is not None
        if not gal_mode.is_write():
            raise PermissionDenied
    except:
        raise PermissionDenied

    # if request is POST
    if request.method == "POST":
        form = ArchiveImageForm(request.POST, request.FILES)
        if form.is_valid():
            archive = request.FILES["file"]
            temp = os.path.join(settings.SITE_ROOT, "temp")
            if not os.path.exists(temp):
                os.makedirs(temp)
            zfile = zipfile.ZipFile(archive, "a")
            for i in zfile.namelist():
                ph_temp = os.path.abspath(os.path.join(temp, i))
                (dirname, filename) = os.path.split(i)
                # if directory doesn't exist, created on
                if not os.path.exists(os.path.dirname(ph_temp)):
                    os.makedirs(os.path.dirname(ph_temp))
                # if file is directory, don't create file
                if filename.strip() == "":
                    continue
                data = zfile.read(i)
                # create file for image
                fp = open(ph_temp, "wb")
                fp.write(data)
                fp.close()
                title = os.path.basename(i)
                # if size is too large don't save
                if os.stat(ph_temp).st_size > settings.ZDS_APP['gallery']['image_max_size']:
                    messages.error(
                        request,
                        u"L'image {} n'a pas pu être importée dans la gallerie"
                        u" car elle est beaucoup trop lourde".format(title))
                    continue
                # if it's not an image, pass
                try:
                    ImagePIL.open(ph_temp)
                except IOError:
                    continue
                f = File(open(ph_temp, "rb"))
                f.name = title
                # create picture in database
                pic = Image()
                pic.gallery = gal
                pic.title = title
                pic.pubdate = datetime.now()
                pic.physical = f
                pic.save()
                f.close()

            zfile.close()

            if os.path.exists(temp):
                shutil.rmtree(temp)

            # Redirect to the newly uploaded gallery
            return redirect(reverse("zds.gallery.views.gallery_details",
                                    args=[gal.pk, gal.slug]))
        else:
            return render_template("gallery/image/new.html", {"form": form,
                                                              "gallery_mode": gal_mode,
                                                              "gallery": gal})
    else:
        form = ArchiveImageForm(initial={"new_image": True})  # A empty, unbound form
        return render_template("gallery/image/new.html", {"form": form,
                                                          "gallery_mode": gal_mode,
                                                          "gallery": gal})
