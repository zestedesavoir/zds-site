from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import TemplateView

from zds.member.decorator import LoginRequiredMixin
from zds.tutorialv2.mixins import SingleContentDetailViewMixin, ModalFormView
from zds.tutorialv2.models import SHAREABLE_LINK_TYPES
from zds.tutorialv2.models.database import PublishableContent
from zds.tutorialv2.models.shareable_links import ShareableLink


class ListShareableLinks(LoginRequiredMixin, SingleContentDetailViewMixin, TemplateView):
    template_name = "tutorialv2/view/list_shareable_links.html"
    authorized_for_staff = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        content = self.get_object()
        context["active_links_and_forms"] = self.get_active_links_and_forms(content)
        context["expired_links_and_forms"] = self.get_expired_links_and_forms(content)
        context["inactive_links_and_forms"] = self.get_inactive_links_and_forms(content)
        context["create_form"] = ShareableLinkForm()
        return context

    def get_active_links_and_forms(self, content):
        return self.get_links_and_forms(ShareableLink.objects.active_and_for_content(content))

    def get_expired_links_and_forms(self, content):
        return self.get_links_and_forms(ShareableLink.objects.expired_and_for_content(content))

    def get_inactive_links_and_forms(self, content):
        return self.get_links_and_forms(ShareableLink.objects.inactive_and_for_content(content))

    @staticmethod
    def get_links_and_forms(links):
        edit_forms = [ShareableLinkForm(initial=initial) for initial in links.values()]
        return list(zip(links, edit_forms))


class ShareableLinkForm(forms.Form):
    description = forms.CharField(label=_("Description"), initial=_("Lien de partage"))
    expiration = forms.DateTimeField(
        label=_("Date d'expiration (laisser vide pour une durée illimitée)"),
        widget=forms.DateInput(attrs={"type": "date"}),
        required=False,
    )
    type = forms.ChoiceField(choices=SHAREABLE_LINK_TYPES)


class PermissionMixin:
    http_method_names = ["post"]

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        if self.request.user not in self.content.authors.all():
            raise PermissionDenied
        self.redirect_url = reverse("content:list-shareable-links", kwargs={"pk": self.content.pk})
        return super().dispatch(*args, *kwargs)


class ContentMixin(PermissionMixin):
    def dispatch(self, *args, **kwargs):
        self.content = get_object_or_404(PublishableContent, pk=self.kwargs["pk"])
        return super().dispatch(*args, *kwargs)


class LinkMixin(PermissionMixin):
    def dispatch(self, *args, **kwargs):
        self.link = get_object_or_404(ShareableLink, id=self.kwargs["id"])
        self.content = self.link.content
        return super().dispatch(*args, *kwargs)


class CreateShareableLink(ContentMixin, ModalFormView):
    http_method_names = ["post"]
    form_class = ShareableLinkForm
    modal_form = True

    def form_invalid(self, form):
        form.previous_page_url = self.redirect_url
        return super().form_invalid(form)

    def form_valid(self, form):
        ShareableLink(
            content=self.content,
            description=form.cleaned_data["description"],
            expiration=form.cleaned_data["expiration"],
            type=form.cleaned_data["type"],
        ).save()
        self.success_url = self.redirect_url
        messages.success(self.request, _("Le lien a été créé."))
        return super().form_valid(form)


class EditShareableLink(LinkMixin, ModalFormView):
    form_class = ShareableLinkForm
    modal_form = True

    def form_invalid(self, form):
        form.previous_page_url = self.redirect_url
        return super().form_invalid(form)

    def form_valid(self, form):
        self.link.description = form.cleaned_data["description"]
        self.link.expiration = form.cleaned_data["expiration"]
        self.link.type = form.cleaned_data["type"]
        self.link.save()
        self.success_url = self.redirect_url
        messages.success(self.request, "Le lien a été modifié.")
        return super().form_valid(form)


class DeactivateShareableLink(LinkMixin, View):
    def post(self, *args, **kwargs):
        self.link.deactivate()
        messages.success(self.request, "Le lien a été désactivé.")
        return redirect(self.redirect_url)


class ReactivateShareableLink(LinkMixin, View):
    def post(self, *args, **kwargs):
        self.link.reactivate()
        messages.success(self.request, "Le lien a été réactivé.")
        return redirect(self.redirect_url)


class DeleteShareableLink(LinkMixin, View):
    def post(self, *args, **kwargs):
        self.link.delete()
        messages.success(self.request, "Le lien a été supprimé.")
        return redirect(self.redirect_url)
