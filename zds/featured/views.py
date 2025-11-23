from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic import CreateView, DeleteView, FormView, RedirectView, UpdateView
from django.views.generic.list import MultipleObjectMixin

from zds import json_handler
from zds.featured.forms import FeaturedMessageForm, FeaturedResourceForm
from zds.featured.models import FEATUREABLES, FeaturedMessage, FeaturedRequested, FeaturedResource
from zds.forum.models import Topic
from zds.tutorialv2.models.database import PublishableContent
from zds.utils.paginator import ZdSPagingListView


class FeaturedViewMixin(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = "featured.change_featuredresource"
    raise_exception = True


class FeaturedResourceList(FeaturedViewMixin, ZdSPagingListView):
    """
    Displays the list of featured resources.
    """

    context_object_name = "featured_resource_list"
    paginate_by = settings.ZDS_APP["featured_resource"]["featured_per_page"]
    queryset = FeaturedResource.objects.all().order_by("-pubdate")
    template_name = "featured/index.html"

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class FeaturedResourceCreate(FeaturedViewMixin, CreateView):
    """
    Creates a new featured resource.
    """

    form_class = FeaturedResourceForm
    template_name = "featured/resource/create.html"
    context_object_name = "featured_resource"
    initial_error_message = _("Le contenu est introuvable")
    displayed_content_type = {
        "TUTORIAL": _("Un tutoriel"),
        "ARTICLE": _("Un article"),
        "OPINION": _("Un billet"),
        "TOPIC": _("Un sujet"),
    }

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_initial_topic_data(self, topic_id):
        try:
            content = Topic.objects.get(pk=int(topic_id))
        except (Topic.DoesNotExist, ValueError):
            messages.error(self.request, self.initial_error_message)
            return {}
        initial = {
            "title": content.title,
            "type": self.displayed_content_type["TOPIC"],
            "authors": str(content.author),
            "url": self.request.build_absolute_uri(content.get_absolute_url()),
        }

        featured_request = FeaturedRequested.objects.get_existing(content)
        if featured_request is not None:
            initial.update({"request": featured_request.pk})

        return initial

    def get_initial_content_data(self, content_id):
        try:
            content = PublishableContent.objects.get(pk=int(content_id)).public_version
            if not content:
                raise ValueError("Not a public content")
        except (PublishableContent.DoesNotExist, ValueError):
            messages.error(self.request, self.initial_error_message)
            return {}
        displayed_authors = ", ".join([str(x) for x in content.authors.all()])
        if content.content.image:
            image_url = self.request.build_absolute_uri(content.content.image.physical["featured"].url)
        else:
            image_url = None

        return {
            "title": content.title(),
            "type": self.displayed_content_type[content.content_type],
            "authors": displayed_authors,
            "url": self.request.build_absolute_uri(content.content.get_absolute_url_online()),
            "image_url": self.request.build_absolute_uri(image_url),
        }

    def get_initial(self):
        initial = super().get_initial()
        content_type = self.request.GET.get("content_type", None)
        content_id = self.request.GET.get("content_id", None)
        if content_type == "topic" and content_id:
            initial.update(**self.get_initial_topic_data(content_id))
        elif content_type == "published_content" and content_id:
            initial.update(**self.get_initial_content_data(content_id))
        return initial

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["hide_major_update_field"] = True
        return kw

    def form_valid(self, form):
        featured_resource = FeaturedResource()
        featured_resource.title = form.cleaned_data.get("title")
        featured_resource.type = form.cleaned_data.get("type")
        featured_resource.authors = form.cleaned_data.get("authors")
        featured_resource.image_url = form.cleaned_data.get("image_url")
        featured_resource.url = form.cleaned_data.get("url")

        if form.cleaned_data.get("major_update", False):
            featured_resource.pubdate = datetime.now()
        else:
            featured_resource.pubdate = form.cleaned_data.get("pubdate")

        featured_resource.save()

        if form.cleaned_data.get("request") is not None:
            try:
                featured_request = FeaturedRequested.objects.get(pk=form.cleaned_data["request"])
                featured_request.featured = featured_resource
                featured_request.save()
            except FeaturedRequested.DoesNotExist:
                pass

        messages.success(self.request, _("La une a été créée."))
        return redirect(reverse("featured:resource-list"))


class FeaturedResourceUpdate(FeaturedViewMixin, UpdateView):
    """
    Updates a featured resource.
    """

    form_class = FeaturedResourceForm
    template_name = "featured/resource/update.html"
    queryset = FeaturedResource.objects.all()
    context_object_name = "featured_resource"

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial.update(
            {
                "title": self.object.title,
                "type": self.object.type,
                "authors": self.object.authors,
                "image_url": self.object.image_url,
                "url": self.object.url,
                "pubdate": self.object.pubdate,
            }
        )

        return initial

    def form_valid(self, form):
        self.object.title = form.cleaned_data.get("title")
        self.object.type = form.cleaned_data.get("type")
        self.object.authors = form.cleaned_data.get("authors")
        self.object.image_url = form.cleaned_data.get("image_url")
        self.object.url = form.cleaned_data.get("url")
        if form.cleaned_data.get("major_update", False):
            self.object.pubdate = datetime.now()
        else:
            self.object.pubdate = form.cleaned_data.get("pubdate")

        messages.success(self.request, _("La une a été mise à jour."))
        self.success_url = reverse("featured:resource-list")
        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.helper.form_action = reverse("featured:resource-update", args=[self.object.pk])
        return form


class FeaturedResourceDeleteDetail(FeaturedViewMixin, DeleteView):
    """
    Deletes a featured resource.
    """

    model = FeaturedResource

    def dispatch(self, request, *args, **kwargs):
        self.success_url = reverse("featured:resource-list")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        r = super().post(request, *args, **kwargs)
        messages.success(request, _("La une a été supprimée avec succès."))
        return r


class FeaturedResourceDeleteList(FeaturedViewMixin, MultipleObjectMixin, RedirectView):
    """
    Deletes a list of featured resources.
    """

    permanent = False

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        items_list = self.request.POST.getlist("items")
        return FeaturedResource.objects.filter(pk__in=items_list)

    def post(self, request, *args, **kwargs):
        for featured_resource in self.get_queryset():
            featured_resource.delete()

        messages.success(request, _("Les unes ont été supprimées avec succès."))

        return redirect(reverse("featured:resource-list"))


class FeaturedRequestedList(FeaturedViewMixin, ZdSPagingListView):
    """
    Displays the list of featured resources.
    """

    context_object_name = "featured_request_list"
    paginate_by = settings.ZDS_APP["featured_resource"]["request_per_page"]
    template_name = "featured/list_requests.html"

    def get_queryset(self):
        type_featured_request = self.request.GET.get("type")

        queryset = (
            FeaturedRequested.objects.prefetch_related("content_object")
            .filter(rejected_for_good=False)
            .annotate(num_vote=Count("users_voted"))
            .filter(num_vote__gt=0)
            .order_by("-num_vote")
            .filter(rejected=type_featured_request == "ignored")
            .filter(featured__isnull=type_featured_request != "accepted")
        )

        if type_featured_request in FEATUREABLES.keys():
            queryset = queryset.filter(type=FEATUREABLES[type_featured_request]["name"])

        return [q for q in queryset.all() if isinstance(q.content_object, Topic) or not q.content_object.is_obsolete]

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class FeaturedRequestedUpdate(UpdateView):
    model = FeaturedRequested
    http_method_names = ["post"]

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        result = {"result": "FAIL"}

        if "operation" in request.POST:
            if "REJECT" in request.POST["operation"]:
                obj.rejected = True
                obj.save()
                result = {"result": "OK"}
            if "REJECT_FOR_GOOD" in request.POST["operation"]:
                obj.rejected = True
                obj.rejected_for_good = True
                obj.save()
                result = {"result": "OK"}
            elif "CONSIDER" in request.POST["operation"]:
                obj.rejected = False
                obj.save()
                result = {"result": "OK"}

        return HttpResponse(json_handler.dumps(result), content_type="application/json")


class FeaturedMessageCreateUpdate(FeaturedViewMixin, FormView):
    """
    Creates or updates the featured message.
    """

    form_class = FeaturedMessageForm
    template_name = "featured/message/create.html"
    last_message = None

    def dispatch(self, request, *args, **kwargs):
        self.last_message = FeaturedMessage.objects.get_last_message()
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        init = super().get_initial()

        if self.last_message is not None:
            init.update(
                {
                    "hook": self.last_message.hook,
                    "message": self.last_message.message,
                    "url": self.last_message.url,
                }
            )

        return init

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["display_delete_button"] = self.last_message is not None
        return context

    def form_valid(self, form):
        if self.last_message:
            self.last_message.delete()

        featured_message = FeaturedMessage()
        featured_message.hook = form.data.get("hook")
        featured_message.message = form.data.get("message")
        featured_message.url = form.data.get("url")
        featured_message.save()

        messages.success(self.request, _("Le message a été changé"))
        return redirect(reverse("featured:resource-list"))


class FeaturedMessageDelete(FeaturedViewMixin, DeleteView):
    """Delete the featured message."""

    http_method_names = ["post"]
    model = FeaturedMessage

    def get_object(self, queryset=None):
        return FeaturedMessage.objects.get_last_message()

    def form_valid(self, form):
        if self.object is not None:
            self.object.delete()
        messages.success(self.request, _("Le message a été supprimé."))
        return redirect(reverse("featured:resource-list"))
