from datetime import datetime

from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Layout
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import FileField, forms
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from zds.gallery.mixins import ImageCreateMixin, NotAnImage
from zds.gallery.models import Gallery
from zds.tutorialv2 import signals
from zds.tutorialv2.mixins import SingleContentFormViewMixin
from zds.tutorialv2.models.database import PublishableContent
from zds.utils import get_current_user
from zds.utils.uuslug_wrapper import slugify
from zds.utils.validators import with_svg_validator


class EditThumbnailForm(forms.Form):
    image = FileField(
        label=_("Sélectionnez la miniature de la publication (max. {} ko).").format(
            settings.ZDS_APP["gallery"]["image_max_size"] // 1024
        ),
        validators=[with_svg_validator],
        required=True,
        error_messages={
            "file_too_large": _("La miniature est trop lourde ; la limite autorisée est de {} ko").format(
                settings.ZDS_APP["gallery"]["image_max_size"] // 1024
            ),
        },
    )

    def __init__(self, versioned_content, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_action = reverse("content:edit-thumbnail", kwargs={"pk": versioned_content.pk})
        self.helper.form_id = "edit-thumbnail"
        self.helper.form_class = "modal modal-flex"

        self.helper.layout = Layout(
            Field("image"),
            StrictButton("Valider", type="submit"),
        )

        self.previous_page_url = reverse(
            "content:view", kwargs={"pk": versioned_content.pk, "slug": versioned_content.slug}
        )

    def clean_image(self):
        image = self.cleaned_data.get("image", None)
        if image is not None and image.size > settings.ZDS_APP["gallery"]["image_max_size"]:
            self.add_error("image", self.declared_fields["image"].error_messages["file_too_large"])
        return self.cleaned_data


class EditThumbnailView(LoginRequiredMixin, SingleContentFormViewMixin):
    modal_form = True
    model = PublishableContent
    form_class = EditThumbnailForm
    success_message = _("La miniature a bien été changée.")
    error_messages = {"invalid_image": _("Image invalide")}

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["versioned_content"] = self.versioned_object
        return kwargs

    def form_valid(self, form):
        publishable = self.object

        # Get or create gallery
        gallery_defaults = {
            "title": publishable.title,
            "slug": slugify(publishable.title),
            "pubdate": datetime.now(),
        }
        gallery, _created = Gallery.objects.get_or_create(pk=publishable.gallery.pk, defaults=gallery_defaults)
        publishable.gallery = gallery

        # Create image
        mixin = ImageCreateMixin()
        mixin.gallery = gallery
        try:
            thumbnail = mixin.perform_create(str(_("Icône du contenu")), self.request.FILES["image"])
        except NotAnImage:
            form.add_error("image", self.error_messages["invalid_image"])
            return super().form_invalid(form)
        thumbnail.pubdate = datetime.now()

        # Update thumbnail
        publishable.image = thumbnail
        publishable.save()

        messages.success(self.request, self.success_message)

        signals.thumbnail_management.send(sender=self.__class__, performer=get_current_user(), content=publishable)

        return redirect(form.previous_page_url)
