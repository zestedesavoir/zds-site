from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, View

from zds.gallery.forms import (
    ArchiveImageForm,
    GalleryForm,
    ImageAsAvatarForm,
    ImageForm,
    UpdateGalleryForm,
    UpdateImageForm,
    UserGalleryForm,
)
from zds.gallery.mixins import (
    GalleryCreateMixin,
    GalleryMixin,
    GalleryUpdateOrDeleteMixin,
    ImageCreateMixin,
    ImageUpdateOrDeleteMixin,
    NoMoreUserWithWriteIfLeave,
    NotAnImage,
    UserAlreadyInGallery,
    UserNotInGallery,
)
from zds.gallery.models import GALLERY_WRITE, Gallery, Image, UserGallery
from zds.member.decorator import LoggedWithReadWriteHability
from zds.tutorialv2.models.database import PublishableContent
from zds.utils.paginator import ZdSPagingListView


class ListGallery(LoginRequiredMixin, ZdSPagingListView):
    """Display the gallery list with all their images"""

    object = UserGallery
    template_name = "gallery/gallery/list.html"
    context_object_name = "galleries"
    paginate_by = settings.ZDS_APP["gallery"]["gallery_per_page"]

    def get_queryset(self):
        return Gallery.objects.galleries_of_user(self.request.user).order_by("pk")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # fetch content linked to galleries:
        linked_contents = {}
        pk_list = [g.linked_content for g in self.object_list if g.linked_content is not None]
        contents = PublishableContent.objects.filter(pk__in=pk_list).all()

        for content in contents:
            linked_contents[content.pk] = content

        context["linked_contents"] = linked_contents

        return context


class NewGallery(GalleryCreateMixin, LoggedWithReadWriteHability, FormView):
    """Create a new gallery"""

    template_name = "gallery/gallery/new.html"
    form_class = GalleryForm

    def form_valid(self, form):
        self.perform_create(form.cleaned_data["title"], self.request.user, form.cleaned_data["subtitle"])
        self.success_url = self.gallery.get_absolute_url()

        return super().form_valid(form)


class GalleryDetails(LoginRequiredMixin, GalleryMixin, ZdSPagingListView):
    """Gallery details"""

    object = Image
    template_name = "gallery/gallery/details.html"
    context_object_name = "images"
    paginate_by = settings.ZDS_APP["gallery"]["images_per_page"]

    def get(self, request, *args, **kwargs):
        try:
            self.get_gallery(kwargs.get("pk"), kwargs.get("slug"))
        except Gallery.DoesNotExist:
            raise Http404()

        if not self.has_access_to_gallery(request.user):
            raise PermissionDenied()

        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return self.gallery.get_images().order_by("title")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["permissions"] = self.users_and_permissions[self.request.user.pk]
        context["form"] = UserGalleryForm(gallery=self.gallery)
        context["gallery"] = self.gallery
        context["content_linked"] = self.linked_content()
        context["current_user"] = self.request.user
        context["mode_choices"] = UserGallery.MODE_CHOICES

        return context


class EditGallery(LoggedWithReadWriteHability, GalleryUpdateOrDeleteMixin, FormView):
    """Update gallery information"""

    template_name = "gallery/gallery/edit.html"
    form_class = UpdateGalleryForm

    def dispatch(self, *args, **kwargs):
        try:
            self.get_gallery(pk=self.kwargs.get("pk"))
        except Gallery.DoesNotExist:
            raise Http404()

        if not self.has_access_to_gallery(self.request.user, True):
            raise PermissionDenied()

        if self.linked_content() is not None:
            raise PermissionDenied()

        return super().dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"instance": self.gallery})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["permissions"] = self.users_and_permissions[self.request.user.pk]
        context["gallery"] = self.gallery

        return context

    def form_valid(self, form):
        self.perform_update(
            {
                "title": form.cleaned_data["title"],
                "subtitle": form.cleaned_data["subtitle"],
            }
        )

        self.success_url = self.gallery.get_absolute_url()
        return super().form_valid(form)


class DeleteGalleries(LoggedWithReadWriteHability, GalleryUpdateOrDeleteMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        if "g_items" in request.POST:
            list_galleries = request.POST.getlist("g_items")

            contents = (
                PublishableContent.objects.filter(gallery__pk__in=list_galleries).prefetch_related("gallery").all()
            )

            # Don't delete gallery when it's linked to a content
            if len(contents) > 0:
                wrong_galleries = []
                for content in contents:
                    gallery = content.gallery

                    _type = _("au tutoriel")
                    if content.is_article:
                        _type = _("à l'article")
                    elif content.is_opinion:
                        _type = _("à la tribune")

                    wrong_galleries.append(
                        _('la galerie "{}" est liée {} "{}"').format(gallery.title, _type, content.title)
                    )

                messages.error(request, _("Impossible de supprimer: {}").format(", ".join(wrong_galleries)))
            else:
                # Check that the user has the RW right on each gallery
                queryset = UserGallery.objects.filter(gallery__pk__in=list_galleries)
                if queryset.filter(user=request.user, mode="W").count() < len(list_galleries):
                    messages.error(request, _("Vous n'avez pas le droit d'écriture sur certaine de ces galeries"))
                else:
                    queryset.delete()
                    Gallery.objects.filter(pk__in=list_galleries).delete()
                    messages.success(request, _("Tout a été supprimé !"))

        elif "delete" in request.POST:
            try:
                self.get_gallery(request.POST.get("gallery"))
            except Gallery.DoesNotExist:
                raise Http404()

            if not self.has_access_to_gallery(self.request.user, True) or self.linked_content() is not None:
                raise PermissionDenied()

            self.perform_delete()

        success_url = reverse("gallery:list")
        return HttpResponseRedirect(success_url)


class EditGalleryMembers(LoggedWithReadWriteHability, GalleryUpdateOrDeleteMixin, FormView):
    """Update gallery members"""

    form_class = UserGalleryForm
    http_method_names = ["post"]

    def dispatch(self, *args, **kwargs):
        try:
            self.get_gallery(pk=self.kwargs.get("pk"))
        except Gallery.DoesNotExist:
            raise Http404()

        if self.linked_content() is not None:
            raise PermissionDenied()

        return super().dispatch(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"gallery": self.gallery})
        return kwargs

    def form_invalid(self, form):
        messages.error(self.request, _("Impossible de mettre à jour la liste des utilisateurs"))
        return redirect(self.gallery.get_absolute_url())

    def form_valid(self, form):
        action = form.cleaned_data["action"]
        user = get_object_or_404(User, username=form.cleaned_data["user"])
        can_write = form.cleaned_data["mode"] == GALLERY_WRITE
        has_deleted = False

        modify_self = user.pk == self.request.user.pk

        if modify_self and action != "leave":
            raise PermissionDenied()
        elif not self.has_access_to_gallery(self.request.user, not modify_self):
            raise PermissionDenied()

        if action == "add":
            try:
                if user.pk not in self.users_and_permissions:
                    self.perform_add_user(user, can_write)
                else:
                    raise UserAlreadyInGallery()
            except UserAlreadyInGallery:
                messages.error(self.request, _("Impossible d'ajouter un utilisateur qui l'est déjà"))
        elif action == "edit":
            try:
                if user.pk in self.users_and_permissions:
                    self.perform_update_user(user, can_write)
                else:
                    raise UserNotInGallery()
            except UserNotInGallery:
                messages.error(self.request, _("Impossible de modifier un utilisateur non ajouté"))
        elif action == "leave":
            if user.pk in self.users_and_permissions:
                try:
                    has_deleted = self.perform_leave(user)
                    if has_deleted:
                        messages.info(self.request, _("La galerie a été supprimée par manque d'utilisateur"))
                    elif modify_self:
                        messages.info(self.request, _("Vous avez bien quitté la galerie"))
                except NoMoreUserWithWriteIfLeave:
                    modify_self = False
                    messages.error(
                        self.request,
                        _(
                            "Vous ne pouvez pas quitter la galerie, "
                            "car plus aucun autre utilisateur n'a les droits d'écriture"
                        ),
                    )
            else:
                messages.error(self.request, _("Impossible de supprimer un utilisateur non ajouté"))

        if not has_deleted and not modify_self:
            self.success_url = self.gallery.get_absolute_url()
        else:
            self.success_url = reverse("gallery:list")

        return super().form_valid(form)


class ImageFromGalleryViewMixin(GalleryMixin, View):
    """Mixin that ensure the access to the gallery and fill context data properly"""

    must_write = False  # if True, check for user write access

    def dispatch(self, request, *args, **kwargs):
        try:
            self.get_gallery(pk=self.kwargs.get("pk_gallery"))
        except Gallery.DoesNotExist:
            raise Http404()

        if not self.has_access_to_gallery(request.user, self.must_write):
            raise PermissionDenied()

        return super().dispatch(request, *args, **kwargs)


class ImageFromGalleryContextViewMixin(ImageFromGalleryViewMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["gallery"] = self.gallery
        context["permissions"] = self.users_and_permissions[self.request.user.pk]
        context["content_linked"] = self.linked_content()

        return context


class NewImage(ImageFromGalleryContextViewMixin, ImageCreateMixin, LoggedWithReadWriteHability, FormView):
    """Creates a new image."""

    form_class = ImageForm
    template_name = "gallery/image/new.html"
    must_write = True  # only allowed users can insert images

    def form_valid(self, form):
        try:
            self.perform_create(
                form.cleaned_data.get("title"), self.request.FILES.get("physical"), form.cleaned_data.get("legend")
            )
        except NotAnImage as e:
            messages.error(self.request, _(f"Le fichier « {e} » n'est pas une image valide."))
            form.add_error("physical", _("Image invalide"))
            return super().form_invalid(form)
        self.success_url = reverse("gallery:image-edit", kwargs={"pk_gallery": self.gallery.pk, "pk": self.image.pk})

        return super().form_valid(form)


class EditImage(ImageFromGalleryContextViewMixin, ImageUpdateOrDeleteMixin, LoggedWithReadWriteHability, FormView):
    """Edit or view an existing image."""

    form_class = UpdateImageForm
    template_name = "gallery/image/edit.html"

    def get(self, request, *args, **kwargs):
        try:
            self.get_image(self.kwargs.get("pk"))
        except Image.DoesNotExist:
            raise Http404

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not self.has_access_to_gallery(self.request.user, True):
            raise PermissionDenied()

        try:
            self.get_image(self.kwargs.get("pk"))
        except Image.DoesNotExist:
            raise Http404

        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["as_avatar_form"] = ImageAsAvatarForm()
        context["image"] = self.image
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"instance": self.image})
        return kwargs

    def form_valid(self, form):
        data = {}

        if "physical" in self.request.FILES:  # the user request to change the image
            data["physical"] = self.request.FILES.get("physical")

        data["title"] = form.cleaned_data.get("title")
        data["legend"] = form.cleaned_data.get("legend")

        try:
            self.perform_update(data)
        except NotAnImage as e:
            messages.error(self.request, _(f"Le fichier « {e} » n'est pas une image valide."))
            form.add_error("physical", _("Image invalide"))
            return super().form_invalid(form)

        self.success_url = reverse("gallery:image-edit", kwargs={"pk_gallery": self.gallery.pk, "pk": self.image.pk})

        return super().form_valid(form)


class DeleteImages(ImageFromGalleryViewMixin, ImageUpdateOrDeleteMixin, LoggedWithReadWriteHability, View):
    """Delete a given image"""

    model = Image
    http_method_names = ["post"]
    must_write = True

    def post(self, request, *args, **kwargs):
        if "delete_multi" in request.POST:
            list_items = request.POST.getlist("g_items")
            Image.objects.filter(pk__in=list_items, gallery=self.gallery).delete()
        elif "delete" in request.POST:
            try:
                self.get_image(request.POST.get("image"))
                self.perform_delete()
            except Image.DoesNotExist:
                raise Http404()
        return redirect(self.gallery.get_absolute_url())


class ImportImages(ImageFromGalleryContextViewMixin, ImageCreateMixin, LoggedWithReadWriteHability, FormView):
    """Create images from zip archive."""

    form_class = ArchiveImageForm
    template_name = "gallery/image/import.html"
    must_write = True  # only allowed user can import new images

    def form_valid(self, form):
        archive = self.request.FILES["file"]

        error_files = self.perform_create_multi(archive)

        if len(error_files) > 0:
            messages.error(
                self.request, _('Les fichiers suivants n\'ont pas été importés: "{}"').format('", "'.join(error_files))
            )

        self.success_url = self.gallery.get_absolute_url()
        return super().form_valid(form)
