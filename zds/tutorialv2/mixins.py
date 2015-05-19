#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.views.generic import View

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse, HttpResponsePermanentRedirect
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.views.generic import DetailView, FormView
from django.utils.translation import ugettext_lazy as _

from zds.tutorialv2.models.models_database import PublishableContent, PublishedContent, ContentRead


class SingleContentViewMixin(object):
    """
    Base mixin to get only one content, and its corresponding versioned content

    Deals with URL resolution in the following way:

    1. In `get_object()`:
        - Fetch the `PublishableContent` according to `self.kwargs['pk']`, `self.request.GET['pk']` or
        `self.request.POST['pk']` (one of these have to be defined). Raise `Http404` if any.
        - Then, check permissions with respect to `self.must_be_author` and `self.authorized_for_staff` (and define
        `self.is_staff` and `self.is_author`). Raise `PermissionDenied` if any.
    2. In `get_versioned_object()`:
        - Deal with sha : assume `self.object.sha_draft` by default, but reset according to
        `self.request.GET['version']`, if exists. Then, check `self.only_draft_version` and raise `PermissionDenied`
        if any
        - Fetch the `VersionedContent`. Due to  the use of `self.object.load_version_or_404(sha)`, raise `Http404`.
        - Check if its the beta or public version, and allow access if it's the case. Raise `PermissionDenied`.
        - Check slug if `self.kwargs['slug']` is defined. Raise `Http404` if any.

    Any redefinition of any of these two functions should take care of those points.
    """

    object = None
    versioned_object = None

    prefetch_all = True
    sha = None
    must_be_author = True
    authorized_for_staff = True
    is_staff = False
    is_author = False
    only_draft_version = True
    must_redirect = False

    def get_object(self, queryset=None):
        """ Get database representation of the content by its `pk`, then check permissions
        """

        # fetch object:
        if 'pk' in self.kwargs:
            pk = self.kwargs['pk']
        elif 'pk' in self.request.GET:
            pk = self.request.GET['pk']
        elif 'pk' in self.request.POST:
            pk = self.request.POST['pk']
        else:
            raise Http404("Cannot find the 'pk' parameter.")

        queryset = PublishableContent.objects

        if self.prefetch_all:
            queryset = queryset.\
                select_related("licence") \
                .prefetch_related("authors") \
                .prefetch_related("subcategory") \

        obj = queryset.filter(pk=pk).first()

        if not obj:
            raise Http404("No contents has this pk.")

        # check permissions:
        self.is_staff = self.request.user.has_perm('tutorialv2.change_tutorialv2')
        self.is_author = self.request.user in obj.authors.all()

        if self.must_be_author and not self.is_author:
            if not self.authorized_for_staff or (self.authorized_for_staff and not self.is_staff):
                raise PermissionDenied

        return obj

    def get_versioned_object(self):
        """Gets the asked version of current content.
        """

        # fetch version:
        sha = self.object.sha_draft

        if not self.only_draft_version:
            if self.sha:
                sha = self.sha
            else:
                if 'version' in self.request.GET:
                    sha = self.request.GET['version']
                elif 'version' in self.request.POST:
                    sha = self.request.POST['version']

        self.sha = sha

        # if beta or public version, user can also access to it
        is_beta = self.object.is_beta(self.sha)
        is_public = self.object.is_public(self.sha)

        if not is_beta and not is_public and not self.is_author:
            if not self.is_staff or (not self.authorized_for_staff and self.must_be_author):
                raise PermissionDenied

        # load versioned file
        versioned = self.object.load_version_or_404(self.sha)

        # check slug, if any:
        if 'slug' in self.kwargs:
            slug = self.kwargs['slug']
            if versioned.slug != slug:
                if slug != self.object.slug:  # retro-compatibility, but should raise permanent redirect instead
                    raise Http404("This slug does not exist for this content.")

        return versioned


class SingleContentPostMixin(SingleContentViewMixin):
    """
    Base mixin used to get content from post query
    """

    # represent the fact that we have to check if the version given in self.request.POST['version'] exists
    versioned = True

    def get_object(self, queryset=None):
        self.object = super(SingleContentPostMixin, self).get_object()

        if self.versioned and 'version' in self.request.POST['version']:
            self.object.load_version_or_404(sha=self.request.POST['version'])
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
            return super(ModalFormView, self).form_invalid(form)
        else:
            errors = form.errors.as_data()
            if len(errors) > 0:
                messages.error(self.request, errors[errors.keys()[0]][0][0])  # only the first error is provided
            else:
                messages.error(
                    self.request, _(u'Une erreur inconnue est survenue durant le traitement des données'))

            if hasattr(form, 'previous_page_url'):
                return redirect(form.previous_page_url)
            else:
                return redirect(reverse('content:view'))  # assume a default url


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

        return super(SingleContentFormViewMixin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SingleContentFormViewMixin, self).get_context_data(**kwargs)
        context['content'] = self.versioned_object
        context['is_staff'] = self.is_staff
        return context


class SingleContentDetailViewMixin(SingleContentViewMixin, DetailView):
    """
    This enhanced DetailView ensure,

    - by rewriting `get()`, that:
        * `self.object` contains the result of `get_object()` (as it must be if `get()` is not rewritten)
        * `self.sha` is set according to `self.request.GET['version']` (if any) and `self.object.sha_draft` otherwise
        * `self.versioned_object` contains the results of `get_versioned_object()`
    - by surcharging `get_context_data()`, that
        * context['content'] contains `self.versioned_object`
        * context['can_edit'] is set
        * context['version'] is set (if different from `self.object.sha_draft`)
    """

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not self.sha:
            try:
                self.sha = request.GET["version"]
            except KeyError:
                self.sha = self.object.sha_draft

        self.versioned_object = self.get_versioned_object()

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super(SingleContentDetailViewMixin, self).get_context_data(**kwargs)

        context['content'] = self.versioned_object
        context['can_edit'] = self.is_author
        context['is_staff'] = self.is_staff
        if self.sha != self.object.sha_draft:
            context["version"] = self.sha

        return context


class ContentTypeMixin(object):
    """This class deals with the type of contents and fill context according to that"""

    current_content_type = None

    def get_context_data(self, **kwargs):
        context = super(ContentTypeMixin, self).get_context_data(**kwargs)

        v_type_name = _(u'contenu')
        v_type_name_plural = _(u'contenus')

        if self.current_content_type == 'ARTICLE':
            v_type_name = _(u'article')
            v_type_name_plural = _(u'articles')

        if self.current_content_type == 'TUTORIAL':
            v_type_name = _(u'tutoriel')
            v_type_name_plural = _(u'tutoriels')

        context['current_content_type'] = self.current_content_type
        context['verbose_type_name'] = v_type_name
        context['verbose_type_name_plural'] = v_type_name_plural

        return context


class MustRedirect(Exception):
    """Exception raised when this is not the last version of the content which is called"""

    def __init__(self, *args, **kwargs):
        super(MustRedirect, self).__init__(*args, **kwargs)


class SingleOnlineContentViewMixin(ContentTypeMixin):

    """
    Base mixin to get only one content online content

    Deals with URL resolution in the following way:

    1. In `get_object()`:
        - Fetch the `PublicContent` according to `self.kwargs['pk']`, `self.request.GET['pk']` or
        `self.request.POST['pk']` `(one of these have to be defined). Raise `Http404` if any.
        - Check if `self.current_content_type` if defined, and use it if it's the case
        - Check if `slug` is defined, also check object it if it's the case
        - Then, define `self.is_staff` and `self.is_author`.
    2. In `get_versioned_object()`: Fetch the `VersionedContent`. Due to  the use of
        `self.public_content_object.load_public_version_or_404()`, raise `Http404` if any.

    Any redefinition of any of these two functions should take care of those points.

    """

    object = None
    public_content_object = None
    versioned_object = None

    is_author = False
    is_staff = False

    def get_redirect_url(self, public_version):
        """Return the most recent url, based on the current public version"""
        return public_version.content.public_version.get_absolute_url_online()

    def get_public_object(self):

        if 'pk' in self.kwargs:
            pk = self.kwargs['pk']
        elif 'pk' in self.request.GET:
            pk = self.request.GET['pk']
        elif 'pk' in self.request.POST:
            pk = self.request.POST['pk']
        else:
            raise Http404("Cannot find the 'pk' parameter.")

        queryset = PublishedContent.objects\
            .filter(content_pk=pk)\
            .prefetch_related('content')\
            .prefetch_related("content__authors")\
            .prefetch_related("content__subcategory")\
            .prefetch_related('content__public_version')

        if self.current_content_type:
            queryset = queryset.filter(content_type=self.current_content_type)

        if 'slug' in self.kwargs:
            queryset = queryset.filter(content_public_slug=self.kwargs['slug'])

        obj = queryset.order_by('publication_date').last()  # "last" version must be the most recent to be published
        if obj is None:
            raise Http404("No contents has this slug.")

        # Redirection ?
        if obj.must_redirect:
            if obj.content.public_version:
                raise MustRedirect(self.get_redirect_url(obj))
            else:  # should only happen if the content is unpublished
                raise Http404("The redirection is activated but the content is not public.")

        self.is_author = self.request.user in obj.content.authors.all()
        self.is_staff = self.request.user.has_perm('tutorialv2.change_tutorialv2')

        return obj

    def get_object(self):

        return self.public_content_object.content

    def get_versioned_object(self):

        return self.public_content_object.load_public_version_or_404()


class SingleOnlineContentDetailViewMixin(SingleOnlineContentViewMixin, DetailView):
    """
    This enhanced DetailView ensure,

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
        * context['isantispam'] is set
    """

    def get(self, request, *args, **kwargs):

        try:
            self.public_content_object = self.get_public_object()
        except MustRedirect as redirection_url:
            return HttpResponsePermanentRedirect(redirection_url)

        self.object = self.get_object()
        self.versioned_object = self.get_versioned_object()
        context = self.get_context_data(object=self.object)
        follow = ContentRead.objects.filter(user__pk=self.request.user.pk)\
            .filter(content__pk=self.object.pk)\
            .first()
        if follow is not None:
            follow.note = self.object.last_note
            follow.save()

        return self.render_to_response(context)

    def get_context_data(self, **kwargs):

        context = super(SingleOnlineContentDetailViewMixin, self).get_context_data(**kwargs)

        context['content'] = self.versioned_object
        context['public_object'] = self.public_content_object
        context['can_edit'] = self.request.user in self.object.authors.all()
        context['isantispam'] = self.object.antispam(self.request.user)
        context['is_staff'] = self.is_staff
        context['is_author'] = self.is_author
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

        return super(SingleOnlineContentFormViewMixin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SingleOnlineContentFormViewMixin, self).get_context_data(**kwargs)

        context['content'] = self.versioned_object
        context['public_object'] = self.public_content_object

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
        response['Content-Disposition'] = 'filename=' + self.get_filename()
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

        return super(SingleContentDownloadViewMixin, self).get(context, **response_kwargs)
