from django.views.generic import View

from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, FormView
from django.utils.translation import ugettext as _

from zds.tutorialv2.models import PublishableContent, PublishedContent


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
            if self.authorized_for_staff and self.request.user.has_perm('tutorial.change_tutorial'):
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


class SingleContentFormViewMixin(SingleContentViewMixin, FormView):
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

        if self.sha != self.object.sha_draft:
            context["version"] = self.sha

        return context


class ContentTypeMixin(object):
    """This class deals with the type of contents and fill context according to that"""

    content_type = None

    def get_context_data(self, **kwargs):
        context = super(ContentTypeMixin, self).get_context_data(**kwargs)

        v_type_name = _(u'contenu')
        v_type_name_plural = _(u'contenus')

        if self.content_type == 'ARTICLE':
            v_type_name = _(u'article')
            v_type_name_plural = _(u'articles')

        if self.content_type == 'TUTORIAL':
            v_type_name = _(u'tutoriel')
            v_type_name_plural = _(u'tutoriels')

        context['content_type'] = self.content_type
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
                .filter(content_pk=pk, content_public_slug=slug, content_type=self.content_type)\
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
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super(SingleOnlineContentDetailViewMixin, self).get_context_data(**kwargs)

        context['content'] = self.versioned_object
        context['public_object'] = self.public_content_object
        context['can_edit'] = self.request.user in self.object.authors.all()
        context['isantispam'] = self.object.antispam(self.request.user)
        return context


class SingleOnlineContentFormViewMixin(SingleOnlineContentViewMixin, FormView):
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
