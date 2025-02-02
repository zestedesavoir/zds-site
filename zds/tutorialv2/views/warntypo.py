from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import ButtonHolder, HTML, Field, Hidden, Layout
from django import forms
from django.contrib import messages

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from zds.mp.models import filter_reachable
from zds.mp.utils import send_mp
from zds.tutorialv2.mixins import SingleContentFormViewMixin
from zds.tutorialv2.utils import search_container_or_404


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

        # Manage targeted version
        self.previous_page_url = targeted.get_absolute_url_beta()
        version = content.sha_beta
        if public:
            self.previous_page_url = targeted.get_absolute_url_online()
            version = content.sha_public

        # Create form
        self.helper = FormHelper()
        self.helper.form_action = reverse("content:warn-typo") + f"?pk={content.pk}"
        self.helper.form_method = "post"
        self.helper.form_class = "modal modal-flex"
        self.helper.form_id = "warn-typo-modal"
        self.helper.layout = Layout(
            Field("target"),
            Field("text"),
            HTML(self.get_link_for_pm(content, targeted)),
            Hidden("pk", "{{ content.pk }}"),
            Hidden("version", version),
            ButtonHolder(StrictButton(_("Envoyer"), type="submit", css_class="btn-submit")),
        )

    @staticmethod
    def get_link_for_pm(content, targeted):
        if targeted.get_tree_depth() == 0:
            pm_title = _("J'ai trouvé une faute dans « {} ».").format(targeted.title)
        else:
            pm_title = _("J'ai trouvé une faute dans le chapitre « {} ».").format(targeted.title)
        recipients = filter_reachable(content.authors.all())
        usernames = "&".join([f"username={recipient.username}" for recipient in recipients])
        plural = _("aux auteurs") if len(recipients) > 1 else _("à l'auteur")
        msg = _('<p>Pas assez de place ? <a href="{}?title={}&{}">Envoyez un MP {}</a> !</a>').format(
            reverse("mp:create"), pm_title, usernames, plural
        )
        return msg

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


class WarnTypoView(SingleContentFormViewMixin):
    modal_form = True
    form_class = WarnTypoForm
    must_be_author = False

    http_method_names = ["post"]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        versioned = self.get_versioned_object()
        kwargs["content"] = versioned
        kwargs["targeted"] = versioned

        if "target" in self.request.POST and self.request.POST["target"] != "":
            kwargs["targeted"] = search_container_or_404(versioned, self.request.POST["target"])

        kwargs["public"] = True

        if versioned.is_beta:
            kwargs["public"] = False
        elif not versioned.is_public:
            raise PermissionDenied

        return kwargs

    def form_valid(self, form):
        # Check if the warning is done on a public or beta version
        is_public = False
        if form.content.is_public:
            is_public = True
        elif not form.content.is_beta:
            raise Http404("Le contenu n'est ni public, ni en bêta.")

        user = self.request.user
        recipients = filter_reachable(self.object.authors.all())
        if not recipients:
            if self.object.authors.count() > 1:
                messages.error(self.request, _("Les auteurs sont malheureusement injoignables."))
            else:
                messages.error(self.request, _("L'auteur est malheureusement injoignable."))
        elif user in recipients:
            messages.error(self.request, _("Impossible d'envoyer la proposition de correction : vous êtes auteur."))
        else:
            self.send_pm(form, is_public, recipients, user)
            messages.success(self.request, _("Merci pour votre proposition de correction."))

        return redirect(form.previous_page_url)

    def send_pm(self, form, is_public, recipients, sender):
        text = "\n".join(["> " + line for line in form.cleaned_data["text"].split("\n")])
        title = _("J'ai trouvé une faute dans « {} ».").format(form.content.title)
        body = render_to_string(
            "tutorialv2/messages/warn_typo.md",
            {
                "user": sender,
                "content": form.content,
                "target": form.targeted,
                "public": is_public,
                "text": text,
            },
        )
        send_mp(sender, recipients, title, "", body, leave=False)
