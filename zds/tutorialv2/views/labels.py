from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import ButtonHolder, Field, Layout
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Count
from django.forms import CheckboxSelectMultiple, ModelMultipleChoiceField, forms
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from zds.tutorialv2 import signals
from zds.tutorialv2.mixins import SingleContentFormViewMixin
from zds.tutorialv2.models.database import PublishableContent
from zds.tutorialv2.models.labels import Label
from zds.utils import get_current_user
from zds.utils.paginator import ZdSPagingListView


class EditLabelsForm(forms.Form):
    labels = ModelMultipleChoiceField(
        label=_("Labels de la publication :"),
        queryset=Label.objects.all(),
        required=False,
        widget=CheckboxSelectMultiple,
    )

    def __init__(self, content, *args, **kwargs):
        kwargs["initial"] = {"labels": content.labels.all()}
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_class = "content-wrapper"
        self.helper.form_method = "post"
        self.helper.form_id = "edit-labels"
        self.helper.form_class = "modal modal-flex"
        self.helper.form_action = reverse("content:edit-labels", kwargs={"pk": content.pk})
        self.helper.layout = Layout(
            Field("labels"),
            ButtonHolder(StrictButton("Valider", type="submit")),
        )


class EditLabels(LoginRequiredMixin, PermissionRequiredMixin, SingleContentFormViewMixin):
    """View managing the form used to modify the labels of a single content."""

    permission_required = "tutorialv2.change_publishablecontent"
    model = PublishableContent
    form_class = EditLabelsForm
    success_message = _("Les labels ont bien été modifiés.")
    modal_form = True
    http_method_names = ["post"]

    def dispatch(self, request, *args, **kwargs):
        content = get_object_or_404(PublishableContent, pk=self.kwargs["pk"])
        success_url_kwargs = {"pk": content.pk, "slug": content.slug}
        self.success_url = reverse("content:view", kwargs=success_url_kwargs)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["content"] = self.object
        return kwargs

    def form_invalid(self, form):
        form.previous_page_url = self.success_url
        return super().form_invalid(form)

    def form_valid(self, form):
        self.object.labels.clear()
        new_labels = Label.objects.filter(id__in=form.cleaned_data["labels"])
        self.object.labels.add(*new_labels)
        messages.success(self.request, self.success_message)
        signals.labels_management.send(sender=self.__class__, performer=get_current_user(), content=self.object)
        return super().form_valid(form)


class ContentsByLabelMixin:
    context_object_name = "contents"

    def get_queryset(self):
        self.current_label = get_object_or_404(Label, slug=self.kwargs["slug"])
        self.base_queryset = PublishableContent.objects.exclude(public_version=None)
        return self.base_queryset.filter(labels__in=[self.current_label])

    def get_context_data(self, **kwargs):
        context = {
            "labels": Label.objects.all().annotate(num_contents=Count("contents")),
            "current_description": self.current_label.description,
            "current_filter_pk": self.current_label.pk,
        }
        context.update(kwargs)
        return super().get_context_data(**context)


class ViewContentsByLabel(ContentsByLabelMixin, ZdSPagingListView):
    template_name = "tutorialv2/labels/view_labels.html"
    ordering = ["-creation_date"]
    paginate_by = settings.ZDS_APP["content"]["view_contents_by_label_content_per_page"]

    def get_context_data(self, **kwargs):
        headline = _("Publications avec pour label « {} »").format(self.current_label.name)
        context = {"headline": headline}
        context.update(kwargs)
        return super().get_context_data(**context)
