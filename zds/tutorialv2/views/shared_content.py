from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from zds.tutorialv2.mixins import ContentTypeMixin
from zds.tutorialv2.models.shareable_links import ShareableLink
from zds.tutorialv2.utils import search_container_or_404


class DisplaySharedContentMixin:
    """
    Base behavior for DisplaySharedContent and DisplaySharedContainer.
    Modify this mixin to change what is common to DisplaySharedContent and DisplaySharedContainer.
    """

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.link = get_object_or_404(ShareableLink, id=kwargs["id"])
        if not self.link.active:
            raise PermissionDenied
        self.content = self.link.content
        self.versioned_content = self.content.load_version_or_404(sha=self.content.sha_draft)

    def get_context_data(self, **kwargs):
        kwargs["link"] = self.link
        kwargs["content"] = self.versioned_content
        return super().get_context_data(**kwargs)


class DisplaySharedContent(DisplaySharedContentMixin, ContentTypeMixin, TemplateView):
    """View a shared version of a content (main page)."""

    template_name = "tutorialv2/view/shared_content.html"


class DisplaySharedContainer(DisplaySharedContentMixin, ContentTypeMixin, TemplateView):
    """View a shared version of a content (subpage)."""

    template_name = "tutorialv2/view/shared_container.html"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.container = search_container_or_404(self.versioned_content, self.kwargs)

    def get_context_data(self, **kwargs):
        kwargs["container"] = self.container
        return super().get_context_data(**kwargs)
