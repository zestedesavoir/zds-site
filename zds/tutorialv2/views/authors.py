from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

from zds.gallery.models import UserGallery, GALLERY_WRITE
from zds.member.decorator import LoggedWithReadWriteHability

from zds.tutorialv2.forms import AuthorForm, RemoveAuthorForm
from zds.tutorialv2.mixins import SingleContentFormViewMixin
from zds.utils.models import get_hat_from_settings
from zds.mp.utils import send_mp


class AddAuthorToContent(LoggedWithReadWriteHability, SingleContentFormViewMixin):
    only_draft_version = True
    must_be_author = True
    form_class = AuthorForm
    authorized_for_staff = True

    def get(self, request, *args, **kwargs):
        content = self.get_object()
        url = "content:find-{}".format("tutorial" if content.is_tutorial() else content.type.lower())
        return redirect(url, self.request.user)

    def form_valid(self, form):

        _type = _("de l'article")

        if self.object.is_tutorial:
            _type = _("du tutoriel")
        elif self.object.is_opinion:
            _type = _("du billet")

        bot = get_object_or_404(User, username=settings.ZDS_APP["member"]["bot_account"])
        all_authors_pk = [author.pk for author in self.object.authors.all()]
        for user in form.cleaned_data["users"]:
            if user.pk not in all_authors_pk:
                self.object.authors.add(user)
                if self.object.validation_private_message:
                    self.object.validation_private_message.add_participant(user)
                all_authors_pk.append(user.pk)
                if user != self.request.user:
                    url_index = reverse(self.object.type.lower() + ":find-" + self.object.type.lower(), args=[user.pk])
                    send_mp(
                        bot,
                        [user],
                        format_lazy("{}{}", _("Ajout à la rédaction "), _type),
                        self.versioned_object.title,
                        render_to_string(
                            "tutorialv2/messages/add_author_pm.md",
                            {
                                "content": self.object,
                                "type": _type,
                                "url": self.object.get_absolute_url(),
                                "index": url_index,
                                "user": user.username,
                            },
                        ),
                        hat=get_hat_from_settings("validation"),
                    )
                UserGallery(gallery=self.object.gallery, user=user, mode=GALLERY_WRITE).save()
        self.object.save()
        self.success_url = self.object.get_absolute_url()

        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _("Les auteurs sélectionnés n'existent pas."))
        self.success_url = self.object.get_absolute_url()
        return super().form_valid(form)


class RemoveAuthorFromContent(LoggedWithReadWriteHability, SingleContentFormViewMixin):

    form_class = RemoveAuthorForm
    only_draft_version = True
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

        bot = get_object_or_404(User, username=settings.ZDS_APP["member"]["bot_account"])
        for user in users:
            if RemoveAuthorFromContent.remove_author(self.object, user):
                if user.pk == self.request.user.pk:
                    current_user = True
                else:
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
            else:  # if user is incorrect or alone
                messages.error(
                    self.request,
                    _(
                        "Vous êtes le seul auteur de {} ou le membre sélectionné " "en a déjà quitté la rédaction."
                    ).format(_type[0]),
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
                self.request, _("Vous avez enlevé {} de la liste des auteurs de {}.").format(authors_list, _type[0])
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
