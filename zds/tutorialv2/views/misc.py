from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, HTML, Hidden, ButtonHolder
from django import forms
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponse, Http404
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from zds import json_handler
from zds.featured.mixins import FeatureableMixin
from zds.member.decorator import LoggedWithReadWriteHability
from zds.member.models import Profile
from zds.notification.models import NewPublicationSubscription
from zds.tutorialv2.mixins import SingleOnlineContentViewMixin, SingleContentFormViewMixin
from zds.tutorialv2.utils import search_container_or_404
from zds.mp.utils import send_mp
from zds.utils.misc import is_ajax


class RequestFeaturedContent(LoggedWithReadWriteHability, FeatureableMixin, SingleOnlineContentViewMixin, FormView):
    redirection_is_needed = False

    def featured_request_allowed(self):
        """Featured request is not allowed on obsolete content and opinions"""
        return self.object.type != "OPINION" and not self.object.is_obsolete

    def post(self, request, *args, **kwargs):
        self.public_content_object = self.get_public_object()
        self.object = self.get_object()

        response = dict()
        response["requesting"], response["newCount"] = self.toogle_featured_request(request.user)
        if is_ajax(self.request):
            return HttpResponse(json_handler.dumps(response), content_type="application/json")
        return redirect(self.public_content_object.get_absolute_url_online())


class FollowNewContent(LoggedWithReadWriteHability, FormView):
    @staticmethod
    def perform_follow(user_to_follow, user):
        return NewPublicationSubscription.objects.toggle_follow(user_to_follow, user).is_active

    @staticmethod
    def perform_follow_by_email(user_to_follow, user):
        return NewPublicationSubscription.objects.toggle_follow(user_to_follow, user, True).is_active

    def post(self, request, *args, **kwargs):
        response = {}

        # get user to follow
        try:
            user_to_follow = User.objects.get(pk=kwargs["pk"])
        except User.DoesNotExist:
            raise Http404

        # follow content if user != user_to_follow only
        if user_to_follow == request.user:
            raise PermissionDenied

        with transaction.atomic():
            if "follow" in request.POST:
                response["follow"] = self.perform_follow(user_to_follow, request.user)
                response["subscriberCount"] = NewPublicationSubscription.objects.get_subscriptions(
                    user_to_follow
                ).count()
            elif "email" in request.POST:
                response["email"] = self.perform_follow_by_email(user_to_follow, request.user)

        if is_ajax(self.request):
            return HttpResponse(json_handler.dumps(response), content_type="application/json")
        return redirect(request.META.get("HTTP_REFERER"))


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

        # Modal form, send back to previous page if any
        if public:
            self.previous_page_url = targeted.get_absolute_url_online()
        else:
            self.previous_page_url = targeted.get_absolute_url_beta()

        if targeted.get_tree_depth() == 0:
            pm_title = _("J'ai trouvé une faute dans « {} ».").format(targeted.title)
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


class WarnTypoView(SingleContentFormViewMixin):
    modal_form = True
    form_class = WarnTypoForm
    must_be_author = False

    http_method_names = ["post"]
    object = None

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
        user = self.request.user
        authors = list(Profile.objects.contactable_members().filter(user__in=self.object.authors.all()))
        authors = list(author.user for author in authors)

        # Check if the warning is done on a public or beta version
        is_public = False
        if form.content.is_public:
            is_public = True
        elif not form.content.is_beta:
            raise Http404("Le contenu n'est ni public, ni en bêta.")

        if not authors:
            if self.object.authors.count() > 1:
                messages.error(self.request, _("Les auteurs sont malheureusement injoignables."))
            else:
                messages.error(self.request, _("L'auteur est malheureusement injoignable."))

        elif user in authors:  # Author is trying to PM himself
            messages.error(self.request, _("Impossible d'envoyer la proposition de correction : vous êtes auteur."))

        else:  # Send correction
            text = "\n".join(["> " + line for line in form.cleaned_data["text"].split("\n")])
            pm_title = _("J'ai trouvé une faute dans « {} ».").format(form.content.title)
            msg = render_to_string(
                "tutorialv2/messages/warn_typo.md",
                {
                    "user": user,
                    "content": form.content,
                    "target": form.targeted,
                    "public": is_public,
                    "text": text,
                },
            )
            send_mp(user, authors, pm_title, "", msg, leave=False)
            messages.success(self.request, _("Merci pour votre proposition de correction."))

        return redirect(form.previous_page_url)
