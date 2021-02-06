from collections import OrderedDict

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.text import format_lazy
from django.utils.translation import ugettext_lazy as _

from zds.member.decorator import LoggedWithReadWriteHability
from zds.notification.models import NewPublicationSubscription
from zds.tutorialv2.forms import ContributionForm, RemoveContributionForm
from zds.tutorialv2.mixins import SingleContentFormViewMixin
from zds.tutorialv2.models import TYPE_CHOICES_DICT
from zds.tutorialv2.models.database import ContentContribution, PublishableContent
from zds.utils.mps import send_mp
from zds.utils.paginator import ZdSPagingListView


class AddContributorToContent(LoggedWithReadWriteHability, SingleContentFormViewMixin):
    only_draft_version = True
    must_be_author = True
    form_class = ContributionForm
    authorized_for_staff = True

    def get_form_kwargs(self):
        kwargs = super(AddContributorToContent, self).get_form_kwargs()
        kwargs.update({"content": self.object})
        return kwargs

    def get(self, request, *args, **kwargs):
        content = self.get_object()
        url = "content:find-{}".format("tutorial" if content.is_tutorial() else content.type.lower())
        return redirect(url, self.request.user)

    def form_valid(self, form):

        _type = _("à l'article")

        if self.object.is_tutorial:
            _type = _("au tutoriel")
        elif self.object.is_opinion:
            raise PermissionDenied

        bot = get_object_or_404(User, username=settings.ZDS_APP["member"]["bot_account"])
        all_authors_pk = [author.pk for author in self.object.authors.all()]
        user = form.cleaned_data["user"]
        if user.pk in all_authors_pk:
            messages.error(self.request, _("Un auteur ne peut pas être désigné comme contributeur"))
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
                        'contributeurs {} avec pour rôle "{}"'.format(_type, contribution_role.title)
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
                format_lazy("{} {}", _("Contribution"), _type),
                self.versioned_object.title,
                render_to_string(
                    "tutorialv2/messages/add_contribution_pm.md",
                    {
                        "content": self.object,
                        "type": _type,
                        "url": self.object.get_absolute_url(),
                        "index": url_index,
                        "user": user.username,
                        "role": contribution.contribution_role.title,
                    },
                ),
                send_by_mail=True,
                direct=False,
                leave=True,
            )
            self.success_url = self.object.get_absolute_url()

            return super(AddContributorToContent, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, form.errors)
        self.success_url = self.object.get_absolute_url()
        return super(AddContributorToContent, self).form_valid(form)


class RemoveContributorFromContent(LoggedWithReadWriteHability, SingleContentFormViewMixin):

    form_class = RemoveContributionForm
    only_draft_version = True
    must_be_author = True
    authorized_for_staff = True

    def form_valid(self, form):
        _type = _("cet article")
        if self.object.is_tutorial:
            _type = _("ce tutoriel")
        elif self.object.is_opinion:
            raise PermissionDenied

        contribution = get_object_or_404(ContentContribution, pk=form.cleaned_data["pk_contribution"])
        user = contribution.user
        contribution.delete()

        messages.success(
            self.request, _("Vous avez enlevé {} de la liste des contributeurs de {}.").format(user.username, _type)
        )
        self.success_url = self.object.get_absolute_url()

        return super(RemoveContributorFromContent, self).form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _("Les contributeurs sélectionnés n'existent pas."))
        self.success_url = self.object.get_absolute_url()
        return super(RemoveContributorFromContent, self).form_valid(form)


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
        return super(ContentOfContributors, self).dispatch(request, *args, **kwargs)

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
        context = super(ContentOfContributors, self).get_context_data(**kwargs)
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
