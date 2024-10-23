from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field
from django import forms
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

from zds.gallery.models import UserGallery, GALLERY_WRITE
from zds.member.decorator import LoggedWithReadWriteHability
from zds.member.models import Profile
from zds.member.utils import get_bot_account
from zds.mp.models import is_reachable
from zds.tutorialv2 import signals

from zds.tutorialv2.mixins import SingleContentFormViewMixin
from zds.utils.models import get_hat_from_settings
from zds.mp.utils import send_mp


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


class RemoveAuthorFromContent(LoggedWithReadWriteHability, SingleContentFormViewMixin):
    form_class = RemoveAuthorForm
    must_be_author = True
    authorized_for_staff = True

    @staticmethod
    def remove_author(content, user):
        """Remove a user from the authors and ensure that he is access to the content's gallery is also removed.
        The last author is not removed.

        :param content: the content
        :type content: zds.tutorialv2.models.database.PublishableContent
        :param user: the author
        :type user: User
        :return: ``True`` if the author was removed, ``False`` otherwise
        """
        if user in content.authors.all() and content.authors.count() > 1:
            gallery = UserGallery.objects.filter(user__pk=user.pk, gallery__pk=content.gallery.pk).first()

            if gallery:
                gallery.delete()

            content.authors.remove(user)
            return True

        return False

    def form_valid(self, form):
        current_user = False
        users = form.cleaned_data["users"]

        _type = (_("cet article"), _("de l'article"))
        if self.object.is_tutorial:
            _type = (_("ce tutoriel"), _("du tutoriel"))
        elif self.object.is_opinion:
            _type = (_("ce billet"), _("du billet"))

        bot = get_bot_account()
        for user in users:
            if RemoveAuthorFromContent.remove_author(self.object, user):
                if user.pk == self.request.user.pk:
                    current_user = True
                elif is_reachable(user):
                    send_mp(
                        bot,
                        [user],
                        format_lazy("{}{}", _("Retrait de la rédaction "), _type[1]),
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
                    _("Vous êtes le seul auteur de {} ou le membre sélectionné en a déjà quitté la rédaction.").format(
                        _type[0]
                    ),
                )
                return redirect(self.object.get_absolute_url())

        self.object.save()

        authors_list = ""

        for index, user in enumerate(form.cleaned_data["users"]):
            if index > 0:
                if index == len(users) - 1:
                    authors_list += _(" et ")
                else:
                    authors_list += _(", ")
            authors_list += user.username

        if not current_user:  # if the removed author is not current user
            messages.success(
                self.request,
                _("Vous avez enlevé {} de la liste des auteurs et autrices de {}.").format(authors_list, _type[0]),
            )
            self.success_url = self.object.get_absolute_url()
        else:  # if current user is leaving the content's redaction, redirect him to a more suitable page
            messages.success(self.request, _("Vous avez bien quitté la rédaction de {}.").format(_type[0]))
            self.success_url = reverse(
                self.object.type.lower() + ":find-" + self.object.type.lower(), args=[self.request.user.username]
            )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _("Les auteurs sélectionnés n'existent pas."))
        self.success_url = self.object.get_absolute_url()
        return super().form_valid(form)
