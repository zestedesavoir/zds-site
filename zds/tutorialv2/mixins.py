from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse, HttpResponsePermanentRedirect, StreamingHttpResponse
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, FormView, View

from zds.forum.models import Topic
from zds.tutorialv2.models.database import ContentRead, PublishableContent, PublishedContent
from zds.tutorialv2.models.help_requests import HelpWriting
from zds.tutorialv2.utils import mark_read
from zds.utils.misc import is_ajax


class SingleContentViewMixin:
    """
    Base mixin to get only one content, and its corresponding versioned content

    Deals with URL resolution in the following way:

    1. In ``get_object()``:
        - Fetch the ``PublishableContent`` according to ``self.kwargs['pk']``, ``self.request.GET['pk']`` or \
        ``self.request.POST['pk']`` (one of these have to be defined). Raise `Http404` if any.
        - Then, check permissions with respect to ``self.must_be_author`` and ``self.authorized_for_staff`` \
         (and define ``self.is_staff`` and ``self.is_author``). Raise ``PermissionDenied`` if any.

    2. In ``get_versioned_object()``:
        - Deal with sha : assume ``self.object.sha_draft`` by default, but reset according to \
        ``self.request.GET['version']``, if exists. \
        - Fetch the ``VersionedContent``. Due to  the use of ``self.object.load_version_or_404(sha)``,\
        raise ``Http404``.
        - Check if it's the beta or public version, and allow access if it's the case. Raise ``PermissionDenied``.
        - Check slug if ``self.kwargs['slug']`` is defined. Raise ``Http404`` if any.

    3. In ``get_public_object()``, fetch the last published version, if any

    Any redefinition of any of these two functions should take care of those points.
    """

    object = None
    versioned_object = None
    public_content_object = None

    prefetch_all = True
    sha = None
    must_be_author = True
    authorized_for_staff = True
    is_staff = False
    is_author = False
    must_redirect = False
    public_is_prioritary = True

    def get_object(self, queryset=None):
        """Get database representation of the content by its `pk`, then check permissions"""

        # fetch object:
        try:
            if "pk" in self.kwargs:
                pk = int(self.kwargs["pk"])
            elif "pk" in self.request.GET:
                pk = int(self.request.GET["pk"])
            elif "pk" in self.request.POST:
                pk = int(self.request.POST["pk"])
            else:
                raise Http404("Impossible de trouver le paramètre 'pk'.")
        except ValueError as badvalue:
            raise Http404(f"La valeur du paramètre pk '{badvalue}' n'est pas un entier valide.")

        queryset = queryset or PublishableContent.objects

        if self.prefetch_all:
            queryset = queryset.select_related("licence").prefetch_related("authors").prefetch_related("subcategory")
        obj = queryset.filter(pk=pk).first()

        if not obj:
            raise Http404("Aucun contenu ne possède cet identifiant.")

        # check permissions:
        self.is_staff = self.request.user.has_perm("tutorialv2.change_publishablecontent")
        self.is_author = self.request.user in obj.authors.all()

        if self.must_be_author and not self.is_author:
            if not self.authorized_for_staff or (self.authorized_for_staff and not self.is_staff):
                raise PermissionDenied

        return obj

    def get_versioned_object(self):
        """Gets the asked version of current content."""

        self.sha = self._get_sha()

        # if beta or public version, user can also access to it
        is_beta = self.object.is_beta(self.sha)
        is_public = self.object.is_public(self.sha) and self.public_is_prioritary

        if not is_beta and not is_public and not self.is_author:
            if not self.is_staff or (not self.authorized_for_staff and self.must_be_author):
                raise PermissionDenied

        # load versioned file
        versioned = self.object.load_version_or_404(self.sha)
        versioned.current_version = self.sha

        # check slug, if any:
        if "slug" in self.kwargs:
            slug = self.kwargs["slug"]
            if versioned.slug != slug:
                if slug != self.object.slug:  # retro-compatibility, but should raise permanent redirect instead
                    raise Http404("Ce slug n'existe pas pour ce contenu.")

        return versioned

    def _get_sha(self):
        if self.sha:
            return self.sha
        elif "version" in self.request.GET:
            return self.request.GET["version"]
        elif "version" in self.request.POST:
            return self.request.POST["version"]
        elif "version" in self.kwargs:
            return self.kwargs["version"]
        else:
            return self.object.sha_draft

    def get_public_object(self):
        """Get the published version, if any"""

        object = PublishedContent.objects.filter(content_pk=self.object.pk, must_redirect=False).last()
        if object:
            object.load_public_version()
        return object


class SingleContentPostMixin(SingleContentViewMixin):
    """
    Base mixin used to get content from post query
    """

    # represent the fact that we have to check if the version given in self.request.POST['version'] exists
    versioned = True

    def get_object(self, queryset=None):
        self.object = super().get_object()

        if self.versioned and "version" in self.request.POST["version"]:
            self.object.load_version_or_404(sha=self.request.POST["version"])
        return self.object


class ModalFormView(FormView):
    """If `self.modal_form` is set `True`, this class will ensure that the redirection is made to the previous page
    if an error appear"""

    modal_form = False  # `form_invalid()` will behave differently if `True`, see implementation below

    def form_invalid(self, form):
        """If `self.modal_form` is set `True`, this function is rewritten to send back to the previous page
        with an error message, instead of using the form template which is normally provided.

        The redirection is made to `form.previous_page_url`, if exists, `content:view` otherwise."""

        if not self.modal_form:
            return super().form_invalid(form)
        else:
            errors = form.errors.as_data()
            if len(errors) > 0:
                # only the first error is provided
                error_message = list(errors.values())[0][0].messages[0]
                messages.error(self.request, error_message)
            else:
                messages.error(self.request, _("Une erreur inconnue est survenue durant le traitement des données."))

            if hasattr(form, "previous_page_url"):
                return redirect(form.previous_page_url)
            else:
                return redirect(reverse("content:view"))  # assume a default url


class FormWithPreview(FormView):
    def post(self, request, *args, **kwargs):
        form = self.get_form()

        if "preview" in request.POST:
            self.form_invalid(form)
            if is_ajax(self.request):
                content = render_to_string("misc/preview.part.html", {"text": request.POST.get("text")})
                return StreamingHttpResponse(content)

        return super().post(request, *args, **kwargs)


class SingleContentFormViewMixin(SingleContentViewMixin, ModalFormView):
    """
    This enhanced FormView ensure,

    - by surcharging `dispatch()`, that:
        * `self.object` contains the result of `get_object()` (as for DetailView)
        * `self.versioned_object` contains the results of `get_versioned_object()`
    - by surcharging `get_context_data()`, that
        * context['content'] contains `self.versioned_object`
    """

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.versioned_object = self.get_versioned_object()
        if self.object.sha_public:
            self.public_content_object = self.get_public_object()

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["content"] = self.versioned_object
        context["is_staff"] = self.is_staff
        return context


class SingleContentDetailViewMixin(SingleContentViewMixin, DetailView):
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not self.sha:
            try:
                self.sha = kwargs["version"]
            except KeyError:
                self.sha = self.object.sha_draft

        self.versioned_object = self.get_versioned_object()
        if self.object.sha_public:
            self.public_content_object = self.get_public_object()

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["helps"] = list(HelpWriting.objects.all())
        context["content_helps"] = list(self.object.helps.all())
        context["content"] = self.versioned_object
        context["db_content"] = self.object
        context["can_edit"] = self.is_author
        context["is_staff"] = self.is_staff
        context["version"] = self.sha
        context["beta_topic"] = self.object.beta_topic
        return context


class ContentTypeMixin:
    """This class deals with the type of contents and fill context according to that"""

    current_content_type = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        v_type_name = _("contenu")
        v_type_name_plural = _("contenus")

        if self.current_content_type == "ARTICLE":
            v_type_name = _("article")
            v_type_name_plural = _("articles")

        if self.current_content_type == "TUTORIAL":
            v_type_name = _("tutoriel")
            v_type_name_plural = _("tutoriels")

        if self.current_content_type == "OPINION":
            v_type_name = _("billet")
            v_type_name_plural = _("billets")

        context["current_content_type"] = self.current_content_type
        context["verbose_type_name"] = v_type_name
        context["verbose_type_name_plural"] = v_type_name_plural

        return context


class MustRedirect(Exception):
    """Exception raised when this is not the last version of the content which is called"""

    def __init__(self, url, *args, **kwargs):
        """
        initialize the exception

        :param url: the targetted url
        :param args: exception *args
        :param kwargs: exception **kwargs
        """
        super().__init__(*args, **kwargs)
        self.url = url


class SingleOnlineContentViewMixin(ContentTypeMixin):
    """
    Base mixin to get only one content online content

    Deals with URL resolution in the following way:

    1. In `get_object()`:
        - Fetch the ``PublicContent`` according to ``self.kwargs['pk']``, ``self.request.GET['pk']`` or \
        ``self.request.POST['pk']`` 0(one of these have to be defined). Raise ``Http404`` if any.
        - Check if ``self.current_content_type`` if defined, and use it if it's the case
        - Check if ``slug`` is defined, also check object it if it's the case
        - Then, define ``self.is_staff`` and ``self.is_author``.
    2. In ``get_versioned_object()``: Fetch the ``VersionedContent``. Due to  the use of
        ``self.public_content_object.load_public_version_or_404()``, raise ``Http404`` if any.

    Any redefinition of any of these two functions should take care of those points.

    """

    object = None
    public_content_object = None
    versioned_object = None
    redirection_is_needed = True

    is_author = False
    is_staff = False

    def get_redirect_url(self, public_version):
        """Return the most recent url, based on the current public version"""
        return public_version.content.public_version.get_absolute_url_online()

    def get_public_object(self):
        try:
            if "pk" in self.kwargs:
                pk = int(self.kwargs["pk"])
            elif "pk" in self.request.GET:
                pk = int(self.request.GET["pk"])
            elif "pk" in self.request.POST:
                pk = int(self.request.POST["pk"])
            else:
                raise Http404("Impossible de trouver le paramètre 'pk'.")
        except ValueError as badvalue:
            raise Http404(f"La valeur du paramètre pk '{badvalue}' n'est pas un entier valide.")
        queryset = (
            PublishedContent.objects.filter(content_pk=pk)
            .prefetch_related("content")
            .prefetch_related("content__authors")
            .prefetch_related("content__subcategory")
            .prefetch_related("content__tags")
            .prefetch_related("content__public_version")
            .select_related("content__last_note")
        )

        if self.current_content_type:
            queryset = queryset.filter(content_type=self.current_content_type)

        if "slug" in self.kwargs:
            queryset = queryset.filter(content_public_slug=self.kwargs["slug"])

        obj = queryset.order_by("publication_date").last()  # 'last' version must be the most recent to be published

        if obj is None:
            raise Http404("Aucun contenu ne possède ce slug.")

        # Redirection ?
        if obj.must_redirect:
            if obj.content.public_version and self.redirection_is_needed:
                raise MustRedirect(self.get_redirect_url(obj))
            elif obj.content.public_version and not self.redirection_is_needed:
                obj = obj.content.public_version
            else:  # should only happen if the content is unpublished
                raise Http404("La redirection est activée mais le contenu n'est pas public.")

        self.is_author = self.request.user in obj.authors.all()
        self.is_staff = self.request.user.has_perm("tutorialv2.change_publishablecontent")

        self.current_content_type = obj.content_type
        if obj and obj.content.last_note:
            mark_read(obj.content, self.request.user)
        return obj

    def get_object(self):
        obj = self.public_content_object.content
        if obj is None:
            raise Http404("Le contenu de la publication n'est pas trouvé.")
        return obj

    def get_versioned_object(self):
        return self.public_content_object.load_public_version_or_404()


class SingleOnlineContentDetailViewMixin(SingleOnlineContentViewMixin, DetailView):
    """
    This enhanced DetailView ensures,

    - by rewriting `get()`, that:
        * `self.object` contains the result of `get_object()` (as it must be if `get()` was not rewritten)
        * Redirection is made if we catch `MustRedirect`
        * `self.versioned_object` contains a PublicContent object
        * `self.public_content_object` contains a PublishedContent object
    - by surcharging `get_context_data()`, that
        * context['content'] is set
        * context['is_staff'] is set
        * context['can_edit'] is set
        * context['public_object'] is set
        * context['is_antispam'] is set
        * context['db_content'] is set with the PublishableContent instance
    """

    def get(self, request, *args, **kwargs):
        try:
            self.public_content_object = self.get_public_object()
        except MustRedirect as redirection_url:
            return HttpResponsePermanentRedirect(redirection_url.url)

        self.object = self.get_object()
        self.versioned_object = self.get_versioned_object()
        context = self.get_context_data(object=self.object)
        follow = ContentRead.objects.filter(user__pk=self.request.user.pk).filter(content__pk=self.object.pk).first()
        if follow is not None:
            follow.note = self.object.last_note
            follow.save()

        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["content"] = self.versioned_object
        context["is_obsolete"] = self.object.is_obsolete
        context["public_object"] = self.public_content_object
        context["can_edit"] = self.request.user in self.object.authors.all()
        context["is_staff"] = self.is_staff
        context["is_author"] = self.is_author
        context["db_content"] = self.object
        return context


class SingleOnlineContentFormViewMixin(SingleOnlineContentViewMixin, ModalFormView):
    """
    This enhanced FormView ensure,

    - by surcharging `dispatch()`, that:
        * `self.public_content_object` contains a PublishedContent object
        * `self.object` contains the result of `get_object()` (as for DetailView)
        * `self.versioned_object` contains the results of `get_versioned_object()`
    - by surcharging `get_context_data()`, that
        * context['content'] is set
        * context['public_object'] is set


    Note: does not catch `MustRedirect`, so you should not use a `slug` with POST request
    """

    denied_if_lock = False  # denied the use of the form if the content is locked

    def dispatch(self, request, *args, **kwargs):
        self.public_content_object = self.get_public_object()
        self.object = self.get_object()
        self.versioned_object = self.get_versioned_object()

        if self.denied_if_lock and self.object.is_locked:
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["content"] = self.versioned_object
        context["public_object"] = self.public_content_object

        return context


class DownloadViewMixin(View):
    """Basic View to return a file to download

    (inspired from https://djangosnippets.org/snippets/2549/ and
    http://stackoverflow.com/questions/16286666/send-a-file-through-django-class-based-views)

    You just need to override `get_contents()` to make it works
    """

    mimetype = None
    filename = None

    def get_mimetype(self):
        return self.mimetype

    def get_filename(self):
        return self.filename

    def get_contents(self):
        pass

    def get(self, context, **response_kwargs):
        """
        Access to a file with only get method then write the file content in response stream.
        Properly sets Content-Type and Content-Disposition headers
        """
        response = HttpResponse(content_type=self.get_mimetype())
        response["Content-Disposition"] = "filename=" + self.get_filename()
        response.write(self.get_contents())

        return response


class SingleContentDownloadViewMixin(SingleContentViewMixin, DownloadViewMixin):
    """
    Ensure, by rewritring ``get()``, that
    - `self.object` contains the result of `get_object()` (as it must be if `get()` is not rewritten)
    - `self.sha` is set according to `self.request.GET['version']` (if any) and `self.object.sha_draft` otherwise
    - `self.versioned_object` contains the results of `get_versioned_object()`
    """

    def get(self, context, **response_kwargs):
        self.object = self.get_object()

        if not self.sha:
            try:
                self.sha = self.request.GET["version"]
            except KeyError:
                self.sha = self.object.sha_draft

        self.versioned_object = self.get_versioned_object()

        return super().get(context, **response_kwargs)


class RequiresValidationViewMixin(SingleContentDetailViewMixin):
    """
    Ensure the content require validation before publication.
    """

    def get(self, request, *args, **kwargs):
        if not self.get_object().requires_validation():
            raise PermissionDenied
        return super().get(request, *args, **kwargs)


class DoesNotRequireValidationFormViewMixin(SingleContentFormViewMixin):
    """
    Ensure the content do not require validation before publication.
    """

    def get_form_kwargs(self):
        if self.versioned_object.requires_validation():
            raise PermissionDenied
        return super().get_form_kwargs()
