from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, ButtonHolder, Field, Hidden, Layout, Submit
from django import forms
from django.conf import settings
from django.core.validators import MinLengthValidator
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from zds.tutorialv2.models import TYPE_CHOICES
from zds.tutorialv2.models.database import PublishableContent
from zds.tutorialv2.utils import get_content_version_url
from zds.utils.forms import CommonLayoutEditor, CommonLayoutVersionEditor, IncludeEasyMDE
from zds.utils.models import SubCategory
from zds.utils.validators import InvalidSlugError, slugify_raise_on_invalid


class FormWithTitle(forms.Form):
    title = forms.CharField(
        label=_("Titre"), max_length=PublishableContent._meta.get_field("title").max_length, required=False
    )

    error_messages = {"bad_slug": _("Le titre « {} » n'est pas autorisé, car son slug est invalide !")}

    def clean(self):
        cleaned_data = super().clean()

        title = cleaned_data.get("title")

        if title is None or not title.strip():
            title = "Titre par défaut"
            cleaned_data["title"] = title

        try:
            slugify_raise_on_invalid(title)
        except InvalidSlugError:
            self._errors["title"] = self.error_class([self.error_messages["bad_slug"].format(title)])

        return cleaned_data


class ReviewerTypeModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.title


class ContainerForm(FormWithTitle):
    introduction = forms.CharField(
        label=_("Introduction"),
        required=False,
        widget=forms.Textarea(
            attrs={"placeholder": _("Votre introduction, au format Markdown."), "class": "md-editor preview-source"}
        ),
    )

    conclusion = forms.CharField(
        label=_("Conclusion"),
        required=False,
        widget=forms.Textarea(
            attrs={
                "placeholder": _("Votre conclusion, au format Markdown."),
            }
        ),
    )

    msg_commit = forms.CharField(
        label=_("Message de suivi"),
        max_length=400,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": _("Un résumé de vos ajouts et modifications.")}),
    )

    last_hash = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = "content-wrapper"
        self.helper.form_method = "post"

        self.helper.layout = Layout(
            IncludeEasyMDE(),
            Field("title"),
            Field("introduction", css_class="md-editor preview-source"),
            ButtonHolder(
                StrictButton(_("Aperçu"), type="preview", name="preview", css_class="btn btn-grey preview-btn"),
            ),
            HTML(
                '{% if form.introduction.value %}{% include "misc/preview.part.html" \
            with text=form.introduction.value %}{% endif %}'
            ),
            Field("conclusion", css_class="md-editor preview-source"),
            ButtonHolder(
                StrictButton(_("Aperçu"), type="preview", name="preview", css_class="btn btn-grey preview-btn"),
            ),
            HTML(
                '{% if form.conclusion.value %}{% include "misc/preview.part.html" \
            with text=form.conclusion.value %}{% endif %}'
            ),
            Field("msg_commit"),
            Field("last_hash"),
            ButtonHolder(
                StrictButton(_("Valider"), type="submit"),
            ),
        )


class ContentForm(ContainerForm):
    type = forms.ChoiceField(choices=TYPE_CHOICES, required=True)

    def _create_layout(self):
        self.helper.layout = Layout(
            IncludeEasyMDE(),
            Field("title"),
            Field("type"),
            StrictButton("Valider", type="submit"),
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_class = "content-wrapper"
        self.helper.form_method = "post"
        self._create_layout()

        if "type" in self.initial:
            self.helper["type"].wrap(Field, disabled=True)


class ExtractForm(FormWithTitle):
    text = forms.CharField(
        label=_("Texte"),
        required=False,
        widget=forms.Textarea(attrs={"placeholder": _("Votre message, au format Markdown.")}),
    )

    msg_commit = forms.CharField(
        label=_("Message de suivi"),
        max_length=400,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": _("Un résumé de vos ajouts et modifications.")}),
    )

    last_hash = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = "content-wrapper"
        self.helper.form_method = "post"
        display_save = bool(self.initial.get("last_hash", False))
        self.helper.layout = Layout(
            Field("title"),
            Field("last_hash"),
            CommonLayoutVersionEditor(
                display_save=display_save, send_label="Sauvegarder et quitter" if display_save else "Envoyer"
            ),
        )


class ImportForm(forms.Form):
    file = forms.FileField(label=_("Sélectionnez le contenu à importer."), required=True)
    images = forms.FileField(label=_("Fichier zip contenant les images du contenu."), required=False)

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_class = "content-wrapper"
        self.helper.form_method = "post"

        self.helper.layout = Layout(
            Field("file"),
            Field("images"),
            Submit("import-tuto", _("Importer le .tuto")),
        )
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()

        # Check that the files extensions are correct
        tuto = cleaned_data.get("file")
        images = cleaned_data.get("images")

        if tuto is not None:
            ext = tuto.name.split(".")[-1]
            if ext != "tuto":
                del cleaned_data["file"]
                msg = _("Le fichier doit être au format .tuto.")
                self._errors["file"] = self.error_class([msg])

        if images is not None:
            ext = images.name.split(".")[-1]
            if ext != "zip":
                del cleaned_data["images"]
                msg = _("Le fichier doit être au format .zip.")
                self._errors["images"] = self.error_class([msg])


class ImportContentForm(forms.Form):
    archive = forms.FileField(label=_("Sélectionnez l'archive de votre contenu."), required=True)
    image_archive = forms.FileField(label=_("Sélectionnez l'archive des images."), required=False)

    msg_commit = forms.CharField(
        label=_("Message de suivi"),
        max_length=400,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": _("Un résumé de vos ajouts et modifications.")}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = "content-wrapper"
        self.helper.form_method = "post"

        self.helper.layout = Layout(
            Field("archive"),
            Field("image_archive"),
            Field("msg_commit"),
            ButtonHolder(
                StrictButton("Importer l'archive", type="submit"),
            ),
        )

    def clean(self):
        cleaned_data = super().clean()

        # Check that the files extensions are correct
        archive = cleaned_data.get("archive")

        if archive is not None:
            ext = archive.name.split(".")[-1]
            if ext != "zip":
                del cleaned_data["archive"]
                msg = _("L'archive doit être au format .zip.")
                self._errors["archive"] = self.error_class([msg])

        image_archive = cleaned_data.get("image_archive")

        if image_archive is not None:
            ext = image_archive.name.split(".")[-1]
            if ext != "zip":
                del cleaned_data["image_archive"]
                msg = _("L'archive doit être au format .zip.")
                self._errors["image_archive"] = self.error_class([msg])

        return cleaned_data


class ImportNewContentForm(ImportContentForm):
    subcategory = forms.ModelMultipleChoiceField(
        label=_(
            "Sous catégories de votre contenu. Si aucune catégorie ne convient "
            "n'hésitez pas à en demander une nouvelle lors de la validation !"
        ),
        queryset=SubCategory.objects.order_by("title").all(),
        required=True,
        widget=forms.SelectMultiple(
            attrs={
                "required": "required",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_class = "content-wrapper"
        self.helper.form_method = "post"

        self.helper.layout = Layout(
            Field("archive"),
            Field("image_archive"),
            Field("subcategory"),
            Field("msg_commit"),
            ButtonHolder(
                StrictButton("Importer l'archive", type="submit"),
            ),
        )


class BetaForm(forms.Form):
    version = forms.CharField(widget=forms.HiddenInput, required=True)


# Notes


class NoteForm(forms.Form):
    text = forms.CharField(
        label="",
        widget=forms.Textarea(attrs={"placeholder": _("Votre message, au format Markdown."), "required": "required"}),
    )
    last_note = forms.IntegerField(label="", widget=forms.HiddenInput(), required=False)

    def __init__(self, content, reaction, *args, **kwargs):
        """initialize the form, handle antispam GUI
        :param content: the parent content
        :type content: zds.tutorialv2.models.database.PublishableContent
        :param reaction: the initial reaction if we edit, ``Ǹone```otherwise
        :type reaction: zds.tutorialv2.models.database.ContentReaction
        :param args:
        :param kwargs:
        """

        last_note = kwargs.pop("last_note", 0)

        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse("content:add-reaction") + f"?pk={content.pk}"
        self.helper.form_method = "post"

        self.helper.layout = Layout(
            CommonLayoutEditor(), Field("last_note") if not last_note else Hidden("last_note", last_note)
        )

        if reaction is not None:  # we're editing an existing comment
            self.helper.layout.append(HTML("{% include 'misc/hat_choice.html' with edited_message=reaction %}"))
        else:
            self.helper.layout.append(HTML("{% include 'misc/hat_choice.html' %}"))

        if content.antispam():
            if not reaction:
                self.helper["text"].wrap(
                    Field,
                    placeholder=_(
                        "Vous avez posté il n'y a pas longtemps. Merci de patienter "
                        "au moins 15 minutes entre deux messages consécutifs "
                        "afin de limiter le flood."
                    ),
                    disabled=True,
                )
        elif content.is_locked:
            self.helper["text"].wrap(Field, placeholder=_("Ce contenu est verrouillé."), disabled=True)

        if reaction is not None:
            self.initial.setdefault("text", reaction.text)

        self.content = content

    def clean(self):
        cleaned_data = super().clean()

        text = cleaned_data.get("text")

        if text is None or not text.strip():
            self._errors["text"] = self.error_class([_("Vous devez écrire une réponse !")])
            if "text" in cleaned_data:
                del cleaned_data["text"]

        elif len(text) > settings.ZDS_APP["forum"]["max_post_length"]:
            self._errors["text"] = self.error_class(
                [
                    _("Ce message est trop long, il ne doit pas dépasser {0} " "caractères.").format(
                        settings.ZDS_APP["forum"]["max_post_length"]
                    )
                ]
            )
        last_note = cleaned_data.get("last_note", "0")
        if last_note is None:
            last_note = "0"
        is_valid = last_note == "0" or self.content.last_note is None or int(last_note) == self.content.last_note.pk
        if not is_valid:
            self._errors["last_note"] = self.error_class([_("Quelqu'un a posté pendant que vous répondiez")])
        return cleaned_data


class NoteEditForm(NoteForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        content = kwargs["content"]
        reaction = kwargs["reaction"]

        self.helper.form_action = reverse("content:update-reaction") + "?message={}&pk={}".format(
            reaction.pk, content.pk
        )


# Validations.


class AskValidationForm(forms.Form):
    text = forms.CharField(
        label="",
        required=False,
        widget=forms.Textarea(
            attrs={"placeholder": _("Commentaire pour votre demande."), "rows": "3", "id": "ask_validation_text"}
        ),
    )

    version = forms.CharField(widget=forms.HiddenInput(), required=True)

    previous_page_url = ""

    def __init__(self, content, *args, **kwargs):
        """

        :param content: the parent content
        :type content: zds.tutorialv2.models.database.PublishableContent
        :param args:
        :param kwargs:
        :return:
        """
        super().__init__(*args, **kwargs)

        # modal form, send back to previous page:
        self.previous_page_url = get_content_version_url(content, content.current_version)

        self.helper = FormHelper()
        self.helper.form_action = reverse("validation:ask", kwargs={"pk": content.pk, "slug": content.slug})
        self.helper.form_method = "post"
        self.helper.form_class = "modal modal-flex"
        self.helper.form_id = "ask-validation"

        self.no_subcategories = content.subcategory.count() == 0
        no_category_msg = HTML(
            _(
                """<p><strong>Votre publication n'est dans aucune catégorie.
                                    Vous devez <a href="{}">choisir une catégorie</a>
                                    avant de demander la validation.</strong></p>""".format(
                    reverse("content:edit-categories", kwargs={"pk": content.pk}),
                )
            )
        )

        self.no_license = not content.licence
        no_license_msg = HTML(
            _(
                """<p><strong>Vous n'avez pas choisi de licence pour votre publication.
                                   Vous devez <a href="#edit-license" class="open-modal">choisir une licence</a>
                                   avant de demander la validation.</strong></p>"""
            )
        )

        self.helper.layout = Layout(
            no_category_msg if self.no_subcategories else None,
            no_license_msg if self.no_license else None,
            Field("text"),
            Field("version"),
            StrictButton(_("Confirmer"), type="submit", css_class="btn-submit"),
        )

    def clean(self):
        cleaned_data = super().clean()

        base_error_msg = "La validation n'a pas été demandée. "

        if self.no_subcategories:
            error = [_(base_error_msg + "Vous devez choisir au moins une catégorie pour votre publication.")]
            self.add_error(field=None, error=error)

        if self.no_license:
            error = [_(base_error_msg + "Vous devez choisir une licence pour votre publication.")]
            self.add_error(field=None, error=error)

        return cleaned_data


class AcceptValidationForm(forms.Form):
    validation = None

    text = forms.CharField(
        label="",
        required=True,
        error_messages={"required": _("Vous devez fournir un commentaire aux validateurs.")},
        widget=forms.Textarea(attrs={"placeholder": _("Commentaire de publication."), "rows": "2", "minlength": "3"}),
        validators=[MinLengthValidator(3, _("Votre commentaire doit faire au moins 3 caractères."))],
    )

    is_major = forms.BooleanField(label=_("Version majeure ?"), required=False, initial=True)

    def __init__(self, validation, *args, **kwargs):
        """

        :param validation: the linked validation request object
        :type validation: zds.tutorialv2.models.database.Validation
        :param args:
        :param kwargs:
        :return:
        """
        self.previous_page_url = get_content_version_url(validation.content, validation.version)

        super().__init__(*args, **kwargs)

        # if content is already published, it's probably a minor change, so do not check `is_major`
        self.fields["is_major"].initial = not validation.content.sha_public

        self.helper = FormHelper()
        self.helper.form_action = reverse("validation:accept", kwargs={"pk": validation.pk})
        self.helper.form_method = "post"
        self.helper.form_class = "modal modal-flex"
        self.helper.form_id = "valid-publish"

        self.helper.layout = Layout(
            Field("text"), Field("is_major"), StrictButton(_("Publier"), type="submit", css_class="btn-submit")
        )


class CancelValidationForm(forms.Form):
    text = forms.CharField(
        label="",
        required=True,
        widget=forms.Textarea(
            attrs={"placeholder": _("Pourquoi annuler la validation ?"), "rows": "4", "id": "cancel_text"}
        ),
    )

    def __init__(self, validation, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.previous_page_url = get_content_version_url(validation.content, validation.version)

        self.helper = FormHelper()
        self.helper.form_action = reverse("validation:cancel", kwargs={"pk": validation.pk})
        self.helper.form_method = "post"
        self.helper.form_class = "modal modal-flex"
        self.helper.form_id = "cancel-validation"

        self.helper.layout = Layout(
            HTML("<p>Êtes-vous certain de vouloir annuler la validation de ce contenu ?</p>"),
            Field("text"),
            ButtonHolder(StrictButton(_("Confirmer"), type="submit", css_class="btn-submit")),
        )

    def clean(self):
        cleaned_data = super().clean()

        text = cleaned_data.get("text")

        if text is None or not text.strip():
            self._errors["text"] = self.error_class([_("Merci de fournir une raison à l'annulation.")])
            if "text" in cleaned_data:
                del cleaned_data["text"]

        elif len(text) < 3:
            self._errors["text"] = self.error_class([_("Votre commentaire doit faire au moins 3 caractères.")])
            if "text" in cleaned_data:
                del cleaned_data["text"]

        return cleaned_data


class RejectValidationForm(forms.Form):
    text = forms.CharField(
        label="",
        required=True,
        widget=forms.Textarea(attrs={"placeholder": _("Commentaire de rejet."), "rows": "6", "id": "reject_text"}),
    )

    def __init__(self, validation, *args, **kwargs):
        """

        :param validation: the linked validation request object
        :type validation: zds.tutorialv2.models.database.Validation
        :param args:
        :param kwargs:
        :return:
        """
        super().__init__(*args, **kwargs)

        self.previous_page_url = get_content_version_url(validation.content, validation.version)

        self.helper = FormHelper()
        self.helper.form_action = reverse("validation:reject", kwargs={"pk": validation.pk})
        self.helper.form_method = "post"
        self.helper.form_class = "modal modal-flex"
        self.helper.form_id = "reject"

        self.helper.layout = Layout(
            Field("text"), ButtonHolder(StrictButton(_("Rejeter"), type="submit", css_class="btn-submit"))
        )

    def clean(self):
        cleaned_data = super().clean()

        text = cleaned_data.get("text")

        if text is None or not text.strip():
            self._errors["text"] = self.error_class([_("Merci de fournir une raison au rejet.")])
            if "text" in cleaned_data:
                del cleaned_data["text"]

        elif len(text) < 3:
            self._errors["text"] = self.error_class([_("Votre commentaire doit faire au moins 3 caractères.")])
            if "text" in cleaned_data:
                del cleaned_data["text"]

        return cleaned_data


class RevokeValidationForm(forms.Form):
    version = forms.CharField(widget=forms.HiddenInput())

    text = forms.CharField(
        label="",
        required=True,
        widget=forms.Textarea(
            attrs={"placeholder": _("Pourquoi dépublier ce contenu ?"), "rows": "6", "id": "up_text"}
        ),
    )

    def __init__(self, content, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # modal form, send back to previous page:
        self.previous_page_url = content.get_absolute_url_online()

        self.helper = FormHelper()
        self.helper.form_action = reverse("validation:revoke", kwargs={"pk": content.pk, "slug": content.slug})
        self.helper.form_method = "post"
        self.helper.form_class = "modal modal-flex"
        self.helper.form_id = "unpublish"

        self.helper.layout = Layout(
            Field("text"), Field("version"), StrictButton(_("Dépublier"), type="submit", css_class="btn-submit")
        )

    def clean(self):
        cleaned_data = super().clean()

        text = cleaned_data.get("text")

        if text is None or not text.strip():
            self._errors["text"] = self.error_class([_("Veuillez fournir la raison de votre dépublication.")])
            if "text" in cleaned_data:
                del cleaned_data["text"]

        elif len(text) < 3:
            self._errors["text"] = self.error_class([_("Votre commentaire doit faire au moins 3 caractères.")])
            if "text" in cleaned_data:
                del cleaned_data["text"]

        return cleaned_data


class JsFiddleActivationForm(forms.Form):
    js_support = forms.BooleanField(label="À cocher pour activer JSFiddle.", required=False, initial=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse("content:activate-jsfiddle")
        self.helper.form_method = "post"
        self.helper.form_class = "modal modal-flex"
        self.helper.form_id = "js-activation"

        self.helper.layout = Layout(
            Field("js_support"),
            ButtonHolder(
                StrictButton(_("Valider"), type="submit", css_class="btn-submit"),
            ),
            Hidden("pk", "{{ content.pk }}"),
        )

    def clean(self):
        cleaned_data = super().clean()
        if "js_support" not in cleaned_data:
            cleaned_data["js_support"] = False
        if "pk" in self.data and self.data["pk"].isdigit():
            cleaned_data["pk"] = int(self.data["pk"])
        else:
            cleaned_data["pk"] = 0
        return cleaned_data


class MoveElementForm(forms.Form):
    child_slug = forms.HiddenInput()
    container_slug = forms.HiddenInput()
    first_level_slug = forms.HiddenInput()
    moving_method = forms.HiddenInput()

    MOVE_UP = "up"
    MOVE_DOWN = "down"
    MOVE_AFTER = "after"
    MOVE_BEFORE = "before"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse("content:move-element")
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Field("child_slug"),
            Field("container_slug"),
            Field("first_level_slug"),
            Field("moving_method"),
            Hidden("pk", "{{ content.pk }}"),
        )


class WarnTypoForm(forms.Form):
    text = forms.CharField(
        label="",
        required=True,
        widget=forms.Textarea(attrs={"placeholder": _("Expliquez la faute"), "rows": "3", "id": "warn_text"}),
    )

    target = forms.CharField(widget=forms.HiddenInput(), required=False)
    version = forms.CharField(widget=forms.HiddenInput(), required=True)

    def __init__(self, content, targeted, public=True, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.content = content
        self.targeted = targeted

        # modal form, send back to previous page if any:
        if public:
            self.previous_page_url = targeted.get_absolute_url_online()
        else:
            self.previous_page_url = targeted.get_absolute_url_beta()

        # add an additional link to send PM if needed
        type_ = _("l'article")

        if content.is_tutorial:
            type_ = _("le tutoriel")
        elif content.is_opinion:
            type_ = _("le billet")

        if targeted.get_tree_depth() == 0:
            pm_title = _("J'ai trouvé une faute dans {} « {} ».").format(type_, targeted.title)
        else:
            pm_title = _("J'ai trouvé une faute dans le chapitre « {} ».").format(targeted.title)

        usernames = ""
        num_of_authors = content.authors.count()
        for index, user in enumerate(content.authors.all()):
            if index != 0:
                usernames += "&"
            usernames += "username=" + user.username

        msg = _('<p>Pas assez de place ? <a href="{}?title={}&{}">Envoyez un MP {}</a> !</a>').format(
            reverse("mp:create"), pm_title, usernames, _("à l'auteur") if num_of_authors == 1 else _("aux auteurs")
        )

        version = content.sha_beta
        if public:
            version = content.sha_public

        # create form
        self.helper = FormHelper()
        self.helper.form_action = reverse("content:warn-typo") + f"?pk={content.pk}"
        self.helper.form_method = "post"
        self.helper.form_class = "modal modal-flex"
        self.helper.form_id = "warn-typo-modal"
        self.helper.layout = Layout(
            Field("target"),
            Field("text"),
            HTML(msg),
            Hidden("pk", "{{ content.pk }}"),
            Hidden("version", version),
            ButtonHolder(StrictButton(_("Envoyer"), type="submit", css_class="btn-submit")),
        )

    def clean(self):
        cleaned_data = super().clean()

        text = cleaned_data.get("text")

        if text is None or not text.strip():
            self._errors["text"] = self.error_class([_("Vous devez indiquer la faute commise.")])
            if "text" in cleaned_data:
                del cleaned_data["text"]

        elif len(text) < 3:
            self._errors["text"] = self.error_class([_("Votre commentaire doit faire au moins 3 caractères.")])
            if "text" in cleaned_data:
                del cleaned_data["text"]

        return cleaned_data


class PublicationForm(forms.Form):
    """
    The publication form (used only for content without preliminary validation).
    """

    def __init__(self, content, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.previous_page_url = content.get_absolute_url()

        self.helper = FormHelper()
        self.helper.form_action = reverse("validation:publish-opinion", kwargs={"pk": content.pk, "slug": content.slug})
        self.helper.form_method = "post"
        self.helper.form_class = "modal modal-flex"
        self.helper.form_id = "valid-publication"

        self.no_subcategories = content.subcategory.count() == 0
        no_category_msg = HTML(
            _(
                """<p><strong>Votre publication n'est dans aucune catégorie.
                                    Vous devez <a href="{}">choisir une catégorie</a>
                                    avant de publier.</strong></p>""".format(
                    reverse("content:edit-categories", kwargs={"pk": content.pk})
                )
            )
        )

        self.no_license = not content.licence
        no_license_msg = HTML(
            _(
                """<p><strong>Vous n'avez pas choisi de licence pour votre publication.
                                   Vous devez <a href="#edit-license" class="open-modal">choisir une licence</a>
                                   avant de publier.</strong></p>"""
            )
        )

        self.helper.layout = Layout(
            no_category_msg if self.no_subcategories else None,
            no_license_msg if self.no_license else None,
            HTML(_("<p>Ce billet sera publié directement et n'engage que vous.</p>")),
            StrictButton(_("Publier"), type="submit", css_class="btn-submit"),
        )

    def clean(self):
        cleaned_data = super().clean()

        base_error_msg = "La publication n'a pas été effectuée. "

        if self.no_subcategories:
            error = _(base_error_msg + "Vous devez choisir au moins une catégorie pour votre publication.")
            self.add_error(field=None, error=error)

        if self.no_license:
            error = _(base_error_msg + "Vous devez choisir une licence pour votre publication.")
            self.add_error(field=None, error=error)

        return cleaned_data


class UnpublicationForm(forms.Form):
    version = forms.CharField(widget=forms.HiddenInput())

    text = forms.CharField(
        label="",
        required=True,
        widget=forms.Textarea(
            attrs={"placeholder": _("Pourquoi dépublier ce contenu ?"), "rows": "6", "id": "up_reason"}
        ),
    )

    def __init__(self, content, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # modal form, send back to previous page:
        self.previous_page_url = content.get_absolute_url_online()

        self.helper = FormHelper()
        self.helper.form_action = reverse(
            "validation:unpublish-opinion", kwargs={"pk": content.pk, "slug": content.slug}
        )

        self.helper.form_method = "post"
        self.helper.form_class = "modal modal-flex"
        self.helper.form_id = "unpublish"

        self.helper.layout = Layout(
            Field("text"), Field("version"), StrictButton(_("Dépublier"), type="submit", css_class="btn-submit")
        )


class PickOpinionForm(forms.Form):
    version = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, content, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # modal form, send back to previous page:
        self.previous_page_url = content.get_absolute_url_online()

        self.helper = FormHelper()
        self.helper.form_action = reverse("validation:pick-opinion", kwargs={"pk": content.pk, "slug": content.slug})
        self.helper.form_method = "post"
        self.helper.form_class = "modal modal-flex"
        self.helper.form_id = "pick-opinion"

        self.helper.layout = Layout(
            HTML(
                "<p>Êtes-vous certain(e) de vouloir valider ce billet ? "
                "Il pourra maintenant être présent sur la page d’accueil.</p>"
            ),
            Field("version"),
            StrictButton(_("Valider"), type="submit", css_class="btn-submit"),
        )


class DoNotPickOpinionForm(forms.Form):
    operation = forms.CharField(widget=forms.HiddenInput())
    redirect = forms.CharField(widget=forms.HiddenInput(), required=False)

    def __init__(self, content, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # modal form, send back to previous page:
        self.previous_page_url = content.get_absolute_url_online()

        self.helper = FormHelper()
        self.helper.form_action = reverse("validation:unpick-opinion", kwargs={"pk": content.pk, "slug": content.slug})
        self.helper.form_method = "post"
        self.helper.form_class = "modal modal-flex"
        self.helper.form_id = "unpick-opinion"

        self.helper.layout = Layout(
            HTML(_("<p>Ce billet n'apparaîtra plus dans la liste des billets à choisir.</p>")),
            Field("operation"),
            StrictButton(_("Valider"), type="submit", css_class="btn-submit"),
        )

    def clean(self):
        cleaned = super().clean()
        cleaned["operation"] = (
            self.data["operation"] if self.data["operation"] in ["NO_PICK", "REJECT", "REMOVE_PUB"] else None
        )
        cleaned["redirect"] = self.data["redirect"] == "true" if "redirect" in self.data else False
        return cleaned

    def is_valid(self):
        base = super().is_valid()
        if not self["operation"]:
            self._errors["operation"] = _("Opération invalide, NO_PICK, REJECT ou REMOVE_PUB attendu.")
            return False
        return base


class UnpickOpinionForm(forms.Form):
    version = forms.CharField(widget=forms.HiddenInput())

    text = forms.CharField(
        label="",
        required=True,
        widget=forms.Textarea(
            attrs={"placeholder": _("Pourquoi retirer ce billet de la liste des billets choisis ?"), "rows": "6"}
        ),
    )

    def __init__(self, content, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # modal form, send back to previous page:
        self.previous_page_url = content.get_absolute_url_online()

        self.helper = FormHelper()
        self.helper.form_action = reverse("validation:unpick-opinion", kwargs={"pk": content.pk, "slug": content.slug})
        self.helper.form_method = "post"
        self.helper.form_class = "modal modal-flex"
        self.helper.form_id = "unpick-opinion"

        self.helper.layout = Layout(
            Field("version"), Field("text"), StrictButton(_("Enlever"), type="submit", css_class="btn-submit")
        )


class PromoteOpinionToArticleForm(forms.Form):
    version = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, content, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # modal form, send back to previous page:
        self.previous_page_url = content.get_absolute_url_online()

        self.helper = FormHelper()
        self.helper.form_action = reverse("validation:promote-opinion", kwargs={"pk": content.pk, "slug": content.slug})
        self.helper.form_method = "post"
        self.helper.form_class = "modal modal-flex"
        self.helper.form_id = "convert-opinion"

        self.helper.layout = Layout(
            HTML(
                """<p>Avez-vous la certitude de vouloir proposer ce billet comme article ?
                    Cela copiera le billet pour en faire un article,
                    puis créera une demande de validation pour ce dernier.</p>"""
            ),
            Field("version"),
            StrictButton(_("Valider"), type="submit", css_class="btn-submit"),
        )


class ContentCompareStatsURLForm(forms.Form):
    urls = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple(), required=True)

    def __init__(self, urls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["urls"].choices = urls

        self.helper = FormHelper()
        self.helper.layout = Layout(Field("urls"), StrictButton(_("Comparer"), type="submit"))

    def clean(self):
        cleaned_data = super().clean()
        urls = cleaned_data.get("urls")
        if not urls:
            raise forms.ValidationError(_("Vous devez choisir des URL a comparer"))
        if len(urls) < 2:
            raise forms.ValidationError(_("Il faut au minimum 2 urls à comparer"))
