from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, ButtonHolder
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Count
from django.forms import (
    forms,
    ModelMultipleChoiceField,
    CheckboxSelectMultiple,
)
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
        self.current_filter_pk = None

        self.base_queryset = PublishableContent.objects.exclude(public_version=None)
        self.num_all = self.base_queryset.count()

        queryset_not_classified = self.base_queryset.filter(labels=None)
        self.num_not_classified = queryset_not_classified.count()

        self.only_not_classified = "non-classes" in self.request.GET
        if self.only_not_classified:
            return queryset_not_classified
        else:
            for label in Label.objects.all():
                if f"label_{label.pk}" in self.request.GET:
                    self.current_filter_pk = label.pk
                    return self.base_queryset.filter(labels__in=[label])
        return self.base_queryset

    def get_context_data(self, **kwargs):
        context = {
            "labels": Label.objects.all().annotate(num_contents=Count("contents")),
            "current_filter_pk": self.current_filter_pk,
            "only_not_classified": self.only_not_classified,
            "all": self.current_filter_pk is None and not self.only_not_classified,
            "num_all": self.num_all,
            "num_not_classified": self.num_not_classified,
        }
        context.update(kwargs)
        return super().get_context_data(**context)


class ViewContentsByLabel(ContentsByLabelMixin, ZdSPagingListView):
    template_name = "tutorialv2/labels/view-labels.html"
    ordering = ["-creation_date"]
    paginate_by = settings.ZDS_APP["content"]["view_contents_by_label_content_per_page"]

    def get_context_data(self, **kwargs):
        if self.only_not_classified:
            headline = _("Publications sans label")
        elif self.current_filter_pk is not None:
            headline = _("Publications avec pour label « {} »").format(
                Label.objects.get(pk=self.current_filter_pk).name
            )
        else:
            headline = _("Toutes les publications")
        context = {"headline": headline}
        context.update(kwargs)
        return super().get_context_data(**context)
