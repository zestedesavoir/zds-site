from collections import OrderedDict

from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Layout
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from zds.member.decorator import LoggedWithReadWriteHability
from zds.member.models import Profile
from zds.member.utils import get_bot_account
from zds.mp.utils import send_mp
from zds.notification.models import NewPublicationSubscription
from zds.tutorialv2 import signals
from zds.tutorialv2.forms import ReviewerTypeModelChoiceField
from zds.tutorialv2.mixins import SingleContentFormViewMixin
from zds.tutorialv2.models import TYPE_CHOICES_DICT
from zds.tutorialv2.models.database import ContentContribution, ContentContributionRole, PublishableContent
from zds.utils.paginator import ZdSPagingListView


class ContributionForm(forms.Form):
    contribution_role = ReviewerTypeModelChoiceField(
        label=_("Role"),
        required=True,
        queryset=ContentContributionRole.objects.order_by("title").all(),
    )

    username = forms.CharField(
        label=_("Contributeur"),
        required=True,
        widget=forms.TextInput(
            attrs={"placeholder": _("Pseudo du membre à ajouter."), "data-autocomplete": "{ 'type': 'single' }"}
        ),
    )

    comment = forms.CharField(
        label=_("Commentaire"),
        required=False,
        widget=forms.Textarea(attrs={"placeholder": _("Commentaire sur ce contributeur."), "rows": "3"}),
    )

    def __init__(self, content, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_class = "modal modal-flex"
        self.helper.form_id = "add-contributor"
        self.helper.form_method = "post"
        self.helper.form_action = reverse("content:add-contributor", kwargs={"pk": content.pk})
        self.helper.layout = Layout(
            Field("username"),
            Field("contribution_role"),
            Field("comment"),
            StrictButton(_("Ajouter"), type="submit", css_class="btn-submit"),
        )
        super().__init__(*args, **kwargs)

    def clean_username(self):
        cleaned_data = super().clean()
        if cleaned_data.get("username"):
            username = cleaned_data.get("username")
            user = Profile.objects.contactable_members().filter(user__username__iexact=username.strip().lower()).first()
            if user is not None:
                cleaned_data["user"] = user.user
            else:
                self._errors["user"] = self.error_class([_("L'utilisateur sélectionné n'existe pas")])

        if "user" not in cleaned_data:
            self._errors["user"] = self.error_class([_("Veuillez renseigner l'utilisateur")])

        return cleaned_data


class AddContributorToContent(LoggedWithReadWriteHability, SingleContentFormViewMixin):
    must_be_author = True
    form_class = ContributionForm
    authorized_for_staff = True

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"content": self.object})
        return kwargs

    def get(self, request, *args, **kwargs):
        content = self.get_object()
        url = "content:find-{}".format("tutorial" if content.is_tutorial() else content.type.lower())
        return redirect(url, self.request.user)

    def form_valid(self, form):
        bot = get_bot_account()
        all_authors_pk = [author.pk for author in self.object.authors.all()]
        user = form.cleaned_data["user"]
        if user.pk in all_authors_pk:
            messages.error(self.request, _("Un auteur ne peut pas être désigné comme contributeur."))
            return redirect(self.object.get_absolute_url())
        else:
            contribution_role = form.cleaned_data.get("contribution_role")
            comment = form.cleaned_data.get("comment")
            if ContentContribution.objects.filter(
                user=user, contribution_role=contribution_role, content=self.object
            ).exists():
                messages.error(
                    self.request,
                    _(
                        "Ce membre fait déjà partie des "
                        'contributeurs à la publication avec pour rôle "{}"'.format(contribution_role.title)
                    ),
                )
                return redirect(self.object.get_absolute_url())

            contribution = ContentContribution(
                user=user, contribution_role=contribution_role, comment=comment, content=self.object
            )
            contribution.save()
            url_index = reverse(self.object.type.lower() + ":find-" + self.object.type.lower(), args=[user.pk])
            send_mp(
                bot,
                [user],
                _("Contribution à la publication"),
                self.versioned_object.title,
                render_to_string(
                    "tutorialv2/messages/add_contribution_pm.md",
                    {
                        "content": self.object,
                        "url": self.object.get_absolute_url(),
                        "index": url_index,
                        "user": user.username,
                        "role": contribution.contribution_role.title,
                    },
                ),
                send_by_mail=True,
                leave=True,
            )
            signals.contributors_management.send(
                sender=self.__class__, content=self.object, performer=self.request.user, contributor=user, action="add"
            )
            self.success_url = self.object.get_absolute_url()

            return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, form.errors)
        self.success_url = self.object.get_absolute_url()
        return super().form_valid(form)


class RemoveContributionForm(forms.Form):
    pk_contribution = forms.CharField(
        label=_("Contributeur"),
        required=True,
    )


class RemoveContributorFromContent(LoggedWithReadWriteHability, SingleContentFormViewMixin):
    form_class = RemoveContributionForm
    must_be_author = True
    authorized_for_staff = True

    def form_valid(self, form):
        contribution = get_object_or_404(ContentContribution, pk=form.cleaned_data["pk_contribution"])
        user = contribution.user
        contribution.delete()
        signals.contributors_management.send(
            sender=self.__class__, content=self.object, performer=self.request.user, contributor=user, action="remove"
        )
        messages.success(
            self.request,
            _("Vous avez enlevé {} de la liste des contributeurs de cette publication.").format(user.username),
        )
        self.success_url = self.object.get_absolute_url()

        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _("Les contributeurs sélectionnés n'existent pas."))
        self.success_url = self.object.get_absolute_url()
        return super().form_valid(form)


class ContentOfContributors(ZdSPagingListView):
    type = "ALL"
    context_object_name = "contribution_contents"
    paginate_by = settings.ZDS_APP["content"]["content_per_page"]
    template_name = "tutorialv2/contributions.html"
    model = PublishableContent

    sorts = OrderedDict(
        [
            ("creation", [lambda q: q.order_by("content__creation_date"), _("Par date de création")]),
            ("abc", [lambda q: q.order_by("content__title"), _("Par ordre alphabétique")]),
            ("modification", [lambda q: q.order_by("-content__update_date"), _("Par date de dernière modification")]),
        ]
    )
    sort = ""
    filter = ""
    user = None

    def dispatch(self, request, *args, **kwargs):
        self.user = get_object_or_404(User, username=self.kwargs["username"])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        if self.type == "ALL":
            queryset = ContentContribution.objects.filter(user__pk=self.user.pk, content__sha_public__isnull=False)
        elif self.type in list(TYPE_CHOICES_DICT.keys()):
            queryset = ContentContribution.objects.filter(
                user__pk=self.user.pk, content__sha_public__isnull=False, content__type=self.type
            )
        else:
            raise Http404("Ce type de contenu est inconnu dans le système.")

        # Sort.
        if "sort" in self.request.GET and self.request.GET["sort"].lower() in self.sorts:
            self.sort = self.request.GET["sort"]
        elif not self.sort:
            self.sort = "abc"
        queryset = self.sorts[self.sort.lower()][0](queryset)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sorts"] = []
        context["sort"] = self.sort.lower()
        context["subscriber_count"] = NewPublicationSubscription.objects.get_subscriptions(self.user).count()
        context["type"] = self.type.lower()
        contents = list(self.object_list.values_list("content", flat=True).distinct())

        queryset = PublishableContent.objects.filter(pk__in=contents)
        # prefetch:
        queryset = (
            queryset.prefetch_related("authors")
            .prefetch_related("subcategory")
            .select_related("licence")
            .select_related("image")
        )

        context["contribution_tutorials"] = queryset.filter(type="TUTORIAL").all()
        context["contribution_articles"] = queryset.filter(type="ARTICLE").all()

        context["usr"] = self.user
        for sort in list(self.sorts.keys()):
            context["sorts"].append({"key": sort, "text": self.sorts[sort][1]})
        return context
