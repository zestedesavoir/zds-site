#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.views.generic import View

from django.contrib import messages
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.core.urlresolvers import reverse
from django.views.generic import DetailView, FormView
from django.utils.translation import ugettext as _

from zds.tutorialv2.models import PublishableContent, PublishedContent, ContentRead


class SingleContentViewMixin(object):
    """
    Base mixin to get only one content, and its corresponding versioned content
    sends 404 error if the primary key is not found or the slug is not coherent,
    sends 403 error if the view is only accessible for author
    """

    object = None
    versioned_object = None

    must_be_author = True
    authorized_for_staff = True
    prefetch_all = True
    only_draft_version = True
    sha = None
    is_public = False
    must_redirect = False
    is_staff = False

    def get_object(self, queryset=None):
        if self.prefetch_all:
            if "pk" in self.request.GET and "pk" not in self.kwargs:
                queryset = PublishableContent.objects \
                    .select_related("licence") \
                    .prefetch_related("authors") \
                    .prefetch_related("subcategory") \
                    .filter(pk=self.request.GET["pk"])
            else:
                queryset = PublishableContent.objects \
                    .select_related("licence") \
                    .prefetch_related("authors") \
                    .prefetch_related("subcategory") \
                    .filter(pk=self.kwargs["pk"])

            obj = queryset.first()
        else:
            obj = get_object_or_404(PublishableContent, pk=self.kwargs['pk'])
        self.is_staff = self.request.user.has_perm('tutorial.change_tutorial')
        if "slug" in self.kwargs and self.kwargs["slug"] != obj.slug and self.is_public:
            # if slug and pk does not match try to find old pk
            queryset = PublishableContent.objects \
                .select_related("licence") \
                .prefetch_related("authors") \
                .prefetch_related("subcategory") \
                .filter(old_pk=self.kwargs["pk"], slug=self.kwargs["slug"])
            obj = queryset.first()
            self.must_redirect = True
        if self.is_public and not self.must_redirect:
            self.sha = obj.sha_public
        if self.must_be_author and self.request.user not in obj.authors.all():
            if self.authorized_for_staff and self.is_staff:
                return obj
            raise PermissionDenied

        return obj

    def get_versioned_object(self):
        """
        Gets the asked version of current content.
        """
        sha = self.object.sha_draft

        if not self.only_draft_version:
            if self.sha:
                sha = self.sha
            else:
                try:
                    sha = self.request.GET["version"]
                except KeyError:
                    pass

        # if beta, user can also access to it
        is_beta = self.object.is_beta(sha)
        if self.object.is_public(sha):
            pass
        elif self.request.user not in self.object.authors.all() and not is_beta:
            if not self.request.user.has_perm("tutorial.change_tutorial") \
                    or (not self.authorized_for_staff and self.must_be_author):
                raise PermissionDenied

        # load versioned file
        versioned = self.object.load_version_or_404(sha)

        if 'slug' in self.kwargs \
                and (versioned.slug != self.kwargs['slug'] and self.object.slug != self.kwargs['slug']):

            raise Http404

        return versioned


class SingleContentPostMixin(SingleContentViewMixin):
    """
    Base mixin used to get content from post query
    """

    # represent the fact that we have to check if the version given in self.request.POST['version'] exists
    versioned = True

    def get_object(self, queryset=None):
        try:
            self.kwargs["pk"] = self.request.POST['pk']
        except KeyError:
            raise Http404
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
        context['can_edit'] = self.request.user in self.object.authors.all()
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

        context['is_staff'] = self.request.user.has_perm('tutorial.change_tutorial')
        context['current_content_type'] = self.current_content_type
        context['verbose_type_name'] = v_type_name
        context['verbose_type_name_plural'] = v_type_name_plural

        return context


class SingleOnlineContentViewMixin(ContentTypeMixin):

    """
    Base mixin to get only one content online content
    sends 404 error if the primary key is not found or the slug is not coherent,
    """

    object = None
    public_content_object = None
    versioned_object = None

    def get_public_object(self):
        pk = self.kwargs.pop('pk', None)
        slug = self.kwargs.pop('slug', '')

        try:
            obj = PublishedContent.objects\
                .filter(content_pk=pk, content_public_slug=slug, content_type=self.current_content_type)\
                .prefetch_related('content')\
                .prefetch_related("content__authors")\
                .prefetch_related("content__subcategory")\
                .first()
        except ObjectDoesNotExist:
            raise Http404

        if obj is None:
            raise Http404

        return obj

    def get_object(self):

        return self.public_content_object.content

    def get_versioned_object(self):

        return self.object.load_version_or_404(
            sha=self.public_content_object.sha_public, public=self.public_content_object)


class SingleOnlineContentDetailViewMixin(SingleOnlineContentViewMixin, DetailView):
    """
    This enhanced DetailView ensure,

    - by rewriting `get()`, that:
        * `self.object` contains the result of `get_object()` (as it must be if `get()` was not rewritten)
        * `self.versioned_object` contains a PublicContent object
        * `self.public_content_object` contains a PublishedContent object
    - by surcharging `get_context_data()`, that
        * context['content'] is set
        * context['can_edit'] is set
        * context['public_object'] is set
        * context['isantispam'] is set
    """

    def get(self, request, *args, **kwargs):
        self.public_content_object = self.get_public_object()
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
        context['is_staff'] = self.request.user.has_perm('tutorial.change_tutorial')
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
