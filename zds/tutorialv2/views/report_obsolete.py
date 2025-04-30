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
        queryset = PotentialObsolete.objects.all().select_related("publishable_content")

        # filtering by type
        try:
            type_ = self.request.GET["type"]
            if type_ == "unprocessed":
                queryset = queryset.filter(status="nouveau")
            if type_ == "processed":
                queryset = queryset.filter(status="traite")
            if type_ == "ignored":
                queryset = queryset.filter(status="ignore")
            if type_ == "article":
                queryset = queryset.filter(publishable_content__type="ARTICLE")
            if type_ == "tuto":
                queryset = queryset.filter(publishable_content__type="TUTORIAL")
            else:
                raise KeyError()
        except KeyError:
            pass

        # filtering by category
        try:
            category_pk = int(self.request.GET["subcategory"])
            self.subcategory = get_object_or_404(SubCategory, pk=category_pk)
            queryset = queryset.filter(publishable_content__subcategory__in=[self.subcategory])
        except KeyError:
            pass
        except ValueError:
            raise Http404("Format invalide pour le paramètre de la sous-catégorie.")

        return queryset.order_by(self.ordering).all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["forms_decide_obsolete"] = {report.pk: DecideObsoleteForm(obj=report) for report in context["reports"]}
        context["category"] = self.subcategory
        return context
