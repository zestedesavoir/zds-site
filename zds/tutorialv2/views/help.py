import json

from django import forms
from django.conf import settings
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.utils.translation import gettext_lazy as _

from zds.member.decorator import LoggedWithReadWriteHability
from zds.tutorialv2 import signals
from zds.tutorialv2.mixins import SingleContentFormViewMixin
from zds.tutorialv2.models.database import PublishableContent
from zds.tutorialv2.models.help_requests import HelpWriting
from zds.utils.misc import is_ajax
from zds.utils.paginator import ZdSPagingListView


class ToggleHelpForm(forms.Form):
    help_wanted = forms.CharField()
    activated = forms.BooleanField(required=False)

    def clean(self):
        clean_data = super().clean()
        clean_data["help_wanted"] = HelpWriting.objects.filter(title=(self.data["help_wanted"] or "").strip()).first()
        if not clean_data["help_wanted"]:
            self.add_error("help_wanted", _("Inconnu"))
        return clean_data


class ContentsWithHelps(ZdSPagingListView):
    """List all tutorial that needs help, i.e registered as needing at least one HelpWriting or is in beta
    for more documentation, have a look to ZEP 03 specification (fr)"""

    context_object_name = "contents"
    template_name = "tutorialv2/view/help.html"
    paginate_by = settings.ZDS_APP["content"]["helps_per_page"]

    specific_need = None

    def get_queryset(self):
        """get only tutorial that need help and handle filtering if asked"""
        query_set = (
            PublishableContent.objects.annotate(total=Count("helps"), shasize=Count("sha_beta"))
            .filter((Q(sha_beta__isnull=False) & Q(shasize__gt=0)) | Q(total__gt=0))
            .order_by("-update_date")
            .all()
        )
        if "need" in self.request.GET:
            self.specific_need = self.request.GET.get("need")
            if self.specific_need != "":
                query_set = query_set.filter(helps__slug__in=[self.specific_need])
        if "type" in self.request.GET:
            filter_type = None
            if self.request.GET["type"] == "article":
                filter_type = "ARTICLE"
            elif self.request.GET["type"] == "tuto":
                filter_type = "TUTORIAL"
            if filter_type:
                query_set = query_set.filter(type=filter_type)
        return query_set

    def get_context_data(self, **kwargs):
        """Add all HelpWriting objects registered to the context so that the template can use it"""
        context = super().get_context_data(**kwargs)
        queryset = kwargs.pop("object_list", self.object_list)

        helps = HelpWriting.objects

        if self.specific_need:
            context["specific_need"] = helps.filter(slug=self.specific_need).first()

        context["helps"] = list(helps.all())
        context["total_contents_number"] = queryset.count()
        return context


class ChangeHelp(LoggedWithReadWriteHability, SingleContentFormViewMixin):
    form_class = ToggleHelpForm

    def form_valid(self, form):
        """
        change help needing state, assume this is ajax request
        :param form: the data
        :return: json answer
        """
        if self.object.is_opinion:
            return HttpResponse(
                json.dumps({"errors": str(_("Impossible de demander de l'aide pour un billet"))}),
                status=400,
                content_type="application/json",
            )
        data = form.cleaned_data
        if data["activated"]:
            self.object.helps.add(data["help_wanted"])
        else:
            self.object.helps.remove(data["help_wanted"])
        self.object.save()
        signals.help_management.send(sender=self.__class__, performer=self.request.user, content=self.object)
        if is_ajax(self.request):
            return JsonResponse({"state": data["activated"]})
        self.success_url = self.object.get_absolute_url()
        return super().form_valid(form)

    def form_invalid(self, form):
        if is_ajax(self.request):
            return JsonResponse({"errors": form.errors}, status=400)
        return super().form_invalid(form)
