from django.http import Http404
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, FormView
from zds.tutorialv2.models import PublishableContent


class SingleContentViewMixin(object):
    """
    Base mixin to get only one content, and its corresponding versioned content
    sends 404 error if the primary key is not found or the slug is not coherent,
    sends 403 error if the view is only accessible for author
    """

    must_be_author = True
    authorized_for_staff = True
    prefetch_all = True

    only_draft_version = True
    sha = None

    def get_object(self, queryset=None):
        if self.prefetch_all:
            queryset = PublishableContent.objects \
                .select_related("licence") \
                .prefetch_related("authors") \
                .prefetch_related("subcategory") \
                .filter(pk=self.kwargs["pk"])

            obj = queryset.first()
        else:
            obj = get_object_or_404(PublishableContent, pk=self.kwargs['pk'])
        if 'slug' in self.kwargs and obj.slug != self.kwargs['slug']:
            raise Http404
        if self.must_be_author and self.request.user not in obj.authors.all():
            if self.authorized_for_staff and self.request.user.has_perm('tutorial.change_tutorial'):
                return obj
            raise PermissionDenied
        return obj

    def get_versioned_object(self):
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
        if self.request.user not in self.object.authors.all() and not is_beta:
            if not self.request.user.has_perm("tutorial.change_tutorial"):
                raise PermissionDenied

        # load versioned file
        return self.object.load_version_or_404(sha)


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
        obj = super(SingleContentPostMixin, self).get_object()
        if self.versioned and 'version' in self.request.POST['version']:
            obj.load_version_or_404(sha=self.request.POST['version'])
        return obj


class SingleContentFormViewMixin(SingleContentViewMixin, FormView):
    """
    This enhanced FormView ensure,

    - by surcharging `dispatch()`, that:
        * `self.object` contains the result of `get_object()` (as for DetailView)
        * `self.versioned_object` contains the results of `get_versioned_object()`
    - by surcharging `get_context_data()`, that
        * context['content'] contains `self.versioned_object`
    """

    object = None
    versioned_object = None

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

    object = None
    versioned_object = None

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
