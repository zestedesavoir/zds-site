from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _

from zds.utils.models import Comment


class FilterMixin:
    """
    View mixin which provides filtering for ListView.
    """

    filter_url_kwarg = "type"
    default_filter_param = None

    def filter_queryset(self, queryset, filter_param):
        """
        Filter the queryset `queryset`, given the selected `filter_param`. Default
        implementation does no filtering at all.
        """
        return queryset

    def get_default_filter_param(self):
        if self.default_filter_param is None:
            raise ImproperlyConfigured("'FilterMixin' requires the 'default_filter_param' attribute " "to be set.")
        return self.default_filter_param

    def get_filter_param(self):
        return self.request.GET.get(self.filter_url_kwarg, self.get_default_filter_param())

    def get_queryset(self):
        return self.filter_queryset(super().get_queryset(), self.get_filter_param())

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update(
            {
                self.filter_url_kwarg: self.get_filter_param(),
            }
        )
        return context


class QuoteMixin:
    model_quote = None

    def build_quote(self, post_pk, user):
        assert self.model_quote is not None, "Model for the quote cannot be None."

        try:
            post_pk = int(post_pk)
        except (KeyError, ValueError, TypeError):
            raise Http404
        post_cite = get_object_or_404(self.model_quote, pk=post_pk)

        if isinstance(post_cite, Comment) and not post_cite.is_visible:
            raise PermissionDenied

        if hasattr(post_cite, "topic") and not post_cite.topic.forum.can_read(user):
            raise PermissionDenied

        text = ""
        for line in post_cite.text.splitlines():
            text = text + "> " + line + "\n"

        return _("{0}Source:[{1}]({2}{3})").format(
            text, post_cite.author.username, settings.ZDS_APP["site"]["url"], post_cite.get_absolute_url()
        )
