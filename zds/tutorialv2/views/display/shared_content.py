from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse

from zds.tutorialv2.models.database import PublishableContent
from zds.tutorialv2.models.shareable_links import ShareableLink
from zds.tutorialv2.models.versioned import VersionedContent
from zds.tutorialv2.views.display.config import ViewConfig
from zds.tutorialv2.views.display.container import ContainerBaseView
from zds.tutorialv2.views.display.content import ContentBaseView


class ConfigForSharedView(ViewConfig):
    def __init__(self, user, content: PublishableContent, versioned_content: VersionedContent):
        super().__init__(user, content, versioned_content)
        self.beta_actions.enabled = False
        self.draft_actions.enabled = False
        self.online_config.enabled = False
        self.info_config.enabled = False
        self.public_actions.enabled = False
        self.administration_actions.enabled = False
        self.validation_actions.enabled = False


class ContentSharedView(ContentBaseView):
    must_be_author = False
    authorized_for_all = True
    sha = None

    def get_object(self, queryset=None):
        self.link = get_object_or_404(ShareableLink, id=self.kwargs["id"])

        if not self.link.active or self.link.expired():
            raise PermissionDenied

        self.content = self.link.content

        sha = self._get_sha()
        if sha is None:
            raise Http404("This link type cannot be provided by this content.")

        self.versioned_content = self.content.load_version_or_404(sha=sha)

        return self.content

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["display_config"] = ConfigForSharedView(self.request.user, self.object, self.versioned_object)
        context["link"] = self.link
        context["content"] = self.versioned_content
        return context

    def get_base_url(self):
        route_parameters = {"id": self.link.id}
        url = reverse("content:shareable-link-view", kwargs=route_parameters)
        return url

    def _get_sha(self):
        if self.link.type == "DRAFT":
            return self.content.sha_draft
        elif self.link.type == "BETA" and self.content.in_beta():
            return self.content.sha_beta
        else:
            return None


class ContainerSharedView(ContainerBaseView):
    must_be_author = False
    authorized_for_all = True

    def get_object(self, queryset=None):
        self.link = get_object_or_404(ShareableLink, id=self.kwargs["id"])
        if not self.link.active:
            raise PermissionDenied

        self.content = self.link.content

        sha = self._get_sha()
        if sha is None:
            raise Http404("This link type cannot be provided by this content.")

        return self.content

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["display_config"] = ConfigForSharedView(self.request.user, self.object, self.versioned_object)
        return context

    def get_base_url(self):
        route_parameters = {"id": self.link.id}
        url = reverse("content:shareable-link-view", kwargs=route_parameters)
        return url

    def _get_sha(self):
        if self.link.type == "DRAFT":
            return self.content.sha_draft
        elif self.link.type == "BETA" and self.content.in_beta():
            return self.content.sha_beta
        else:
            return None
