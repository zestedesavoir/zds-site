from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from zds.tutorialv2.forms import WarnTypoForm
from zds.tutorialv2.mixins import SingleContentDetailViewMixin, SingleOnlineContentDetailViewMixin
from zds.tutorialv2.models.database import PublishableContent
from zds.tutorialv2.utils import get_target_tagged_tree, search_container_or_404
from zds.tutorialv2.views.display.config import (
    ConfigForBetaView,
    ConfigForContainerDraftView,
    ConfigForOnlineView,
    ConfigForValidationView,
    ConfigForVersionView,
)


class Item:
    def __init__(self, title, url):
        self.title = title
        self.url = url


class BreadcrumbItem(Item):
    pass


class Breadcrumbs:
    def __init__(self, base_url=""):
        self.items = []
        self.base_url = base_url

    def add_item(self, container):
        item = BreadcrumbItem(container.title, container.get_url_path(self.base_url))
        self.items.append(item)


class PagerItem(Item):
    pass


class Pager:
    def __init__(self, has_pagination, base_url=""):
        self.has_pagination = has_pagination
        self.base_url = base_url
        self.previous = None
        self.next = None

    def add_previous(self, container):
        self.previous = PagerItem(
            container.title,
            container.get_url_path(self.base_url),
        )

    def add_next(self, container):
        self.next = PagerItem(
            container.title,
            container.get_url_path(self.base_url),
        )


class ContainerBaseView(SingleContentDetailViewMixin):
    model = PublishableContent
    template_name = "tutorialv2/view/container.html"
    sha = None
    must_be_author = False
    warn_typo_public = True

    def get_context_data(self, **kwargs):
        """Show the given tutorial if exists."""
        context = super().get_context_data(**kwargs)
        context["base_url"] = self.get_base_url()
        container = search_container_or_404(self.versioned_object, self.kwargs)
        context["breadcrumb_items"] = self.get_breadcrumbs(container)
        context["containers_target"] = get_target_tagged_tree(container, self.versioned_object)
        context["form_warn_typo"] = WarnTypoForm(
            self.versioned_object,
            container,
            public=self.warn_typo_public,
            initial={"target": container.get_path(relative=True)},
        )
        context["container"] = container
        context["pm_link"] = self.object.get_absolute_contact_url(_("À propos de"))
        context["pager"] = self.get_pager(container)
        context["is_js"] = self.object.js_support
        return context

    def get_breadcrumbs(self, container, breadcrumbs=None):
        if breadcrumbs is None:
            breadcrumbs = Breadcrumbs(base_url=self.get_base_url())
            return self.get_breadcrumbs(container, breadcrumbs)
        else:
            breadcrumbs.add_item(container)
            if container.parent is not None:
                self.get_breadcrumbs(container.parent, breadcrumbs)
            return reversed(breadcrumbs.items)

    def get_pager(self, container):
        containers = self.versioned_object.get_list_of_containers()
        if container not in containers:
            pager = Pager(has_pagination=False)
        else:
            pager = Pager(has_pagination=True, base_url=self.get_base_url())
            position = containers.index(container)
            container_is_first = position == 0
            container_is_last = position == len(containers) - 1
            if not container_is_first:
                pager.add_previous(containers[position - 1])
            if not container_is_last:
                pager.add_next(containers[position + 1])
        return pager

    def get_base_url(self):
        raise NotImplementedError


class ContainerDraftView(LoginRequiredMixin, ContainerBaseView):
    """Show the draft page of a container."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        container = search_container_or_404(self.versioned_object, self.kwargs)
        context["form_warn_typo"] = WarnTypoForm(
            self.versioned_object, container, initial={"target": container.get_path(relative=True)}
        )
        context["display_config"] = ConfigForContainerDraftView(self.request.user, self.object, self.versioned_object)
        return context

    def get_base_url(self):
        route_parameters = {"pk": self.object.pk, "slug": self.object.slug}
        url = reverse("content:view", kwargs=route_parameters)
        return url


class ContainerVersionView(ContainerBaseView):
    """Show the page for a specific version of a container."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["display_config"] = ConfigForVersionView(self.request.user, self.object, self.versioned_object)
        return context

    def get_base_url(self):
        route_parameters = {"pk": self.object.pk, "slug": self.object.slug, "version": self.sha}
        url = reverse("content:view-version", kwargs=route_parameters)
        return url


class ContainerOnlineView(SingleOnlineContentDetailViewMixin, ContainerBaseView):
    """Show the online page of a container."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["display_config"] = ConfigForOnlineView(self.request.user, self.object, self.versioned_object)
        return context

    def get_base_url(self):
        return self.object.get_absolute_url_online()


class ContainerBetaView(LoginRequiredMixin, ContainerBaseView):
    """Show the beta page of a container."""

    sha = None
    warn_typo_public = False

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)

        if not obj.sha_beta:
            raise Http404("Aucune bêta n'existe pour ce contenu.")
        else:
            self.sha = obj.sha_beta

        # make the slug always right in URLs resolution:
        if "slug" in self.kwargs:
            self.kwargs["slug"] = obj.slug

        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["display_config"] = ConfigForBetaView(self.request.user, self.object, self.versioned_object)
        return context

    def get_base_url(self):
        route_parameters = {"pk": self.object.pk, "slug": self.object.slug}
        url = reverse("content:beta-view", kwargs=route_parameters)
        return url


class ContainerValidationView(LoginRequiredMixin, ContainerBaseView):
    """Show the validation page of a container."""

    sha = None
    warn_typo_public = False

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)

        if not obj.sha_validation:
            raise Http404("Aucune version en validation n'existe pour ce contenu.")
        else:
            self.sha = obj.sha_validation

        # make the slug always right in URLs resolution:
        if "slug" in self.kwargs:
            self.kwargs["slug"] = obj.slug

        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["display_config"] = ConfigForValidationView(self.request.user, self.object, self.versioned_object)
        return context

    def get_base_url(self):
        route_parameters = {"pk": self.object.pk, "slug": self.object.slug}
        url = reverse("content:validation-view", kwargs=route_parameters)
        return url
