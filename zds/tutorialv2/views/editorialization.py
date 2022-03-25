from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _

from zds.member.decorator import LoggedWithReadWriteHability, can_write_and_read_now
from zds.tutorialv2.forms import RemoveSuggestionForm, EditContentTagsForm
from zds.tutorialv2.mixins import SingleContentFormViewMixin
from zds.tutorialv2.models.database import ContentSuggestion, PublishableContent


class RemoveSuggestion(PermissionRequiredMixin, SingleContentFormViewMixin):
    form_class = RemoveSuggestionForm
    modal_form = True
    only_draft_version = True
    permission_required = "tutorialv2.change_publishablecontent"

    @method_decorator(login_required)
    @method_decorator(can_write_and_read_now)
    def dispatch(self, *args, **kwargs):
        if self.get_object().is_opinion:
            raise PermissionDenied
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        suggestion = ContentSuggestion.objects.get(pk=form.cleaned_data["pk_suggestion"])
        suggestion.delete()
        messages.success(self.request, self.get_success_message(suggestion))
        return super().form_valid(form)

    def form_invalid(self, form):
        form.previous_page_url = self.get_success_url()
        return super().form_invalid(form)

    def get_success_message(self, content_suggestion):
        return _('Vous avez enlevé "{}" de la liste des suggestions de {}.').format(
            content_suggestion.suggestion.title,
            self.describe_type(),
        )

    def get_success_url(self):
        if self.object.public_version:
            return self.object.get_absolute_url_online()
        else:
            return self.object.get_absolute_url()

    def describe_type(self):
        if self.object.is_tutorial:
            return _("ce tutoriel")
        return _("cet article")


class AddSuggestion(LoggedWithReadWriteHability, PermissionRequiredMixin, SingleContentFormViewMixin):
    only_draft_version = True
    authorized_for_staff = True
    permission_required = "tutorialv2.change_publishablecontent"

    def post(self, request, *args, **kwargs):
        publication = get_object_or_404(PublishableContent, pk=kwargs["pk"])

        _type = _("cet article")
        if publication.is_tutorial:
            _type = _("ce tutoriel")
        elif self.object.is_opinion:
            raise PermissionDenied

        if "options" in request.POST:
            options = request.POST.getlist("options")
            for option in options:
                suggestion = get_object_or_404(PublishableContent, pk=option)
                if ContentSuggestion.objects.filter(publication=publication, suggestion=suggestion).exists():
                    messages.error(
                        self.request,
                        _(f'Le contenu "{suggestion.title}" fait déjà partie des suggestions de {_type}'),
                    )
                elif suggestion.pk == publication.pk:
                    messages.error(
                        self.request,
                        _(f"Vous ne pouvez pas ajouter {_type} en tant que suggestion pour lui même."),
                    )
                elif suggestion.is_opinion and suggestion.sha_picked != suggestion.sha_public:
                    messages.error(
                        self.request,
                        _(f"Vous ne pouvez pas suggerer pour {_type} un billet qui n'a pas été mis en avant."),
                    )
                elif not suggestion.sha_public:
                    messages.error(
                        self.request,
                        _(f"Vous ne pouvez pas suggerer pour {_type} un contenu qui n'a pas été publié."),
                    )
                else:
                    obj_suggestion = ContentSuggestion(publication=publication, suggestion=suggestion)
                    obj_suggestion.save()
                    messages.info(
                        self.request,
                        _(f'Le contenu "{suggestion.title}" a été ajouté dans les suggestions de {_type}'),
                    )

        if self.object.public_version:
            return redirect(self.object.get_absolute_url_online())
        else:
            return redirect(self.object.get_absolute_url())


class EditContentTags(LoggedWithReadWriteHability, SingleContentFormViewMixin):
    modal_form = True
    model = PublishableContent
    form_class = EditContentTagsForm
    success_message = _("Les tags ont bien été modifiés.")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["content"] = self.versioned_object
        kwargs["db_content"] = self.object
        return kwargs

    def form_valid(self, form):
        self.object.tags.clear()
        self.object.add_tags(form.cleaned_data["tags"].split(","))
        self.object.save()
        messages.success(self.request, EditContentTags.success_message)
        return redirect(form.previous_page_url)
