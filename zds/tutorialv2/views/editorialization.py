from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext_lazy as _

from zds.member.decorator import LoggedWithReadWriteHability
from zds.tutorialv2.forms import RemoveSuggestionForm, EditContentTagsForm
from zds.tutorialv2.mixins import SingleContentFormViewMixin
from zds.tutorialv2.models.database import ContentSuggestion, PublishableContent


class RemoveSuggestion(LoggedWithReadWriteHability, SingleContentFormViewMixin):

    form_class = RemoveSuggestionForm
    only_draft_version = True
    authorized_for_staff = True

    def form_valid(self, form):
        _type = _("cet article")
        if self.object.is_tutorial:
            _type = _("ce tutoriel")
        elif self.object.is_opinion:
            raise PermissionDenied

        content_suggestion = get_object_or_404(ContentSuggestion, pk=form.cleaned_data["pk_suggestion"])
        content_suggestion.delete()

        messages.success(
            self.request,
            _('Vous avez enlevé "{}" de la liste des suggestions de {}.').format(
                content_suggestion.suggestion.title, _type
            ),
        )

        if self.object.public_version:
            self.success_url = self.object.get_absolute_url_online()
        else:
            self.success_url = self.object.get_absolute_url()

        return super(RemoveSuggestion, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, str(_("Les suggestions sélectionnées n'existent pas.")))
        if self.object.public_version:
            self.success_url = self.object.get_absolute_url_online()
        else:
            self.success_url = self.object.get_absolute_url()
        return super(RemoveSuggestion, self).form_valid(form)


class AddSuggestion(LoggedWithReadWriteHability, SingleContentFormViewMixin):
    only_draft_version = True
    authorized_for_staff = True

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
                        _('Le contenu "{}" fait déjà partie des suggestions de {}'.format(suggestion.title, _type)),
                    )
                elif suggestion.pk == publication.pk:
                    messages.error(
                        self.request,
                        _("Vous ne pouvez pas ajouter {} en tant que suggestion pour lui même.".format(_type)),
                    )
                elif suggestion.is_opinion and suggestion.sha_picked != suggestion.sha_public:
                    messages.error(
                        self.request,
                        _("Vous ne pouvez pas suggerer pour {} un billet qui n'a pas été mis en avant.".format(_type)),
                    )
                elif not suggestion.sha_public:
                    messages.error(
                        self.request,
                        _("Vous ne pouvez pas suggerer pour {} un contenu qui n'a pas été publié.".format(_type)),
                    )
                else:
                    obj_suggestion = ContentSuggestion(publication=publication, suggestion=suggestion)
                    obj_suggestion.save()
                    messages.info(
                        self.request,
                        _('Le contenu "{}" a été ajouté dans les suggestions de {}'.format(suggestion.title, _type)),
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
        kwargs = super(EditContentTags, self).get_form_kwargs()
        kwargs["content"] = self.versioned_object
        kwargs["db_content"] = self.object
        return kwargs

    def form_valid(self, form):
        self.object.tags.clear()
        self.object.add_tags(form.cleaned_data["tags"].split(","))
        self.object.save(force_slug_update=False)
        messages.success(self.request, EditContentTags.success_message)
        return redirect(form.previous_page_url)
