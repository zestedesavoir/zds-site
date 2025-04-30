from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import ButtonHolder, Field, Layout
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import ValidationError
from django.db.models import Count
from django.forms import (
    BooleanField,
    CheckboxSelectMultiple,
    HiddenInput,
    IntegerField,
    ModelMultipleChoiceField,
    forms,
)
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import BaseFormView

from zds.tutorialv2 import signals
from zds.tutorialv2.mixins import SingleContentFormViewMixin
from zds.tutorialv2.models.database import PublishableContent
from zds.tutorialv2.models.goals import Goal
from zds.utils import get_current_user
from zds.utils.paginator import ZdSPagingListView


class EditGoalsForm(forms.Form):
    goals = ModelMultipleChoiceField(
        label=_("Objectifs de la publication :"),
        queryset=Goal.objects.all(),
        required=False,
        widget=CheckboxSelectMultiple,
    )

    def __init__(self, content, *args, **kwargs):
        kwargs["initial"] = {"goals": content.goals.all()}
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_class = "content-wrapper"
        self.helper.form_method = "post"
        self.helper.form_id = "edit-goals"
        self.helper.form_class = "modal modal-flex"
        self.helper.form_action = reverse("content:edit-goals", kwargs={"pk": content.pk})
        self.helper.layout = Layout(
            Field("goals"),
            ButtonHolder(StrictButton("Valider", type="submit")),
        )


class EditGoals(LoginRequiredMixin, PermissionRequiredMixin, SingleContentFormViewMixin):
    """View managing the form used to modify the goals of a single content."""

    permission_required = "tutorialv2.change_publishablecontent"
    model = PublishableContent
    form_class = EditGoalsForm
    success_message = _("Les objectifs ont bien été modifiés.")
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
        self.object.goals.clear()
        new_goals = Goal.objects.filter(id__in=form.cleaned_data["goals"])
        self.object.goals.add(*new_goals)
        messages.success(self.request, self.success_message)
        signals.goals_management.send(sender=self.__class__, performer=get_current_user(), content=self.object)
        return super().form_valid(form)


class MassEditGoalsForm(forms.Form):
    """Form for requests sent with the page for mass edit of goals."""

    activated = BooleanField(widget=HiddenInput, required=False)
    goal_id = IntegerField(widget=HiddenInput)
    content_id = IntegerField(widget=HiddenInput)

    def clean_goal_id(self):
        goal_id = self.cleaned_data["goal_id"]
        if not Goal.objects.filter(id=goal_id).exists():
            raise ValidationError(f"The goal with id {goal_id} does not exist.")
        return goal_id

    def clean_content_id(self):
        content_id = self.cleaned_data["content_id"]
        if not PublishableContent.objects.filter(id=content_id).exists():
            raise ValidationError(f"The content with id {content_id} does not exist.")
        return content_id


class ContentsByGoalMixin:
    context_object_name = "contents"

    def get_queryset(self):
        self.current_filter_pk = None

        self.base_queryset = PublishableContent.objects.exclude(public_version=None).prefetch_related("goals")
        self.num_all = self.base_queryset.count()

        queryset_not_classified = self.base_queryset.filter(goals=None)
        self.num_not_classified = queryset_not_classified.count()

        self.only_not_classified = Goal.SLUG_UNCLASSIFIED in self.request.GET
        if self.only_not_classified:
            return queryset_not_classified
        elif len(self.request.GET) > 0:
            slug = list(self.request.GET.keys())[0]
            goal = Goal.objects.filter(slug=slug).first()
            if goal is not None:
                self.current_filter_pk = goal.pk
                return self.base_queryset.filter(goals__in=[goal])
        return self.base_queryset

    def get_context_data(self, **kwargs):
        context = {
            "goals": Goal.objects.all().annotate(num_contents=Count("contents")),
            "current_filter_pk": self.current_filter_pk,
            "only_not_classified": self.only_not_classified,
            "all": self.current_filter_pk is None and not self.only_not_classified,
            "num_all": self.num_all,
            "num_not_classified": self.num_not_classified,
        }
        context.update(kwargs)
        return super().get_context_data(**context)


class MassEditGoals(LoginRequiredMixin, PermissionRequiredMixin, BaseFormView, ContentsByGoalMixin, ZdSPagingListView):
    """View to edit the goals of many contents."""

    template_name = "tutorialv2/goals/mass-edit-goals.html"
    permission_required = "tutorialv2.change_publishablecontent"
    form_class = MassEditGoalsForm
    ordering = ["-creation_date"]
    paginate_by = settings.ZDS_APP["content"]["mass_edit_goals_content_per_page"]

    def get_context_data(self, **kwargs):
        context = {
            "url_not_classified": reverse("content:mass-edit-goals") + "?" + Goal.SLUG_UNCLASSIFIED,
        }
        context.update(kwargs)
        return super().get_context_data(**context)

    def form_valid(self, form):
        content = PublishableContent.objects.get(id=form.cleaned_data["content_id"])
        goal = Goal.objects.get(id=form.cleaned_data["goal_id"])
        activated = form.cleaned_data["activated"]
        if activated:
            content.goals.add(goal)
        else:
            content.goals.remove(goal)
        return JsonResponse({"state": activated})

    def form_invalid(self, form):
        return JsonResponse({"errors": form.errors}, status=400)


class ViewContentsByGoal(ContentsByGoalMixin, ZdSPagingListView):
    template_name = "tutorialv2/goals/view-goals.html"
    ordering = ["-creation_date"]
    paginate_by = settings.ZDS_APP["content"]["view_contents_by_goal_content_per_page"]

    def get_context_data(self, **kwargs):
        if self.only_not_classified:
            headline = _("Publications sans objectif")
        elif self.current_filter_pk is not None:
            headline = _("Publications avec pour objectif « {} »").format(
                Goal.objects.get(pk=self.current_filter_pk).name
            )
        else:
            headline = _("Toutes les publications")
        context = {
            "headline": headline,
            "url_not_classified": reverse("content:view-goals") + "?" + Goal.SLUG_UNCLASSIFIED,
        }
        context.update(kwargs)
        return super().get_context_data(**context)
