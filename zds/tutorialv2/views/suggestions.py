from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Layout
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _

import zds.tutorialv2.signals as signals
from zds.member.decorator import LoggedWithReadWriteHability, can_write_and_read_now
from zds.tutorialv2.mixins import SingleContentFormViewMixin
from zds.tutorialv2.models.database import ContentSuggestion, PublishableContent


class SearchSuggestionForm(forms.Form):
    suggestion_pk = forms.CharField(
        label="Publication à suggérer",
        required=False,
        widget=forms.TextInput(),
    )
    excluded_pk = forms.CharField(required=False, widget=forms.HiddenInput(attrs={"class": "excluded_field"}))

    def __init__(self, content, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["suggestion_pk"].widget.attrs.update(
            {
                "data-autocomplete": '{"type": "multiple_checkbox",'
                '"limit": 10,'
                '"fieldname": "title",'
                '"url": "' + reverse("search:suggestion") + '?q=%s&excluded=%e"}',
                "placeholder": "Rechercher un contenu",
            }
        )

        self.helper = FormHelper()
        self.helper.form_action = reverse("content:add-suggestion", kwargs={"pk": content.pk})
        self.helper.form_class = "modal modal-large"
        self.helper.form_id = "add-suggestion"
        self.helper.form_method = "post"

        self.helper.layout = Layout(
            Field("suggestion_pk"), Field("excluded_pk"), StrictButton(_("Ajouter"), type="submit")
        )


class RemoveSuggestionForm(forms.Form):
    pk_suggestion = forms.IntegerField(
        label=_("Suggestion"),
        required=True,
        error_messages={"does_not_exist": _("La suggestion sélectionnée n'existe pas.")},
    )

    def clean_pk_suggestion(self):
        pk_suggestion = self.cleaned_data.get("pk_suggestion")
        suggestion = ContentSuggestion.objects.filter(id=pk_suggestion).first()
        if suggestion is None:
            self.add_error("pk_suggestion", self.fields["pk_suggestion"].error_messages["does_not_exist"])
        return pk_suggestion


class RemoveSuggestionView(PermissionRequiredMixin, SingleContentFormViewMixin):
    form_class = RemoveSuggestionForm
    modal_form = True
    permission_required = "tutorialv2.change_publishablecontent"

    @method_decorator(login_required)
    @method_decorator(can_write_and_read_now)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        suggestion = ContentSuggestion.objects.get(pk=form.cleaned_data["pk_suggestion"])
        suggestion.delete()
        signals.suggestions_management.send(
            sender=self.__class__, performer=self.request.user, content=self.object, action="remove"
        )
        messages.success(self.request, self.get_success_message(suggestion))
        return super().form_valid(form)

    def form_invalid(self, form):
        form.previous_page_url = self.get_success_url()
        return super().form_invalid(form)

    def get_success_message(self, content_suggestion):
        return _('Vous avez enlevé "{}" de la liste des suggestions de cette publication.').format(
            content_suggestion.suggestion.title
        )

    def get_success_url(self):
        if self.object.public_version:
            return self.object.get_absolute_url_online()
        else:
            return self.object.get_absolute_url()


class AddSuggestionView(LoggedWithReadWriteHability, PermissionRequiredMixin, SingleContentFormViewMixin):
    authorized_for_staff = True
    permission_required = "tutorialv2.change_publishablecontent"

    def post(self, request, *args, **kwargs):
        publication = get_object_or_404(PublishableContent, pk=kwargs["pk"])

        if "options" in request.POST:
            options = request.POST.getlist("options")
            for option in options:
                suggestion = get_object_or_404(PublishableContent, pk=option)
                if ContentSuggestion.objects.filter(publication=publication, suggestion=suggestion).exists():
                    messages.error(
                        self.request,
                        _(f'"{suggestion.title}" est déjà suggéré pour cette publication.'),
                    )
                elif suggestion.pk == publication.pk:
                    messages.error(
                        self.request,
                        _(f"Vous ne pouvez pas suggérer la publication pour elle-même."),
                    )
                elif suggestion.is_opinion and suggestion.sha_picked != suggestion.sha_public:
                    messages.error(
                        self.request,
                        _(f"Vous ne pouvez pas suggérer un billet qui n'a pas été mis en avant."),
                    )
                elif not suggestion.sha_public:
                    messages.error(
                        self.request,
                        _(f"Vous ne pouvez pas suggérer une publication non publique."),
                    )
                else:
                    obj_suggestion = ContentSuggestion(publication=publication, suggestion=suggestion)
                    obj_suggestion.save()
                    signals.suggestions_management.send(
                        sender=self.__class__,
                        performer=self.request.user,
                        content=self.object,
                        action="add",
                    )
                    messages.info(
                        self.request,
                        _(f'"{suggestion.title}" a été ajouté aux suggestions de la publication.'),
                    )

        if self.object.public_version:
            return redirect(self.object.get_absolute_url_online())
        else:
            return redirect(self.object.get_absolute_url())
