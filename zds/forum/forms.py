from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Field, Hidden, Layout
from django import forms
from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from zds.forum.models import Forum, Topic
from zds.utils.forms import CommonLayoutEditor, FieldValidatorMixin, TagValidator


class TopicForm(forms.Form, FieldValidatorMixin):
    title = forms.CharField(
        label=_("Titre"),
        max_length=Topic._meta.get_field("title").max_length,
        widget=forms.TextInput(attrs={"placeholder": _("Titre de mon sujet"), "required": "required"}),
    )

    subtitle = forms.CharField(
        label=_("Sous-titre"),
        max_length=Topic._meta.get_field("subtitle").max_length,
        required=False,
    )

    tags = forms.CharField(
        label=_("Tag(s) séparés par une virgule (exemple: python,django,web)"),
        max_length=64,
        required=False,
        widget=forms.TextInput(),
    )

    text = forms.CharField(
        label="Texte",
        widget=forms.Textarea(
            attrs={
                "placeholder": _("Votre message au format Markdown."),
                "required": "required",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["tags"].widget.attrs.update(
            {
                "data-autocomplete": '{ "type": "multiple", "fieldname": "title", "url": "'
                + reverse("api:utils:tags-list")
                + '?search=%s" }'
            }
        )

        self.helper = FormHelper()
        self.helper.form_class = "content-wrapper"
        self.helper.form_method = "post"

        self.helper.layout = Layout(
            Field("title"),
            Field("subtitle", autocomplete="off"),
            Field("tags"),
            HTML(
                """<div id="topic-suggest" style="display:none;"  url="{}">
  <label>{}</label>
  <div id="topic-result-container" data-neither="{}"></div>
</div>""".format(
                    reverse("search:similar"), _("Sujets similaires au vôtre :"), _("Aucun résultat")
                )
            ),
            CommonLayoutEditor(),
        )

        if "text" in self.initial:
            self.helper.layout.append(HTML("{% include 'misc/hat_choice.html' with edited_message=topic.first_post %}"))
        else:
            self.helper.layout.append(HTML("{% include 'misc/hat_choice.html' %}"))

    def clean(self):
        cleaned_data = super().clean()

        self.get_non_empty_field_or_error(cleaned_data, "title", lambda: _("Le champ titre ne peut être vide"))
        text = self.get_non_empty_field_or_error(cleaned_data, "text", lambda: _("Le champ text ne peut être vide"))

        if text:
            self.check_text_length_limit(
                text,
                settings.ZDS_APP["forum"]["max_post_length"],
                lambda: _("Ce message est trop long, " "il ne doit pas dépasser {0} caractères"),
            )

        tags = cleaned_data.get("tags")
        validator = TagValidator()
        if not validator.validate_raw_string(tags):
            self._errors["tags"] = self.error_class(validator.errors)
        return cleaned_data


class PostForm(forms.Form, FieldValidatorMixin):
    text = forms.CharField(
        label="",
        widget=forms.Textarea(
            attrs={
                "placeholder": _("Votre message au format Markdown."),
                "required": "required",
            }
        ),
    )

    def __init__(self, topic, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"

        self.helper.layout = Layout(
            CommonLayoutEditor(),
            Hidden("last_post", "{{ last_post_pk }}"),
        )

        if "text" in self.initial:
            self.helper.layout.append(HTML("{% include 'misc/hat_choice.html' with edited_message=post %}"))
        else:
            self.helper.layout.append(HTML("{% include 'misc/hat_choice.html' %}"))

        if topic.antispam(user):
            if "text" not in self.initial:
                self.helper["text"].wrap(
                    Field,
                    placeholder=_(
                        "Vous venez de poster. Merci de patienter "
                        "au moins 15 minutes entre deux messages consécutifs "
                        "afin de limiter le flood."
                    ),
                    disabled=True,
                )
        elif topic.is_locked:
            if "text" not in self.initial:
                self.helper["text"].wrap(Field, placeholder=_("Ce topic est verrouillé."), disabled=True)

    def clean(self):
        cleaned_data = super().clean()

        text = self.get_non_empty_field_or_error(cleaned_data, "text", lambda: _("Vous devez écrire une réponse !"))

        if text:
            self.check_text_length_limit(
                text,
                settings.ZDS_APP["forum"]["max_post_length"],
                lambda: _("Ce message est trop long, " "il ne doit pas dépasser {0} caractères"),
            )
        return cleaned_data


class MoveTopicForm(forms.Form):
    forum = forms.ModelChoiceField(
        label=_("Forum"),
        queryset=Forum.objects.all(),
        required=True,
    )

    def __init__(self, topic, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse("forum:topic-edit")
        self.helper.form_class = "modal modal-flex"
        self.helper.form_id = "move-topic"
        self.helper.form_method = "post"

        self.helper.layout = Layout(
            Field("forum"),
            Hidden("move", ""),
            Hidden("topic", topic.pk),
            StrictButton(_("Valider"), type="submit", css_class="btn-submit"),
        )
