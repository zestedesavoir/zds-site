from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.generic import ListView

from zds.tutorialv2.forms import DecideObsoleteForm
from zds.tutorialv2.models.database import PotentialObsolete
from zds.utils.models import SubCategory


class PotentialObsoleteContentListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """List the obsolete reports, with possibilities of filters"""

    permission_required = "tutorialv2.change_publishablecontent"
    template_name = "tutorialv2/list_page_elements/potentialobsolete_list.html"
    context_object_name = "reports"
    ordering = "-report_date"
    subcategory = None

    def get_queryset(self):
        queryset = (
            PotentialObsolete.objects.all()
            .prefetch_related("publishable_content")
            .prefetch_related("publishable_content__authors")
            .prefetch_related("publishable_content__subcategory")
            .prefetch_related("publishable_content__authors")
            .prefetch_related("author")
        )

        # filtering by type
        try:
            type_ = self.request.GET["type"]
            if type_ == "unprocessed":
                queryset = queryset.filter(status="nouveau")
            elif type_ == "processed":
                queryset = queryset.filter(status="traite")
            elif type_ == "ignored":
                queryset = queryset.filter(status="ignore")
            elif type_ == "article":
                queryset = queryset.filter(publishable_content__type="ARTICLE")
            elif type_ == "tuto":
                queryset = queryset.filter(publishable_content__type="TUTORIAL")
            elif type_ == "opinion":
                queryset = queryset.filter(publishable_content__type="OPINION")
            else:
                raise Http404("Type de filtre invalide.")
        except KeyError:
            pass

        # filtering by category
        category_pk = self.request.GET.get("subcategory")
        if category_pk is not None:
            try:
                _category_pk = int(category_pk)
                self.subcategory = get_object_or_404(SubCategory, pk=_category_pk)
                queryset = queryset.filter(publishable_content__subcategory__in=[self.subcategory])
            except ValueError:
                raise Http404("Format invalide pour le paramètre de la sous-catégorie.")

        return queryset.order_by(self.ordering).all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["forms_decide_obsolete"] = {report.pk: DecideObsoleteForm(obj=report) for report in context["reports"]}
        context["category"] = self.subcategory
        return context
