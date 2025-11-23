from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Layout
from django import forms
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from zds.gallery.models import GALLERY_WRITE, UserGallery
from zds.member.decorator import LoggedWithReadWriteHability
from zds.member.models import Profile
from zds.member.utils import get_bot_account
from zds.mp.models import is_reachable
from zds.mp.utils import send_mp
from zds.tutorialv2 import signals
from zds.tutorialv2.mixins import SingleContentFormViewMixin
from zds.utils.models import get_hat_from_settings


class AuthorForm(forms.Form):
    username = forms.CharField(label=_("Auteurs à ajouter séparés d'une virgule."), required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = "content-wrapper"
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Field("username"),
            StrictButton(_("Ajouter"), type="submit"),
        )

    def clean_username(self):
        """
        Check each username in the comma-separated list and add the corresponding Users to cleaned_data["users"].
        Skip non-existing usernames and remove duplicates.
        """
        cleaned_data = super().clean()

        username_field = cleaned_data.get("username")
        if username_field is None:
            return cleaned_data

        usernames = username_field.split(",")
        usernames_normalized = [username.strip().lower() for username in usernames]

        condition = Q()
        for username in usernames_normalized:
            condition |= Q(username__iexact=username)
        users = User.objects.filter(condition, profile__in=Profile.objects.contactable_members())

        if len(users) > 0:
            cleaned_data["users"] = list(users)

        return cleaned_data

    def is_valid(self):
        return super().is_valid() and "users" in self.clean()


class RemoveAuthorForm(AuthorForm):
    def clean_username(self):
        """Check every username and send it to the cleaned_data['user'] list

        :return: a dictionary of all treated data with the users key added
        """
        cleaned_data = super(AuthorForm, self).clean()
        users = []
        for username in cleaned_data.get("username").split(","):
            # we can remove all users (bots inclued)
            user = Profile.objects.filter(user__username__iexact=username.strip().lower()).first()
            if user is not None:
                users.append(user.user)
        if len(users) > 0:
            cleaned_data["users"] = users
        return cleaned_data


class AddAuthorView(LoggedWithReadWriteHability, SingleContentFormViewMixin):
    must_be_author = True
    form_class = AuthorForm
    authorized_for_staff = True
    http_method_names = ["post"]

    def form_valid(self, form):
        bot = get_bot_account()
        authors = self.object.authors.all()
        new_authors = [user for user in form.cleaned_data["users"] if user not in authors]
        for user in new_authors:
            self.object.authors.add(user)

            if self.object.validation_private_message:
                self.object.validation_private_message.add_participant(user)

            if user != self.request.user:
                self.notify_by_private_message(user, bot)

            UserGallery(gallery=self.object.gallery, user=user, mode=GALLERY_WRITE).save()

            signals.authors_management.send(
                sender=self.__class__, content=self.object, performer=self.request.user, author=user, action="add"
            )

        self.object.save()
        self.success_url = self.object.get_absolute_url()

        return super().form_valid(form)

    def notify_by_private_message(self, user, bot):
        url_index = reverse(f"content:find-all", args=[user.username])
        send_mp(
            bot,
            [user],
            _("Ajout à la rédaction d'une publication"),
            self.versioned_object.title,
            render_to_string(
                "tutorialv2/messages/add_author_pm.md",
                {
                    "content": self.object,
                    "url": self.object.get_absolute_url(),
                    "index": url_index,
                    "user": user.username,
                },
            ),
            hat=get_hat_from_settings("validation"),
        )

    def form_invalid(self, form):
        messages.error(self.request, _("Les auteurs sélectionnés n'existent pas."))
        self.success_url = self.object.get_absolute_url()
        return super().form_valid(form)


class RemoveAuthorView(LoggedWithReadWriteHability, SingleContentFormViewMixin):
    form_class = RemoveAuthorForm
    must_be_author = True
    authorized_for_staff = True
    http_method_names = ["post"]

    def form_valid(self, form):
        content = self.object
        current_user = False
        users = form.cleaned_data["users"]

        bot = get_bot_account()
        for user in users:
            if content.remove_author(user):
                if user.pk == self.request.user.pk:
                    current_user = True
                elif is_reachable(user):
                    self.notify_by_private_message(user, bot)
                signals.authors_management.send(
                    sender=self.__class__,
                    content=self.object,
                    performer=self.request.user,
                    author=user,
                    action="remove",
                )
            else:  # if user is incorrect or alone
                messages.error(
                    self.request,
                    _(
                        "Vous êtes le seul auteur de la publication ou le membre sélectionné en a déjà quitté la rédaction."
                    ),
                )
                return redirect(self.object.get_absolute_url())

        content.save()

        if current_user:  # Redirect self-removing authors to their publications list
            messages.success(self.request, _("Vous avez bien quitté la rédaction de la publication."))
            self.success_url = reverse("content:find-all", args=[self.request.user.username])
        else:  # The user removed another user from the authors
            authors_list = self.users_list(users)
            messages.success(
                self.request,
                _("Vous avez enlevé {} de la liste des auteurs et autrices de la publication.").format(authors_list),
            )
            self.success_url = self.object.get_absolute_url()

        return super().form_valid(form)

    @staticmethod
    def users_list(users):
        authors_list = ""
        for index, user in enumerate(users):
            if index > 0:
                if index == len(users) - 1:
                    authors_list += _(" et ")
                else:
                    authors_list += _(", ")
            authors_list += user.username
        return authors_list

    def notify_by_private_message(self, user, bot):
        send_mp(
            bot,
            [user],
            _("Retrait de la rédaction de la publication"),
            self.versioned_object.title,
            render_to_string(
                "tutorialv2/messages/remove_author_pm.md",
                {
                    "content": self.object,
                    "user": user.username,
                },
            ),
            hat=get_hat_from_settings("validation"),
        )

    def form_invalid(self, form):
        messages.error(self.request, _("Les auteurs sélectionnés n'existent pas."))
        self.success_url = self.object.get_absolute_url()
        return super().form_valid(form)
